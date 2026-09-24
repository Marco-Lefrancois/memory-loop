"""
mcp_proxy_registry.py — Registre d'outils et filtre de phase du Proxy Aggregator.

Extraction déclarative du registre statique (ADR-0202, plafond modulaire) :
aucune dépendance au protocole MCP, uniquement la donnée de routage
phase → outils et le schéma JSON des outils exposés.
"""

from __future__ import annotations

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
