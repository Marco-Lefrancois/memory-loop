"""
mcp_proxy_router.py — MCP Proxy Aggregator (Scoped Variant) for mLoop.

Pattern: Proxy Aggregator + Scoped Tool Exposure (arXiv:2606.30317v1)
- Aggregates all mLoop MCP sub-servers into a single entry point.
- Dynamically filters the list of exposed tools based on the active Story phase.
- Prevents the LLM from seeing irrelevant tools (budget: max 15 tools per context).

Sub-servers managed:
  - mloop_mem   → src/bridges/mcp_loop_mem.py       (Session Memory & Graph RAG)
  - open_notebook → src/bridges/mcp_open_notebook.py (Reference Knowledge Gateway)
  - crawler       → src/bridges/mcp_crawler.py       (Web Crawling)

Usage (stdio MCP proxy): call this script directly as an MCP server.
"""

import sys
import json
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Registre déclaratif extrait (ADR-0202, plafond modulaire) — ré-exporté ici
# pour préserver l'API publique historique du pont.
from src.bridges.mcp_proxy_registry import PHASE_TOOL_FILTER, TOOL_REGISTRY
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

SERVER_NAME = "mloop-proxy-router"
SERVER_VERSION = "1.0.0"

# Révision protocolaire mémorisée par la session (état de transport stdio).
_SESSION_PROTOCOL_VERSION: str | None = None


def log_error(msg: str):
    sys.stderr.write(f"[MCP PROXY] {msg}\n")
    sys.stderr.flush()


def validate_tool_registry() -> bool:
    """
    Valide la conformité stricte JSON Schema des outils du registre (ADR-0352 / HarnessDev).
    Garantit une neutralité totale vis-à-vis des fournisseurs (OpenAI, Gemini, Anthropic).
    """
    for name, meta in TOOL_REGISTRY.items():
        if not meta.get("description"):
            log_error(f"Outil {name} sans description valide.")
            return False
        schema = meta.get("inputSchema", {})
        if schema.get("type") != "object":
            log_error(f"Outil {name} : inputSchema doit être de type 'object'.")
            return False
        if "properties" not in schema:
            log_error(f"Outil {name} : inputSchema sans champ 'properties'.")
            return False
    return True


def _get_visible_tools(phase: str) -> list[dict]:
    """Return filtered tool list based on active phase."""
    allowed = PHASE_TOOL_FILTER.get(phase)
    visible = {}
    for name, meta in TOOL_REGISTRY.items():
        if allowed is None or name in allowed:
            visible[name] = meta
    return [
        {"name": name, "description": meta["description"], "inputSchema": meta["inputSchema"]}
        for name, meta in visible.items()
    ]


def _call_sub_server(server_script: str, method: str, params: dict) -> dict:
    """Invoke a sub-server MCP script directly (in-process import for speed)."""
    # We import the sub-module functions directly to avoid subprocess overhead
    try:
        if server_script == "mloop_mem":
            from src.bridges.mcp_loop_mem import handle_tools_call

            return handle_tools_call(req_id=1, params=params)
        elif server_script == "open_notebook":
            from src.bridges.mcp_open_notebook import handle_tools_call

            return handle_tools_call(req_id=1, params=params)
        elif server_script == "graphify":
            from src.bridges.mcp_graphify import handle_tools_call

            return handle_tools_call(req_id=1, params=params)
        else:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "isError": True,
                    "content": [
                        {"type": "text", "text": f"Sub-serveur '{server_script}' non trouvé."}
                    ],
                },
                "id": 1,
            }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"Erreur sous-serveur: {e}"}],
            },
            "id": 1,
        }


def handle_initialize(req_id, params=None, *, version_decision=None):
    """
    Négociation de version à l'initialisation (récit §1, 210-Q1).

    Le registre unique est partagé avec le routage par en-têtes : seule une
    version absente du registre est refusée (-32600), sans mutation de session.
    """
    global _SESSION_PROTOCOL_VERSION

    decision = version_decision
    if decision is None:
        declared, _source = declared_version(params, None)
        decision = negotiate_version(declared)

    if not decision.accepted:
        return invalid_version_error(req_id, decision.requested)

    _SESSION_PROTOCOL_VERSION = decision.negotiated
    base_result = {
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }
    return {
        "jsonrpc": "2.0",
        "result": enrich_initialize_result(base_result, decision),
        "id": req_id,
    }


def handle_tools_list(req_id):
    global _active_phase
    tools = _get_visible_tools(_active_phase)
    log_error(f"Phase '{_active_phase}' — {len(tools)} outils exposés.")
    return {"jsonrpc": "2.0", "result": {"tools": tools}, "id": req_id}


def handle_tools_call(req_id, params):
    global _active_phase
    name = params.get("name")
    arguments = params.get("arguments", {})

    # Router meta-tool: switch phase
    if name == "set_phase":
        new_phase = arguments.get("phase", "ALL")
        _active_phase = new_phase
        tools = _get_visible_tools(new_phase)
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ Phase active : **{new_phase}** — {len(tools)} outils disponibles.",
                    }
                ]
            },
            "id": req_id,
        }

    # Route to the right sub-server
    tool_meta = TOOL_REGISTRY.get(name)
    if not tool_meta:
        return {
            "jsonrpc": "2.0",
            "result": {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Outil '{name}' inconnu ou non disponible dans la phase '{_active_phase}'.",
                    }
                ],
            },
            "id": req_id,
        }

    server = tool_meta["server"]
    # Relay the call to the sub-server, preserving req_id
    result = _call_sub_server(server, "tools/call", {"name": name, "arguments": arguments})
    result["id"] = req_id
    return result


def main():
    global _active_phase
    log_error(f"Démarrage du Proxy Aggregator mLoop (phase initiale: {_active_phase})...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")
            params = req.get("params", {}) or {}

            # Négociation par requête : message déclaré > état de session.
            declared, source = declared_version(params, None)
            decision = negotiate_version(declared or _SESSION_PROTOCOL_VERSION)
            tool_name = params.get("name") if method == "tools/call" else None

            if not decision.accepted:
                res = invalid_version_error(req_id, decision.requested)
            elif method == "initialize":
                res = handle_initialize(req_id, params, version_decision=decision)
            elif method == "tools/list":
                res = handle_tools_list(req_id)
            elif method == "tools/call":
                res = handle_tools_call(req_id, params)
            elif method in ("notifications/initialized", "ping"):
                res = None
            elif req_id is not None:
                res = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Méthode '{method}' non supportée."},
                    "id": req_id,
                }
            else:
                res = None

            # Politique de repli : strictement une application par requête.
            apply_fallback_policy(
                decision,
                transport="stdio",
                method=method,
                tool_name=tool_name,
                header_present=None,
                declared_in_message=source != "absent",
            )

            if res is None:
                continue

            attach_routing_meta(
                res,
                protocol_version=decision.negotiated or PROTOCOL_VERSION_LEGACY,
                method=method,
                tool_name=tool_name,
            )
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        except Exception as e:
            log_error(f"Erreur critique proxy: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
