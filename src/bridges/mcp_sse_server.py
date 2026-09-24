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
from src.bridges._mcp_protocol import (
    PROTOCOL_VERSION_LEGACY,
    PROTOCOL_VERSION_TARGET,
    SUPPORTED_PROTOCOL_VERSIONS,
    apply_fallback_policy,
    declared_version,
    get_adoption_metrics,
    invalid_version_error,
    response_headers,
    route_from_headers,
)

SSE_KEEPALIVE_INTERVAL = 15.0
SSE_CONNECT_TIMEOUT = 30.0
JSONRPC_PARSE_ERROR = -32700
JSONRPC_METHOD_NOT_FOUND = -32601
TRANSPORT_ID = "http_sse"


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
                        # Registre unique partagé avec la négociation (210-Q1).
                        "protocolVersion": PROTOCOL_VERSION_TARGET,
                        "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
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

        Routage par en-têtes (récit §2 / 210-Q2) : la décision de route est
        prise sur les **seuls en-têtes**, sans lecture du corps JSON-RPC ; le
        corps n'est lu qu'ensuite comme enveloppe (`id` / `params`) de la
        requête déjà acheminée. L'absence d'en-tête de version n'est jamais un
        rejet : elle bascule gracieusement en client hérité. Seule une version
        absente du registre provoque le refus dur -32600.
        """
        # ── 1. Route résolue depuis les en-têtes uniquement (zéro corps) ──
        route = route_from_headers(request.headers)
        if not route.accepted:
            return JSONResponse(
                invalid_version_error(None, route.decision.requested),
                status_code=400,
            )
        negotiated = route.decision.negotiated or PROTOCOL_VERSION_LEGACY

        # ── 2. Lecture du corps : enveloppe JSON-RPC de la requête routée ──
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
                headers=response_headers(negotiated),
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
                headers=response_headers(negotiated),
            )

        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params") if isinstance(req.get("params"), dict) else {}

        # ── 3. Désaccords en-tête / corps : non-conformités journalisées ──
        #      (refuser n'est permis qu'à une version inconnue du registre)
        nonconformities = list(route.nonconformities)
        body_version, _source = declared_version(params, None)
        if route.header_present and body_version and body_version != route.decision.requested:
            nonconformities.append("protocol_version_header_body_mismatch")
        if route.header_present and route.method and route.method != method:
            nonconformities.append("method_header_body_mismatch")

        echo_method = method or None
        tool_name = route.tool_name or (params.get("name") if method == "tools/call" else None)
        resp_headers = response_headers(negotiated, echo_method, tool_name)

        # ── 4. Politique de repli : strictement une application par requête ──
        apply_fallback_policy(
            route.decision,
            transport=TRANSPORT_ID,
            method=echo_method,
            tool_name=tool_name,
            header_present=route.header_present,
            declared_in_message=route.header_present,
            nonconformities=nonconformities,
        )

        if method in ("notifications/initialized", "ping"):
            return JSONResponse({"ok": True}, headers=resp_headers)

        # ── 5. Acheminement : la route en-tête est passée au processeur ──
        response_raw = process_message(
            json.dumps(req),
            transport=TRANSPORT_ID,
            headers=dict(request.headers),
            version_decision=route.decision,
            apply_fallback=False,
        )
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
                headers=resp_headers,
            )

        try:
            response = json.loads(response_raw)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "result": {}, "id": req_id}

        return JSONResponse(response, headers=resp_headers)

    @app.get("/health")
    async def health_endpoint():
        """Point de contrôle de santé pour monitoring + adoption protocolaire."""
        stats = bus.get_session_stats()
        return {"status": "ok", "protocol_adoption": get_adoption_metrics(), **stats}

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
