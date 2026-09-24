"""
mLoop MCP Resilience Guard (ADR-0374 & OWASP MCP Top 10) — Pont MCP.

Point d'entrée stdio du garde-fou : poignée de main (négociation de version
MLOOP-210-BE), catalogue d'outils de sécurité et boucle JSON-RPC. Le cœur
d'intégrité (MCP-01 à MCP-04) est exposé par ``_resilience_guard``.

Conforme aux contraintes ADR-0202 (<300 lignes, <15 Ko).
"""

import json
import sys
from typing import Any, Dict

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
from src.bridges._resilience_guard import (  # noqa: F401 — API publique historique
    MCPGuardError,
    MCPResilienceGuard,
    MCPValidationError,
    MCPScopeViolationError,
)

# Révision protocolaire mémorisée par la session (état de transport stdio).
_SESSION_PROTOCOL_VERSION: str | None = None


def handle_initialize(
    req_id: Any,
    params: Dict[str, Any] | None = None,
    *,
    version_decision: VersionDecision | None = None,
) -> Dict[str, Any]:
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
        "capabilities": {"tools": {"listChanged": True}},
        "serverInfo": {"name": "mloop-resilience-guard-mcp", "version": "1.0.0"},
    }
    return {
        "jsonrpc": "2.0",
        "result": enrich_initialize_result(base_result, decision),
        "id": req_id,
    }


def handle_tools_list(req_id: Any) -> Dict[str, Any]:
    tools = [
        {
            "name": "resilience_status",
            "description": "Vérifie l'état du garde-fou de résilience MCP.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "resilience_validate_arguments",
            "description": "Valide les arguments d'un outil MCP contre son schéma strict (MCP-01).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string"},
                    "arguments": {"type": "object"},
                    "schema": {"type": "object"},
                },
                "required": ["tool_name", "arguments"],
            },
        },
        {
            "name": "resilience_check_permission",
            "description": "Vérifie les permissions RBAC d'un outil selon le rôle agent (MCP-03).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string"},
                    "role": {"type": "string"},
                    "is_destructive": {"type": "boolean"},
                },
                "required": ["tool_name", "role"],
            },
        },
        {
            "name": "resilience_encapsulate_result",
            "description": "Confinage étanche d'un résultat d'outil avec troncature et SHA-256 (MCP-02/04).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string"},
                    "content": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["tool_name", "content"],
            },
        },
        {
            "name": "resilience_workflow_digest",
            "description": "Calcule l'empreinte SHA-256 d'un workflow multi-étapes (ADR-0374).",
            "inputSchema": {
                "type": "object",
                "properties": {"steps": {"type": "array", "items": {"type": "object"}}},
                "required": ["steps"],
            },
        },
    ]
    return {"jsonrpc": "2.0", "result": {"tools": tools}, "id": req_id}


def handle_tools_call(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name, args, guard = params.get("name"), params.get("arguments", {}), MCPResilienceGuard()
    try:
        if name == "resilience_status":
            res = {
                "status": "ACTIVE",
                "destructive_actions": sorted(list(guard.DESTRUCTIVE_ACTIONS)),
                "read_only_roles": sorted(list(guard.READ_ONLY_ROLES)),
                "max_payload_chars": guard.max_payload_chars,
            }
            text = json.dumps(res, indent=2, ensure_ascii=False)
        elif name == "resilience_validate_arguments":
            v = guard.validate_tool_arguments(
                args.get("tool_name", ""), args.get("arguments", {}), args.get("schema")
            )
            text = json.dumps({"valid": True, "arguments": v}, indent=2, ensure_ascii=False)
        elif name == "resilience_check_permission":
            v = guard.check_execution_permission(
                args.get("tool_name", ""), args.get("role", ""), args.get("is_destructive")
            )
            text = json.dumps({"allowed": v}, indent=2, ensure_ascii=False)
        elif name == "resilience_encapsulate_result":
            text = guard.encapsulate_tool_result(
                args.get("content", ""), args.get("tool_name", ""), args.get("max_chars")
            )
        elif name == "resilience_workflow_digest":
            text = json.dumps(
                {"digest": guard.compute_workflow_digest(args.get("steps", []))},
                indent=2,
                ensure_ascii=False,
            )
        else:
            text = f"Outil inconnu : {name}"
    except (MCPValidationError, MCPScopeViolationError, MCPGuardError) as e:
        text = json.dumps(
            {"error": True, "type": type(e).__name__, "message": str(e)},
            indent=2,
            ensure_ascii=False,
        )

    return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": text}]}, "id": req_id}


def main() -> None:
    """Boucle standard JSON-RPC stdio pour serveur MCP."""
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
            method = req.get("method")
            req_id = req.get("id")
            params = req.get("params") if isinstance(req.get("params"), dict) else {}

            # Négociation par requête : message déclaré > état de session.
            declared, source = declared_version(params, None)
            decision = negotiate_version(declared or _SESSION_PROTOCOL_VERSION)
            tool_name = params.get("name") if method == "tools/call" else None

            if not decision.accepted:
                resp = invalid_version_error(req_id, decision.requested)
            elif method == "initialize":
                resp = handle_initialize(req_id, params, version_decision=decision)
            elif method == "tools/list":
                resp = handle_tools_list(req_id)
            elif method == "tools/call":
                resp = handle_tools_call(req_id, params)
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": req_id,
                }

            # Politique de repli : strictement une application par requête.
            apply_fallback_policy(
                decision,
                transport="stdio",
                method=method,
                tool_name=tool_name,
                header_present=None,
                declared_in_message=source != "absent",
            )
            attach_routing_meta(
                resp,
                protocol_version=decision.negotiated or PROTOCOL_VERSION_LEGACY,
                method=method,
                tool_name=tool_name,
            )

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {e}"},
                "id": None,
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
