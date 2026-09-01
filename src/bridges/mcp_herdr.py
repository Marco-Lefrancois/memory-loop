"""
mcp_herdr.py - Herdr v0.8.0 MCP Bridge Server for mLoop Engine

Exposes Herdr automation primitives (Layout, Pane, Agent) as Model Context Protocol (MCP)
tools for System 2 Agentic Orchestrators (Claude Code, OpenCode, Antigravity, Cursor).
"""

import sys
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.core.herdr_adapter import HerdrAdapter, herdr

MCP_TOOLS = [
    {
        "name": "herdr_workspace_create",
        "description": "Crée un nouvel espace de travail Herdr. Retourne .result.root_pane.pane_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cwd": {"type": "string", "description": "Répertoire de travail"},
                "label": {"type": "string", "description": "Nom ou label de l'espace (ex: api, US-05)"},
                "no_focus": {"type": "boolean", "description": "Ne pas basculer le focus UI (défaut: true)"}
            },
            "required": ["cwd"]
        }
    },
    {
        "name": "herdr_pane_split",
        "description": "Scinde un volet terminal Herdr existant en deux. Retourne .result.pane.pane_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_pane_id": {"type": "string", "description": "Identifiant du volet cible (ex: p1, w1:p2)"},
                "direction": {"type": "string", "enum": ["right", "down"], "description": "Direction de la scission (défaut: right)"},
                "no_focus": {"type": "boolean", "description": "Ne pas basculer le focus UI (défaut: true)"}
            },
            "required": ["target_pane_id"]
        }
    },
    {
        "name": "herdr_agent_start",
        "description": "Démarre un agent de code reconnu (claude, opencode, codex, gemini, etc.) sur un volet terminal existant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Nom unique pour l'agent (ex: worker_1, reviewer)"},
                "kind": {"type": "string", "description": "Type d'agent (opencode, claude, codex, gemini, pi, etc.)"},
                "pane_id": {"type": "string", "description": "Identifiant du volet cible"},
                "extra_args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Arguments additionnels passés à l'exécutable (ex: ['--yolo', '--dangerously-skip-permissions'])"
                },
                "timeout_ms": {"type": "integer", "description": "Timeout de démarrage en ms (défaut: 30000)"}
            },
            "required": ["agent_name", "kind", "pane_id"]
        }
    },
    {
        "name": "herdr_agent_prompt",
        "description": "Envoie une instruction / prompt à un agent Herdr en cours d'exécution et peut attendre son achèvement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name_or_pane": {"type": "string", "description": "Nom de l'agent ou ID du volet"},
                "prompt_text": {"type": "string", "description": "Texte du prompt à soumettre"},
                "wait": {"type": "boolean", "description": "Attendre que le tour se termine (défaut: true)"},
                "timeout_ms": {"type": "integer", "description": "Timeout en ms (défaut: 300000)"}
            },
            "required": ["agent_name_or_pane", "prompt_text"]
        }
    },
    {
        "name": "herdr_agent_wait",
        "description": "Attend qu'un agent atteigne un des états de cycle de vie spécifiés (working, blocked, idle, done, unknown).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name_or_pane": {"type": "string", "description": "Nom de l'agent ou ID du volet"},
                "until_states": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste des états attendus (défaut: ['idle', 'done', 'blocked'])"
                },
                "timeout_ms": {"type": "integer", "description": "Timeout en ms (défaut: 300000)"}
            },
            "required": ["agent_name_or_pane"]
        }
    },
    {
        "name": "herdr_agent_read",
        "description": "Lit la sortie terminal PTY d'un agent. Supporte le défilement Alternate-Screen (--source recent-unwrapped) pour Claude Code et OpenCode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name_or_pane": {"type": "string", "description": "Nom de l'agent ou ID du volet"},
                "lines": {"type": "integer", "description": "Nombre de lignes à lire (défaut: 120)"},
                "source": {"type": "string", "description": "Source de lecture ('recent-unwrapped', 'recent', 'visible')"}
            },
            "required": ["agent_name_or_pane"]
        }
    },
    {
        "name": "herdr_pane_close",
        "description": "Ferme un volet terminal Herdr et libère ses ressources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pane_id": {"type": "string", "description": "Identifiant du volet à fermer"}
            },
            "required": ["pane_id"]
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Routes tool execution to HerdrAdapter functions."""
    try:
        if name == "herdr_workspace_create":
            return herdr.create_workspace(
                cwd=arguments["cwd"],
                label=arguments.get("label", "mloop-worker"),
                no_focus=arguments.get("no_focus", True)
            )
        elif name == "herdr_pane_split":
            return herdr.split_pane(
                target_pane_id=arguments["target_pane_id"],
                direction=arguments.get("direction", "right"),
                no_focus=arguments.get("no_focus", True)
            )
        elif name == "herdr_agent_start":
            return herdr.start_agent(
                agent_name=arguments["agent_name"],
                kind=arguments["kind"],
                pane_id=arguments["pane_id"],
                extra_args=arguments.get("extra_args"),
                timeout_ms=arguments.get("timeout_ms", 30000)
            )
        elif name == "herdr_agent_prompt":
            return herdr.prompt_agent(
                agent_name_or_pane=arguments["agent_name_or_pane"],
                prompt_text=arguments["prompt_text"],
                wait=arguments.get("wait", True),
                timeout_ms=arguments.get("timeout_ms", 300000)
            )
        elif name == "herdr_agent_wait":
            return herdr.wait_agent(
                agent_name_or_pane=arguments["agent_name_or_pane"],
                until_states=arguments.get("until_states", ["idle", "done", "blocked"]),
                timeout_ms=arguments.get("timeout_ms", 300000)
            )
        elif name == "herdr_agent_read":
            return herdr.read_agent_output(
                agent_name_or_pane=arguments["agent_name_or_pane"],
                lines=arguments.get("lines", 120),
                source=arguments.get("source", "recent-unwrapped")
            )
        elif name == "herdr_pane_close":
            return herdr.close_pane(pane_id=arguments["pane_id"])
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def main():
    """Stdio JSON-RPC MCP Server loop."""
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "mloop-herdr-mcp", "version": "0.8.0"}
                    }
                }
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": MCP_TOOLS}
                }
            elif method == "tools/call":
                params = req.get("params", {})
                t_name = params.get("name")
                t_args = params.get("arguments", {})
                tool_res = handle_tool_call(t_name, t_args)
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(tool_res, ensure_ascii=False, indent=2)}]
                    }
                }
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
