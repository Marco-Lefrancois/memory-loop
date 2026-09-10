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

SERVER_NAME = "mloop-proxy-router"
SERVER_VERSION = "1.0.0"

# ──────────────────────────────────────────────
# Phase → Allowed Tool Namespaces mapping
# Controls which sub-server tools are visible per Story phase.
# ──────────────────────────────────────────────
PHASE_TOOL_FILTER = {
    "INIT": ["loop_mem_timeline", "loop_mem_search", "graph_query"],
    "ANALYZE": ["loop_mem_search", "loop_mem_get_observations", "graph_query", "graph_edge_search", "graph_explain", "graph_blast_radius"],
    "PLAN": ["loop_mem_search", "graph_query", "graph_edge_search", "graph_explain", "graph_blast_radius", "check_story_compliance"],
    "QA": ["loop_mem_search", "loop_mem_rho_search", "graph_blast_radius", "check_story_compliance"],
    "ALL": None,  # None = no filter, expose everything
}

# Current active phase (can be updated via set_phase tool)
_active_phase = "ALL"

# ──────────────────────────────────────────────
# STATIC TOOL REGISTRY
# Each tool entry declares which sub-server handles it.
# ──────────────────────────────────────────────
TOOL_REGISTRY = {
    # mloop_mem tools
    "loop_mem_search": {
        "server": "mloop_mem",
        "description": "Recherche dans la mémoire persistante de session mLoop (FTS5).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Terme de recherche."},
                "project": {"type": "string", "description": "Optionnel. Filtre par projet."},
                "type": {"type": "string", "enum": ["decision", "bugfix", "feature", "discovery"]}
            },
            "required": ["query"]
        }
    },
    "loop_mem_timeline": {
        "server": "mloop_mem",
        "description": "Timeline chronologique des observations d'un projet mLoop.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Nom du projet cible."}
            },
            "required": ["project"]
        }
    },
    "loop_mem_get_observations": {
        "server": "mloop_mem",
        "description": "Récupère le contenu détaillé d'observations par leurs IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ids": {"type": "array", "items": {"type": "integer"}}
            },
            "required": ["ids"]
        }
    },
    "loop_mem_code_rag": {
        "server": "mloop_mem",
        "description": "RAG sémantique sur le code source via Graphify (few-shot injection).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Description du composant recherché."}
            },
            "required": ["query"]
        }
    },
    "loop_mem_rho_search": {
        "server": "mloop_mem",
        "description": "Recherche dans la mémoire RHO (solutions d'erreurs documentées).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_trace": {"type": "string", "description": "La trace d'erreur à analyser."}
            },
            "required": ["error_trace"]
        }
    },
    # graphify tools
    "graph_query": {
        "server": "graphify",
        "description": "Interroge le sous-graphe de connaissances autour d'un concept métier (RM-XXX), d'une ADR ou d'un composant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Mot-clé ou concept recherché."},
                "project": {"type": "string", "description": "Nom optionnel du projet."}
            },
            "required": ["query"]
        }
    },
    "graph_edge_search": {
        "server": "graphify",
        "description": "Cherche des arêtes (edges) reliant directement deux concepts ou composants d'architecture.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Nœud source."},
                "target": {"type": "string", "description": "Nœud cible."},
                "project": {"type": "string", "description": "Nom optionnel du projet."}
            },
            "required": ["source", "target"]
        }
    },
    "graph_explain": {
        "server": "graphify",
        "description": "Génère une explication détaillée d'un nœud d'architecture et de ses voisins dans le graphe.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "Identifiant ou titre du nœud."},
                "project": {"type": "string", "description": "Nom optionnel du projet."}
            },
            "required": ["concept"]
        }
    },
    "graph_blast_radius": {
        "server": "graphify",
        "description": "Calcule le rayon d'impact (Blast Radius) ascendant et descendant pour un fichier ou concept.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Chemin du fichier ou nom du concept cible."},
                "project": {"type": "string", "description": "Nom optionnel du projet."}
            },
            "required": ["target"]
        }
    },
    "check_story_compliance": {
        "server": "mloop_mem",
        "description": "Vérifie la conformité Gherkin 4 Piliers (ADR-0301) et l'isolation technique d'un récit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Le contenu Markdown du récit à auditer."}
            },
            "required": ["content"]
        }
    },
    # Router meta-tool
    "set_phase": {
        "server": "router",
        "description": (
            "Définit la phase active de la Story pour filtrer les outils disponibles. "
            "Phases valides : INIT, ANALYZE, PLAN, QA, ALL."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "phase": {
                    "type": "string",
                    "enum": list(PHASE_TOOL_FILTER.keys()),
                    "description": "La phase à activer."
                }
            },
            "required": ["phase"]
        }
    },
    # Stateful session meta-tool
    "loop_mem_set_project": {
        "server": "mloop_mem",
        "description": (
            "Définit le projet actif pour la session MCP (Stateful Session). "
            "Évite de répéter le nom du projet à chaque appel d'outil."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Nom du projet à activer (ex: 'mLoop')."}
            },
            "required": ["project"]
        }
    }
}


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
                "result": {"isError": True, "content": [{"type": "text", "text": f"Sub-serveur '{server_script}' non trouvé."}]},
                "id": 1
            }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": f"Erreur sous-serveur: {e}"}]},
            "id": 1
        }


def handle_initialize(req_id):
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}
        },
        "id": req_id
    }


def handle_tools_list(req_id):
    global _active_phase
    tools = _get_visible_tools(_active_phase)
    log_error(f"Phase '{_active_phase}' — {len(tools)} outils exposés.")
    return {
        "jsonrpc": "2.0",
        "result": {"tools": tools},
        "id": req_id
    }


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
                "content": [{
                    "type": "text",
                    "text": f"✅ Phase active : **{new_phase}** — {len(tools)} outils disponibles."
                }]
            },
            "id": req_id
        }

    # Route to the right sub-server
    tool_meta = TOOL_REGISTRY.get(name)
    if not tool_meta:
        return {
            "jsonrpc": "2.0",
            "result": {"isError": True, "content": [{"type": "text", "text": f"Outil '{name}' inconnu ou non disponible dans la phase '{_active_phase}'."}]},
            "id": req_id
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
            params = req.get("params", {})

            if method == "initialize":
                res = handle_initialize(req_id)
            elif method == "tools/list":
                res = handle_tools_list(req_id)
            elif method == "tools/call":
                res = handle_tools_call(req_id, params)
            elif method in ("notifications/initialized", "ping"):
                continue
            else:
                if req_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Méthode '{method}' non supportée."},
                        "id": req_id
                    }
                else:
                    continue

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        except Exception as e:
            log_error(f"Erreur critique proxy: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
