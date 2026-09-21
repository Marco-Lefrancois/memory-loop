"""
mcp_sse_server.py — Serveur MCP Transport Réseau SSE (MLOOP-103-BE).

Point d'entrée HTTP pour la communication MCP inter-processus via
Server-Sent Events (SSE) et JSON-RPC POST. Conserve la compatibilité
backward avec le transport stdio existant.

Fonctionnalités :
- Endpoint GET /sse : flux SSE temps réel (notifications/resources/updated,
  notifications/tools/list_changed, keepalive)
- Endpoint POST /messages : réception de requêtes JSON-RPC 2.0
- Pool de connexions asynchrones avec nettoyage automatique
- Handshake initial avec metadata de session
- Intégration du MCPEventBus pour diffusion centralisée

Conforme aux contraintes ADR-0202 (≤300 lignes) et ADR-0369 (context managers,
timeout explicite, logs structurés).

Usage :
    python -m src.bridges.mcp_sse_server --port 8380
    ou depuis swarm.py : python src/swarm.py serve --port 8380
"""

import argparse
import asyncio
import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, StreamingResponse
except ImportError:
    logger.error("FastAPI requis. Installez avec: pip install fastapi uvicorn")
    sys.exit(1)

from src.bridges.mcp_event_bus import MCPEventBus, get_event_bus
from src.bridges.mcp_loop_mem import process_message

SSE_KEEPALIVE_INTERVAL = 15.0
SSE_CONNECT_TIMEOUT = 30.0
JSONRPC_PARSE_ERROR = -32700
JSONRPC_METHOD_NOT_FOUND = -32601


def _create_app(bus: MCPEventBus) -> FastAPI:
    """Crée l'application FastAPI avec les endpoints MCP SSE."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(
            "MCP SSE server starting",
            extra={"max_clients": bus._max_clients},
        )
        yield
        logger.info("MCP SSE server shutting down")

    app = FastAPI(
        title="mLoop MCP SSE Transport",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/sse")
    async def sse_endpoint(request: Request):
        """
        Endpoint SSE unidirectionnel. Diffuse les notifications MCP
        en temps réel aux clients abonnés.
        """
        client_id = str(uuid.uuid4())[:12]
        queue = await bus.subscribe(client_id)

        async def event_stream():
            try:
                welcome = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"subscribe": True, "listChanged": True},
                        },
                        "serverInfo": {
                            "name": "mloop-sse-transport",
                            "version": "1.0.0",
                            "sessionId": client_id,
                        },
                    },
                }
                yield bus._format_sse_frame("initialized", welcome)

                heartbeat_counter = 0
                while True:
                    try:
                        frame = await asyncio.wait_for(queue.get(), timeout=SSE_KEEPALIVE_INTERVAL)
                        if frame is None:
                            break
                        yield frame
                        heartbeat_counter = 0
                    except asyncio.TimeoutError:
                        heartbeat_counter += 1
                        hb = await bus.generate_heartbeat(client_id)
                        if hb is None:
                            break
                        yield hb
                    except asyncio.CancelledError:
                        break
            finally:
                await bus.unsubscribe(client_id)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            },
        )

    @app.post("/messages")
    async def messages_endpoint(request: Request):
        """
        Endpoint JSON-RPC 2.0 POST. Reçoit les requêtes tools/call,
        tools/list, resources/list, etc. et retourne la réponse.
        """
        try:
            body = await asyncio.wait_for(request.body(), timeout=SSE_CONNECT_TIMEOUT)
            raw = body.decode("utf-8")
        except asyncio.TimeoutError:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": JSONRPC_PARSE_ERROR, "message": "Timeout lecture requête"},
                    "id": None,
                },
                status_code=408,
            )

        try:
            req = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.debug("JSON parse error: %s", exc, exc_info=True)
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": JSONRPC_PARSE_ERROR, "message": f"Parse error: {exc}"},
                    "id": None,
                },
                status_code=400,
            )

        method = req.get("method", "")
        req_id = req.get("id")

        if method in ("notifications/initialized", "ping"):
            return JSONResponse({"ok": True})

        response_raw = process_message(json.dumps(req))
        if response_raw is None:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": JSONRPC_METHOD_NOT_FOUND,
                        "message": f"Méthode '{method}' non supportée.",
                    },
                    "id": req_id,
                },
                status_code=404,
            )

        try:
            response = json.loads(response_raw)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "result": {}, "id": req_id}

        return JSONResponse(response)

    @app.get("/health")
    async def health_endpoint():
        """Point de contrôle de santé pour monitoring."""
        stats = bus.get_session_stats()
        return {"status": "ok", **stats}

    return app


def run_server(host: str = "127.0.0.1", port: int = 8380) -> None:
    """Démarre le serveur MCP SSE avec uvicorn."""
    bus = get_event_bus()
    app = _create_app(bus)

    try:
        import uvicorn

        logger.info(
            "Starting MCP SSE server",
            extra={"host": host, "port": port},
        )
        uvicorn.run(app, host=host, port=port, log_level="warning")
    except ImportError:
        logger.error("uvicorn requis. Installez avec: pip install uvicorn")
        sys.exit(1)


def main() -> None:
    """Point d'entrée CLI pour le serveur SSE."""
    parser = argparse.ArgumentParser(description="mLoop MCP SSE Transport Server")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse de bind (défaut: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8380, help="Port HTTP (défaut: 8380)")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
