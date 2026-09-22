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

logger = logging.getLogger(__name__)

_SESSION_ID: str = str(uuid.uuid4())[:8]
_SESSION_PROJECT: str | None = None
_PRELOAD_CACHE: dict = {}


def log_error(msg: str) -> None:
    sys.stderr.write(f"[MCP LOOP-MEM] {msg}\n")
    sys.stderr.flush()


def auto_recall_passive_memory(
    story_id: str = None, query: str = None, project: str = None
) -> list:
    """
    Axe 1 jcode (ADR-0308) : Auto-Recall Sémantique Passif.
    """
    from src.loop_mem.db import search_observations, get_active_project

    proj = project or _SESSION_PROJECT or get_active_project() or "mLoop"
    recalled_items = []

    if story_id and story_id in _PRELOAD_CACHE:
        cached_data = _PRELOAD_CACHE[story_id]
        nodes = cached_data.get("nodes", [])[:3]
        for n in nodes:
            name = n.get("name") if isinstance(n, dict) else str(n)
            recalled_items.append(
                {
                    "source": "RAM_Cache",
                    "type": "engramme_graphe",
                    "summary": f"Nœud sémantique: {name}",
                }
            )

    search_term = query or story_id or "architecture"
    try:
        obs_matches = search_observations(query=search_term, project_name=proj) or []
        for obs in obs_matches[:3]:
            recalled_items.append(
                {
                    "source": "Memory_SQLite",
                    "type": obs.get("type", "observation"),
                    "id": obs.get("id"),
                    "summary": obs.get("content", "")[:120] + "...",
                }
            )
    except Exception as exc:
        logger.debug(f"Erreur Auto-Recall sémantique passif: {exc}", exc_info=True)
        log_error(f"Erreur lors de l'Auto-Recall sémantique passif: {exc}")

    return recalled_items[:5]


def preload_story_context(story_id: str, project: str = None) -> dict:
    global _PRELOAD_CACHE
    from src.loop_mem.db import get_active_project

    proj = project or _SESSION_PROJECT or get_active_project() or "mLoop"
    graph_path = Path("Projects") / proj / "memory" / "knowledge_graph.json"

    nodes_cached = 0
    if graph_path.exists():
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

            relevant_nodes = [n for n in nodes if story_id.lower() in str(n).lower()]
            if not relevant_nodes:
                relevant_nodes = nodes[:10]

            _PRELOAD_CACHE[story_id] = {
                "story_id": story_id,
                "project": proj,
                "nodes": relevant_nodes,
                "edges": edges,
                "timestamp": str(uuid.uuid4()),
            }
            nodes_cached = len(relevant_nodes)
        except Exception as exc:
            logger.debug(f"Erreur lors du préchargement de {story_id}: {exc}", exc_info=True)
            log_error(f"Erreur lors du préchargement de {story_id}: {exc}")

    passive_engrams = auto_recall_passive_memory(story_id=story_id, project=proj)

    return {
        "status": "preloaded",
        "story_id": story_id,
        "nodes_cached": nodes_cached,
        "auto_recall_engrams": len(passive_engrams),
        "memory_used_kb": len(json.dumps(_PRELOAD_CACHE.get(story_id, {}))) // 1024,
    }


def clear_preloaded_context(story_id: str = None) -> dict:
    global _PRELOAD_CACHE
    if story_id:
        _PRELOAD_CACHE.pop(story_id, None)
    else:
        _PRELOAD_CACHE.clear()
    return {"status": "cleared", "remaining_keys": list(_PRELOAD_CACHE.keys())}


def handle_initialize(req_id: Any, params: dict = None) -> dict:
    _meta = (params or {}).get("_meta", {})
    traceparent = _meta.get("traceparent", "")
    if traceparent:
        log_error(f"OpenTelemetry Trace Context: {traceparent}")
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
            },
            "serverInfo": {
                "name": "memory-loop-session-memory-mcp",
                "version": "2.0.0",
                "sessionId": _SESSION_ID,
            },
        },
        "id": req_id,
    }


def handle_server_discover(req_id: Any, params: dict = None) -> dict:
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "supportedVersions": ["2026-07-28", "2025-11-25", "2024-11-05"],
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
            },
            "serverInfo": {"name": "memory-loop-session-memory-mcp", "version": "2.0.0"},
        },
        "id": req_id,
    }


def process_message(line: str) -> str | None:
    global _SESSION_PROJECT
    try:
        req = json.loads(line)
    except json.JSONDecodeError as exc:
        logger.debug(f"JSON decode error: {exc}", exc_info=True)
        return None

    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    _meta = params.get("_meta", {})
    if isinstance(_meta, dict) and _meta.get("stateHandle"):
        _SESSION_PROJECT = str(_meta["stateHandle"]).replace("proj_", "").split("_")[0]

    bus = get_event_bus()

    if method == "initialize":
        res = handle_initialize(req_id, params)
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
