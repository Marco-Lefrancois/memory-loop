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
        "description": "Envoie une instruction / prompt à un agent Herdr en arrière-plan. Acquitte immédiatement la livraison pour éviter tout timeout MCP. Pour sonder la progression, utiliser herdr_agent_wait ou herdr_agent_read.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name_or_pane": {"type": "string", "description": "Nom de l'agent ou ID du volet"},
                "prompt_text": {"type": "string", "description": "Texte du prompt à soumettre"},
                "wait": {"type": "boolean", "description": "Attendre un court instant (max 10s) ou acquitter immédiatement (défaut: false)"},
                "timeout_ms": {"type": "integer", "description": "Timeout en ms si wait=true (capé à 10000ms max)"}
            },
            "required": ["agent_name_or_pane", "prompt_text"]
        }
    },
    {
        "name": "herdr_agent_wait",
        "description": "Sonde l'état d'un agent Herdr (working, blocked, idle, done). Capé à 10s max pour éliminer les timeouts de transport.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name_or_pane": {"type": "string", "description": "Nom de l'agent ou ID du volet"},
                "until_states": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste des états attendus (défaut: ['idle', 'done', 'blocked'])"
                },
                "timeout_ms": {"type": "integer", "description": "Durée de sonde en ms (défaut: 10000ms max)"}
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
    },
    {
        "name": "herdr_layout_export",
        "description": "Exporte l'arbre BSP de la topologie de volets d'un onglet ou d'un volet Herdr (v0.8.2).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tab_id": {"type": "string", "description": "Identifiant de l'onglet cible"},
                "pane_id": {"type": "string", "description": "Identifiant du volet cible"}
            }
        }
    },
    {
        "name": "herdr_layout_apply",
        "description": "Applique une topologie BSP déclarative pour créer/remplacer un onglet dans un workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "Identifiant du workspace"},
                "root_tree": {"type": "object", "description": "Arbre BSP de layout (split / pane nodes)"},
                "tab_label": {"type": "string", "description": "Label de l'onglet (défaut: dev)"},
                "focus": {"type": "boolean", "description": "Basculer le focus (défaut: false)"}
            },
            "required": ["workspace_id", "root_tree"]
        }
    },
    {
        "name": "herdr_pane_report_metadata",
        "description": "Rapporte des jetons/métadonnées d'affichage pour un volet Herdr (titre, badges de statut, tokens sidebar).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pane_id": {"type": "string", "description": "Identifiant du volet"},
                "source": {"type": "string", "description": "Identifiant de la source rapportant les métadonnées (défaut: mloop)"},
                "title": {"type": "string", "description": "Titre du volet (max 80 car)"},
                "display_agent": {"type": "string", "description": "Nom d'affichage personnalisé pour l'agent"},
                "state_labels": {"type": "object", "description": "Labels de statut personnalisés (ex: {'working': 'Analyse INVEST'})"},
                "tokens": {"type": "object", "description": "Jetons personnalisés accessibles dans la sidebar ($token)"},
                "ttl_ms": {"type": "integer", "description": "Durée de vie des tokens en ms"}
            },
            "required": ["pane_id"]
        }
    },
    {
        "name": "herdr_notification_show",
        "description": "Affiche une notification toast légère dans l'UI Herdr sans voler le focus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre de la notification"},
                "body": {"type": "string", "description": "Corps textuel de la notification"},
                "position": {"type": "string", "enum": ["top-left", "top-right", "bottom-left", "bottom-right"], "description": "Position du toast"},
                "sound": {"type": "string", "enum": ["none", "done", "request"], "description": "Signal sonore"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "herdr_agent_explain",
        "description": "Explique l'évaluation et la classification de détection d'état d'un agent sous Herdr.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Nom de l'agent ou identifiant de volet"},
                "file_path": {"type": "string", "description": "Chemin vers un fichier de snapshot d'écran"},
                "agent_label": {"type": "string", "description": "Label de l'agent si analyse de fichier"},
                "verbose": {"type": "boolean", "description": "Mode verbeux"}
            }
        }
    },
    {
        "name": "herdr_zombies_reap",
        "description": "Audit et purge tous les volets workers orphelins (Zero Zombie Policy).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Nom optionnel du projet à auditer"}
            }
        }
    },
    {
        "name": "herdr_handoff_test",
        "description": "Exécute une simulation Handoff Zero-Ask à l'aveugle sur une User Story.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Nom du projet"},
                "story_id": {"type": "string", "description": "Identifiant de la story"},
                "dry_run": {"type": "boolean", "description": "Mode simulation"}
            },
            "required": ["project_name", "story_id"]
        }
    },
    {
        "name": "herdr_legacy_mine",
        "description": "Extrait les règles d'affaires enfouies dans un code source legacy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Nom du projet"},
                "source_path": {"type": "string", "description": "Chemin du code source legacy"},
                "target_domain": {"type": "string", "description": "Domaine métier cible"},
                "dry_run": {"type": "boolean", "description": "Mode simulation"}
            },
            "required": ["project_name", "source_path"]
        }
    },
    {
        "name": "herdr_shadow_estimate",
        "description": "Génère un contre-chiffrage contradictoire pessimiste basé sur les risques techniques.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Nom du projet"},
                "target_id": {"type": "string", "description": "Identifiant de l'Epic ou SOW"},
                "scope_description": {"type": "string", "description": "Description du périmètre"},
                "dry_run": {"type": "boolean", "description": "Mode simulation"}
            },
            "required": ["project_name", "target_id"]
        }
    },
    {
        "name": "herdr_visual_dissect",
        "description": "Dissecte une maquette et génère la matrice UI des 8 états.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Nom du projet"},
                "asset_path": {"type": "string", "description": "Chemin du fichier maquette"},
                "dry_run": {"type": "boolean", "description": "Mode simulation"}
            },
            "required": ["project_name", "asset_path"]
        }
    },
    {
        "name": "herdr_janitor_watch",
        "description": "Audite l'intégrité de la mémoire et des liens documentaires.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Nom du projet"},
                "dry_run": {"type": "boolean", "description": "Mode simulation"}
            },
            "required": ["project_name"]
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Routes tool execution to HerdrAdapter functions and logs event."""
    try:
        from src.utils.event_logger import get_event_logger
        logger_inst = get_event_logger(arguments.get("project_name"))
        logger_inst.log_event(
            event_type="MCP_HERDR_CALL",
            agent_id="MCP_Herdr",
            details={"tool": name, "arguments": {k: v for k, v in arguments.items() if k != "prompt_text"}}
        )
    except Exception:
        pass

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
            wait = arguments.get("wait", False)
            timeout_ms = min(arguments.get("timeout_ms", 10000), 10000) if wait else 10000
            return herdr.prompt_agent(
                agent_name_or_pane=arguments["agent_name_or_pane"],
                prompt_text=arguments["prompt_text"],
                wait=wait,
                timeout_ms=timeout_ms
            )
        elif name == "herdr_agent_wait":
            timeout_ms = min(arguments.get("timeout_ms", 10000), 10000)
            return herdr.wait_agent(
                agent_name_or_pane=arguments["agent_name_or_pane"],
                until_states=arguments.get("until_states", ["idle", "done", "blocked"]),
                timeout_ms=timeout_ms
            )
        elif name == "herdr_agent_read":
            return herdr.read_agent_output(
                agent_name_or_pane=arguments["agent_name_or_pane"],
                lines=arguments.get("lines", 120),
                source=arguments.get("source", "recent-unwrapped")
            )
        elif name == "herdr_pane_close":
            return herdr.close_pane(pane_id=arguments["pane_id"])
        elif name == "herdr_layout_export":
            return herdr.export_layout(
                tab_id=arguments.get("tab_id"),
                pane_id=arguments.get("pane_id")
            )
        elif name == "herdr_layout_apply":
            return herdr.apply_layout(
                workspace_id=arguments["workspace_id"],
                root_tree=arguments["root_tree"],
                tab_label=arguments.get("tab_label", "dev"),
                focus=arguments.get("focus", False)
            )
        elif name == "herdr_pane_report_metadata":
            return herdr.report_metadata(
                pane_id=arguments["pane_id"],
                source=arguments.get("source", "mloop"),
                title=arguments.get("title"),
                display_agent=arguments.get("display_agent"),
                state_labels=arguments.get("state_labels"),
                tokens=arguments.get("tokens"),
                ttl_ms=arguments.get("ttl_ms")
            )
        elif name == "herdr_notification_show":
            return herdr.show_notification(
                title=arguments["title"],
                body=arguments.get("body"),
                position=arguments.get("position", "bottom-right"),
                sound=arguments.get("sound", "none")
            )
        elif name == "herdr_agent_explain":
            return herdr.explain_agent(
                target=arguments.get("target"),
                file_path=arguments.get("file_path"),
                agent_label=arguments.get("agent_label"),
                verbose=arguments.get("verbose", False)
            )
        elif name == "herdr_zombies_reap":
            return herdr.audit_and_reap_zombies(
                project_name=arguments.get("project_name")
            )
        elif name == "herdr_handoff_test":
            from src.pipelines.delegation import run_handoff_simulator
            return run_handoff_simulator(
                project_name=arguments["project_name"],
                story_id=arguments["story_id"],
                dry_run=arguments.get("dry_run", False)
            )
        elif name == "herdr_legacy_mine":
            from src.pipelines.delegation import run_legacy_miner
            return run_legacy_miner(
                project_name=arguments["project_name"],
                source_path=arguments["source_path"],
                target_domain=arguments.get("target_domain"),
                dry_run=arguments.get("dry_run", False)
            )
        elif name == "herdr_shadow_estimate":
            from src.pipelines.delegation import run_shadow_estimator
            return run_shadow_estimator(
                project_name=arguments["project_name"],
                target_id=arguments["target_id"],
                scope_description=arguments.get("scope_description"),
                dry_run=arguments.get("dry_run", False)
            )
        elif name == "herdr_visual_dissect":
            from src.pipelines.delegation import run_visual_dissector
            return run_visual_dissector(
                project_name=arguments["project_name"],
                asset_path=arguments["asset_path"],
                dry_run=arguments.get("dry_run", False)
            )
        elif name == "herdr_janitor_watch":
            from src.pipelines.delegation import run_semantic_janitor
            return run_semantic_janitor(
                project_name=arguments["project_name"],
                dry_run=arguments.get("dry_run", False)
            )
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
