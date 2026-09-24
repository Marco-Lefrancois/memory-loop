"""
Sous-registre déclaratif CLI — Domaine Intelligence & Gates (MLOOP-175-BE).

Code Intelligence (ADR-0204) : code-init, code-explore, code-impact,
                                code-affected, code-status.
Graph Intelligence (ADR-0204/0363) : graph-status, graph-query,
                                      graph-explain, graph-impact.
Gates (ADR-0341) : gates, tree.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

INTELLIGENCE_COMMANDS: dict[str, dict] = {
    # ── Code Intelligence (CodeGraph - ADR-0204) ───────────
    "code-init": {
        "handler": "code_intelligence:handle_code_init",
        "help": "Initialiser l'index CodeGraph sur le code source",
        "args": [{"name": "--path", "type": str, "help": "Chemin explicite du code source"}],
    },
    "code-explore": {
        "handler": "code_intelligence:handle_code_explore",
        "help": "Explorer le code source via CodeGraph (AST & Call Paths)",
        "args": [
            {
                "name": "--query",
                "type": str,
                "required": True,
                "help": "Symbole ou question d'architecture",
            },
            {"name": "--path", "type": str, "help": "Chemin explicite du projet source"},
            {
                "name": "--compact",
                "action": "store_true",
                "help": "Résumé condensé (Token Budget Guardrail)",
            },
        ],
        "no_project": True,
    },
    "code-impact": {
        "handler": "code_intelligence:handle_code_impact",
        "help": "Calculer le rayon d'impact (Blast Radius) d'un symbole",
        "args": [
            {
                "name": "--symbol",
                "type": str,
                "required": True,
                "help": "Nom de la classe, méthode ou fonction",
            },
            {"name": "--path", "type": str, "help": "Chemin explicite du projet source"},
        ],
        "no_project": True,
    },
    "code-affected": {
        "handler": "code_intelligence:handle_code_affected",
        "help": "Identifier les tests affectés par les changements de code",
        "args": [
            {"name": "--files", "nargs": "*", "help": "Liste de fichiers sources modifiés"},
            {"name": "--path", "type": str, "help": "Chemin explicite du projet source"},
        ],
        "no_project": True,
    },
    "code-status": {
        "handler": "code_intelligence:handle_code_status",
        "help": "Afficher les statistiques de l'index CodeGraph",
        "args": [{"name": "--path", "type": str, "help": "Chemin explicite du projet source"}],
        "no_project": True,
    },
    # ── Graph Intelligence (Graphify - ADR-0204 / ADR-0363) ──
    "graph-status": {
        "handler": "graph_intelligence:handle_graph_status",
        "help": "Afficher les statistiques et la fraîcheur du graphe de connaissances",
        "args": [
            {
                "name": "--global",
                "dest": "global_graph",
                "action": "store_true",
                "help": "Graphe racine global mLoop",
            }
        ],
        "no_project": True,
    },
    "graph-query": {
        "handler": "graph_intelligence:handle_graph_query",
        "help": "Interroger le graphe de connaissances sur un concept, ADR ou règle (Agentic Retrieval)",
        "args": [
            {
                "name": "--query",
                "type": str,
                "required": True,
                "help": "Concept, identifiant ou mot-clé recherché",
            },
            {
                "name": "--limit",
                "type": int,
                "default": 5,
                "help": "Nombre maximal de résultats (budget de tokens)",
            },
            {
                "name": "--global",
                "dest": "global_graph",
                "action": "store_true",
                "help": "Graphe racine global mLoop",
            },
        ],
        "no_project": True,
    },
    "graph-explain": {
        "handler": "graph_intelligence:handle_graph_explain",
        "help": "Restituer la fiche conceptuelle et le voisinage 1-hop d'un nœud du graphe",
        "args": [
            {
                "name": "--concept",
                "type": str,
                "required": True,
                "help": "Identifiant ou nom du concept/ADR",
            },
            {
                "name": "--global",
                "dest": "global_graph",
                "action": "store_true",
                "help": "Graphe racine global mLoop",
            },
        ],
        "no_project": True,
    },
    "graph-impact": {
        "handler": "graph_intelligence:handle_graph_impact",
        "help": "Calculer le rayon d'impact conceptuel et architectural (Blast Radius)",
        "args": [
            {
                "name": "--target",
                "type": str,
                "required": True,
                "help": "Nom du concept, fichier ou composant cible",
            },
            {
                "name": "--global",
                "dest": "global_graph",
                "action": "store_true",
                "help": "Graphe racine global mLoop",
            },
        ],
        "no_project": True,
    },
    # ── Runnable Gates & Depth Tree (ADR-0341) ─────────────
    "gates": {
        "handler": "gates:handle_gates",
        "help": "Exécuter, vérifier ou auditer les portails d'acceptation (Runnable Gates - ADR-0341)",
        "args": [
            {"name": "--file", "type": str, "help": "Fichier de gates .gates.md spécifique"},
            {"name": "--scope", "type": str, "help": "Filtrer sur un périmètre ou sous-projet"},
            {
                "name": "--status",
                "action": "store_true",
                "help": "Afficher le statut sans exécuter les oracles",
            },
            {
                "name": "--reverify",
                "action": "store_true",
                "help": "Re-vérification stricte de tous les oracles",
            },
            {
                "name": "--lint",
                "action": "store_true",
                "help": "Audit de qualité des oracles anti-tautologies",
            },
        ],
    },
    "tree": {
        "handler": "gates:handle_tree",
        "help": "Afficher l'arbre d'exécution Depth Tree et l'état des gates (ADR-0341)",
        "args": [
            {"name": "--file", "type": str, "help": "Fichier de gates spécifique"},
            {"name": "--scope", "type": str, "help": "Filtrer sur un scope"},
        ],
    },
}
