"""
Sous-registre déclaratif CLI — Domaine Pipelines & Architecture (MLOOP-175-BE).

Pipelines : ingest, dream[pipeline], research, deep-search, crawl, teach,
             update-story, memory-hygiene.
Architecture : goal-cascade, grill, grill-project, wayfinder, to-tshirt,
               to-sow, to-spec, to-tickets, graph-run, deepen, diagnose.

Note doublon : dream apparaît dans analysis_core (handler dream:handle_dream)
et ici (handler pipeline:handle_dream). Le présent module sera chargé APRÈS
analysis_core dans __init__.py → pipeline:handle_dream gagne (comportement original).

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

PIPELINES_ARCH_COMMANDS: dict[str, dict] = {
    # ── Pipelines ──────────────────────────────────────────
    "ingest": {
        "handler": "pipeline:handle_ingest",
        "help": "Ingestion documentaire vers Markdown normalisé",
        "args": [
            {
                "name": "--initiative",
                "type": str,
                "default": None,
                "help": "Scope l'ingestion à reference/<initiative>/ et écrit sous docs/<initiative>/00-ingested/ (projets à structure par module). Si absent : ingestion globale plate (ADR-0102).",
            },
        ],
    },
    "dream": {
        "handler": "pipeline:handle_dream",
        "help": "Consolidation nocturne et compression mémorielle (Sleep-Wake)",
        "args": [],
    },
    "research": {
        "handler": "pipeline:handle_research",
        "help": "Session de recherche automatisée",
        "args": [
            {
                "name": "--query",
                "type": str,
                "default": "",
                "help": "Sujet de recherche",
            },
            {"name": "--url", "type": str, "help": "URL explicite"},
        ],
    },
    "deep-search": {
        "handler": "deep_search:handle_deep_search",
        "help": "Session de Deep Search autonome (Fact-Search local FTS5, recherche web et aspiration ciblée)",
        "args": [
            {
                "name": "--query",
                "type": str,
                "required": True,
                "help": "Sujet ou question de recherche approfondie",
            },
            {
                "name": "--max-sources",
                "type": int,
                "default": 5,
                "help": "Nombre maximal de sources web à aspirer (défaut: 5)",
            },
            {
                "name": "--depth",
                "type": int,
                "default": 0,
                "help": "Profondeur de découverte récursive (défaut: 0)",
            },
            {
                "name": "--render-js",
                "action": "store_true",
                "help": "Forcer le rendu Playwright local pour les pages dynamiques",
            },
            {
                "name": "--include-superseded",
                "action": "store_true",
                "help": "Inclure les documents obsolètes pénalisés dans Fact-Search",
            },
        ],
    },
    "crawl": {
        "handler": "pipeline:handle_crawl",
        "help": "Crawl intelligent d'une URL ou du backlog (LLMs.txt fast-path, cache TTL, regex filters)",
        "args": [
            {"name": "--url", "type": str, "help": "URL explicite à crawler"},
            {
                "name": "--max-age",
                "type": int,
                "help": "Cache TTL en secondes (réutilise le cache sans appel réseau)",
            },
            {
                "name": "--max-depth",
                "type": int,
                "default": 0,
                "help": "Profondeur maximale de découverte récursive (défaut: 0)",
            },
            {
                "name": "--include",
                "type": str,
                "help": "Regex des chemins d'URL à inclure",
            },
            {
                "name": "--exclude",
                "type": str,
                "help": "Regex des chemins d'URL à exclure",
            },
            {
                "name": "--allow-subdomains",
                "action": "store_true",
                "help": "Autoriser le suivi des sous-domaines du domaine principal",
            },
            {
                "name": "--no-llms-txt",
                "action": "store_true",
                "help": "Désactiver la détection prioritaire de llms.txt",
            },
            {
                "name": "--ignore-query",
                "action": "store_true",
                "help": "Nettoyer et ignorer les paramètres d'URL pour le dédoublonnage",
            },
            {
                "name": "--json-schema",
                "type": str,
                "help": "Chemin vers un JSON Schema pour extraction structurée LLM",
            },
            {
                "name": "--all-sources",
                "action": "store_true",
                "help": "Crawl global de toutes les sources du backlog/projet même si une URL explicite est fournie",
            },
            {
                "name": "--render-js",
                "action": "store_true",
                "help": "Activer le rendu JavaScript via Playwright local pour les SPAs",
            },
            {
                "name": "--no-github-tree",
                "action": "store_true",
                "help": "Désactiver l'exploration de l'arbre Git pour les dépôts GitHub",
            },
        ],
    },
    "teach": {
        "handler": "pipeline:handle_teach",
        "help": "Auto-apprentissage et mise à jour de la mémoire",
        "args": [],
    },
    "update-story": {
        "handler": "pipeline:handle_update_story",
        "help": "Mettre à jour une section H2 spécifique d'une story de façon AST-déterministe",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Chemin du récit (ex: backlog/stories/FOOD/US-08-FOOD.md)",
            },
            {
                "name": "--section",
                "type": str,
                "required": True,
                "help": "Titre de la section H2 (ex: 'Règles d'affaires')",
            },
            {
                "name": "--content",
                "type": str,
                "required": True,
                "help": "Nouveau contenu Markdown de la section",
            },
        ],
    },
    "memory-hygiene": {
        "handler": "pipeline:handle_memory_hygiene",
        "help": "Balayage de confiance de la mémoire vive",
        "args": [],
    },
    # ── Architecture ───────────────────────────────────────
    "goal-cascade": {
        "handler": "architecture:handle_goal_cascade",
        "help": "Alignement stratégique et Goal-Cascading (Wayfinder -> Epics -> Stories)",
        "args": [],
    },
    "grill": {
        "handler": "architecture:handle_grill",
        "help": "Session interactive Grill-with-Docs : Macro (projet transverse) ou Micro (story 1:1)",
        "args": [
            {"name": "--title", "type": str, "help": "Titre"},
            {"name": "--decision", "type": str, "help": "Décision retenue"},
            {"name": "--context", "type": str, "help": "Contexte"},
            {"name": "--positives", "type": str, "help": "Conséquences positives"},
            {"name": "--negatives", "type": str, "help": "Conséquences négatives"},
            {"name": "--story", "type": str, "help": "Identifiant du récit pour analyse micro 1:1"},
            {
                "name": "--mode",
                "type": str,
                "help": "Mode : round/atomic (déprécié : voir --format)",
            },
            {
                "name": "--format",
                "type": str,
                "help": "Format : round ou atomic (prime sur --mode)",
            },
            {"name": "--scope", "type": str, "help": "Périmètre : story, epic ou project"},
            {
                "name": "--health",
                "action": "store_true",
                "help": "Vérifie la santé de la fenêtre de contexte",
            },
        ],
    },
    "grill-project": {
        "handler": "architecture:handle_grill",
        "help": "Cadrage contradictoire macro d'avant-projet (Architecture globale, Loi 25, SSO, exclusions)",
        "args": [
            {"name": "--title", "type": str, "help": "Titre de l'arbitrage macro"},
            {"name": "--decision", "type": str, "help": "Décision retenue"},
            {"name": "--context", "type": str, "help": "Contexte macroscopique"},
            {"name": "--positives", "type": str, "help": "Conséquences positives"},
            {"name": "--negatives", "type": str, "help": "Conséquences négatives"},
            {
                "name": "--mode",
                "type": str,
                "help": "Mode : round (défaut)/atomic (déprécié : voir --format)",
            },
            {
                "name": "--format",
                "type": str,
                "help": "Format : round (défaut) ou atomic (prime sur --mode)",
            },
            {"name": "--scope", "type": str, "help": "Périmètre : story, epic ou project"},
            {
                "name": "--health",
                "action": "store_true",
                "help": "Vérifie la santé de la fenêtre de contexte",
            },
        ],
    },
    "wayfinder": {
        "handler": "architecture:handle_wayfinder",
        "help": "Initialiser ou mettre à jour la carte Wayfinder",
        "args": [
            {"name": "--title", "type": str, "help": "Titre de l'initiative"},
        ],
    },
    "to-tshirt": {
        "handler": "architecture:handle_to_tshirt",
        "help": "Générer un Dimensionnement Budgétaire d'avant-projet (T-Shirt Size) sous docs/01-architecture/",
        "args": [
            {"name": "--title", "type": str, "help": "Titre du projet ou de l'initiative"},
        ],
    },
    "to-sow": {
        "handler": "architecture:handle_to_sow",
        "help": "Générer un Énoncé des Travaux (SOW) contractuel sous docs/01-architecture/",
        "args": [
            {"name": "--title", "type": str, "help": "Titre du projet"},
            {
                "name": "--size",
                "type": str,
                "help": "Taille T-Shirt de référence (xs, s, m, M, l, L, xl)",
            },
        ],
    },
    "to-spec": {
        "handler": "architecture:handle_to_spec",
        "help": "Générer une spécification technique",
        "args": [
            {"name": "--title", "type": str, "help": "Titre pour la spécification"},
        ],
    },
    "to-tickets": {
        "handler": "architecture:handle_to_tickets",
        "help": "Découpage en tickets verticaux depuis l'architecture",
        "args": [],
    },
    "graph-run": {
        "handler": "architecture:handle_graph_run",
        "help": "Exécution Graph Engineering (DAG Multi-Agents)",
        "args": [
            {"name": "--title", "type": str, "help": "Titre initiative"},
        ],
    },
    "deepen": {
        "handler": "architecture:handle_deepen",
        "help": "Rapport HTML de profondeur d'architecture",
        "args": [],
    },
    "diagnose": {
        "handler": "architecture:handle_diagnose",
        "help": "Harnais de reproduction déterministe",
        "args": [
            {"name": "--symptom", "type": str, "help": "Symptôme"},
        ],
    },
}
