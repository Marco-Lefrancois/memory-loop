import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

# Activer l'import depuis la racine du projet (bridges lancés en script direct)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.bridges.mcp_resources import handle_resources_list, handle_resources_read
from src.bridges.mcp_tools import handle_tools_list, handle_tools_call
from src.bridges.mcp_event_bus import get_event_bus
from src.bridges._mcp_prompts import handle_prompts_get, handle_prompts_list
from src.bridges.mcp_recall import (  # noqa: F401 — API publique historique
    _PRELOAD_CACHE,
    auto_recall_passive_memory,
    clear_preloaded_context,
    log_error,
    preload_story_context,
)
from src.bridges._mcp_protocol import (
    PROTOCOL_VERSION_LEGACY,
    VersionDecision,
    apply_fallback_policy,
    attach_routing_meta,
    declared_version,
    enrich_initialize_result,
    invalid_version_error,
    negotiate_version,
)

logger = logging.getLogger(__name__)

_SESSION_ID: str = str(uuid.uuid4())[:8]
_SESSION_PROJECT: str | None = None
# Révision protocolaire mémorisée par la session (état de transport uniquement).
_SESSION_PROTOCOL_VERSION: str | None = None

# Socle de mémoire déporté dans mcp_recall (plafond modulaire ADR-0202) :
# `_PRELOAD_CACHE`, `auto_recall_passive_memory`, `preload_story_context` et
# `clear_preloaded_context` restent importables depuis ce module.

__all__ = [
    "_PRELOAD_CACHE",
    "auto_recall_passive_memory",
    "clear_preloaded_context",
    "handle_initialize",
    "handle_tools_list",
    "log_error",
    "preload_story_context",
    "process_message",
]


def handle_initialize(
    req_id: Any,
    params: dict | None = None,
    *,
    transport: str = "stdio",
    headers: dict | None = None,
    version_decision: VersionDecision | None = None,
) -> dict:
    """
    Négociation de version à l'initialisation (récit §1, 210-Q1).

    La version souhaitée est confrontée au registre unique partagé avec le
    routage. Une valeur inconnue est refusée par l'erreur JSON-RPC -32600 sans
    aucune mutation de session ; une valeur connue est toujours recevable, la
    révision obsolète armant la politique de repli (appliquée par la couche
    transport avant appel).
    """
    global _SESSION_PROTOCOL_VERSION

    decision = version_decision
    if decision is None:
        declared, _source = declared_version(params, headers)
        decision = negotiate_version(declared)

    if not decision.accepted:
        return invalid_version_error(req_id, decision.requested)

    # État de transport uniquement : aucune persistance applicative.
    _SESSION_PROTOCOL_VERSION = decision.negotiated

    _meta = (params or {}).get("_meta", {})
    traceparent = _meta.get("traceparent", "")
    if traceparent:
        log_error(f"OpenTelemetry Trace Context: {traceparent}")

    base_result = {
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
        },
        "serverInfo": {
            "name": "memory-loop-session-memory-mcp",
            "version": "2.0.0",
            "sessionId": _SESSION_ID,
        },
    }
    result = enrich_initialize_result(base_result, decision)
    if transport != "stdio":
        logger.debug(
            "mcp_initialize_negotiated",
            extra={
                "event": "mcp_initialize_negotiated",
                "transport": transport,
                "status": decision.status,
                "negotiated": decision.negotiated,
            },
        )
    return {"jsonrpc": "2.0", "result": result, "id": req_id}


def handle_server_discover(req_id: Any, params: dict | None = None) -> dict:
    """Publie le registre unique des versions prises en charge (anti-dérive)."""
    decision = negotiate_version(_SESSION_PROTOCOL_VERSION)
    base_result = {
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
        },
        "serverInfo": {"name": "memory-loop-session-memory-mcp", "version": "2.0.0"},
    }
    return {
        "jsonrpc": "2.0",
        "result": enrich_initialize_result(base_result, decision),
        "id": req_id,
    }


def process_message(
    line: str,
    *,
    transport: str = "stdio",
    headers: dict | None = None,
    version_decision: VersionDecision | None = None,
    apply_fallback: bool = True,
) -> str | None:
    """
    Traite une requête JSON-RPC et y attache `_meta.routing` (récit §Transport
    stdio) : `{protocolVersion, method, toolName?}` — zéro en-tête HTTP fabriqué.

    - `version_decision` : décision déjà résolue par la couche transport (le
      routage par en-têtes HTTP/SSE se fait sans lire le corps) ;
    - `apply_fallback=False` : la politique de repli a déjà été appliquée par
      la couche transport — strictement une application par requête.
    """
    global _SESSION_PROJECT
    try:
        req = json.loads(line)
    except json.JSONDecodeError as exc:
        logger.debug(f"JSON decode error: {exc}", exc_info=True)
        return None

    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    # ── Résolution de version (message > session) & refus réservé au registre ──
    decision = version_decision
    declared_in_message = False
    if decision is None:
        declared, source = declared_version(params, headers)
        declared_in_message = source != "absent"
        effective = declared or _SESSION_PROTOCOL_VERSION
        decision = negotiate_version(effective)
    if not decision.accepted:
        return json.dumps(invalid_version_error(req_id, decision.requested))

    tool_name = params.get("name") if method == "tools/call" else None

    if apply_fallback:
        # Politique de repli par requête, dans le même traitement (macro Q1).
        apply_fallback_policy(
            decision,
            transport=transport,
            method=method,
            tool_name=tool_name,
            header_present=None,
            declared_in_message=declared_in_message,
        )

    _meta = params.get("_meta", {})
    if isinstance(_meta, dict) and _meta.get("stateHandle"):
        _SESSION_PROJECT = str(_meta["stateHandle"]).replace("proj_", "").split("_")[0]

    bus = get_event_bus()

    if method == "initialize":
        res = handle_initialize(
            req_id,
            params,
            transport=transport,
            headers=headers,
            version_decision=decision,
        )
    elif method == "server/discover":
        res = handle_server_discover(req_id, params)
    elif method == "tools/list":
        res = handle_tools_list(req_id, params)
    elif method == "tools/call":
        res, _SESSION_PROJECT = handle_tools_call(req_id, params, _SESSION_PROJECT)
        _maybe_emit_tool_notifications(bus, params, _SESSION_PROJECT)
    elif method == "resources/list":
        res = handle_resources_list(req_id, _SESSION_PROJECT)
    elif method == "resources/read":
        res = handle_resources_read(req_id, params, _SESSION_PROJECT)
    elif method == "prompts/list":
        res = handle_prompts_list(req_id)
    elif method == "prompts/get":
        res = handle_prompts_get(req_id, params, session_project=_SESSION_PROJECT)
    else:
        if req_id is not None:
            res = {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Méthode '{method}' non supportée."},
                "id": req_id,
            }
        else:
            return None

    attach_routing_meta(
        res,
        protocol_version=decision.negotiated or PROTOCOL_VERSION_LEGACY,
        method=method,
        tool_name=tool_name,
    )
    return json.dumps(res)


def _maybe_emit_tool_notifications(bus: Any, params: dict, session_project: str | None) -> None:
    """Émet les notifications SSE pertinentes après un tools/call."""
    tool_name = params.get("name", "")

    if tool_name == "set_phase":
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(bus.notify_tools_list_changed(session_id=session_project))
        except RuntimeError as e:
            logger.debug(
                "Boucle asyncio non disponible, notification SSE set_phase omise",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_loop_mem",
                    "operation": "notify_set_phase",
                    "error": str(e),
                },
            )

    if tool_name in ("loop_mem_search", "loop_mem_code_rag", "loop_mem_timeline"):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                bus.notify_resource_updated(
                    uri=f"mloop://project/{session_project or 'mLoop'}/observation/latest",
                    session_id=session_project,
                )
            )
        except RuntimeError as e:
            logger.debug(
                "Boucle asyncio non disponible, notification SSE observation omise",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_loop_mem",
                    "operation": "notify_observation_updated",
                    "tool": tool_name,
                    "error": str(e),
                },
            )


def main() -> None:
    log_error("Démarrage serveur MCP stdio Memory Loop...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            response = process_message(line)
            if response:
                sys.stdout.write(response + "\n")
                sys.stdout.flush()
        except Exception as exc:
            logger.debug(f"Erreur boucle stdio MCP: {exc}", exc_info=True)
            log_error(f"Erreur boucle MCP: {exc}")


if __name__ == "__main__":
    main()
