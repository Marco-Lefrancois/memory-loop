"""
Registre déclaratif des commandes CLI mLoop.

Chaque entrée définit :
- handler  : "<module>:<function>" (résolu dynamiquement par lazy import)
- help     : Description affichée dans `--help`
- args     : Liste de dicts passés à `add_argument()`
- aliases  : (optionnel) Noms alternatifs pour la commande
- no_project : (optionnel) True si la commande n'exige pas de contexte projet
"""

def _worker_runtime_kinds() -> str:
    """Déduit la liste des runtimes workers déclarés (SSOT `worker_runtimes`).

    Objectif : interdire **par construction** toute dérive entre l'aide CLI
    `--kind` et les runtimes réellement enregistrés (ADR-0346 / ADR-0370).
    Un repli statique borné est retourné si le registre est indisponible.
    """
    try:
        from src.core.worker_runtimes import WORKER_RUNTIMES

        return ", ".join(sorted(WORKER_RUNTIMES))
    except ImportError:
        return "opencode, cline, pi, omp"


# Liste dérivée du registre SSOT multi-runtimes (ADR-0346) — jamais dupliquée à la main.
WORKER_KIND_HELP = _worker_runtime_kinds()


COMMANDS: dict[str, dict] = {
    # ── Projet ─────────────────────────────────────────────
    "guide": {
        "handler": "project:handle_guide",
        "help": "Afficher le guide d'utilisation du pipeline CLI mLoop par phase ou synchroniser le SSOT",
        "args": [
            {
                "name": "--phase",
                "type": str,
                "choices": ["ingest", "plan", "build", "validate", "ship", "sow", "spec"],
                "help": "Filtrer par phase du cycle",
            },
            {
                "name": "--sync",
                "action": "store_true",
                "help": "Régénérer standards/protocols/CLI_PIPELINE_GUIDE.md depuis le code Python (ADR-0370)",
            },
        ],
        "no_project": True,
    },
    "init": {
        "handler": "project:handle_init",
        "help": "Initialiser un nouveau projet (Loi des 3 Piliers)",
        "args": [],
    },
    "resume": {
        "handler": "project:handle_resume",
        "help": "Restaurer la session anti-amnésie",
        "args": [],
    },
    "focus": {
        "handler": "project:handle_focus",
        "help": "Verrouiller l'attention sur un récit spécifique",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit",
            },
        ],
    },
    "vibe-check": {
        "handler": "project:handle_vibe_check",
        "help": "Guardrail pré-vol de la session (gouvernance de phase ADR-0339)",
        "args": [
            {
                "name": "--stage",
                "type": str,
                "choices": [
                    "init",
                    "spec",
                    "sow",
                    "plan",
                    "build",
                    "validate",
                    "ship",
                    "run",
                ],
                "help": "Étape du cycle de vie projet (auto-détectée par défaut)",
            },
            {
                "name": "--phase",
                "type": str,
                "choices": [
                    "init",
                    "spec",
                    "sow",
                    "plan",
                    "build",
                    "validate",
                    "ship",
                    "run",
                ],
                "help": "Alias de --stage",
            },
        ],
    },
    "gate-approve": {
        "handler": "project:handle_gate_approve",
        "help": "Valider formellement une Porte de Gouvernance (Gate 1 à 5 - ADR-0375)",
        "args": [
            {
                "name": "--gate",
                "type": int,
                "required": True,
                "help": "Numéro de porte (1: Ingestion & Cadrage, 2: DoR, 3: DoD, 4: Recette QA, 5: Clôture)",
            },
            {
                "name": "--approver",
                "type": str,
                "help": "Nom de l'approbateur (ex: 'Marco')",
            },
            {
                "name": "--notes",
                "type": str,
                "help": "Justification ou notes contractuelles d'approbation",
            },
        ],
    },
    "lifecycle-status": {
        "handler": "project:handle_lifecycle_status",
        "help": "Afficher l'état du cycle de vie projet et l'historique des portes (ADR-0339)",
        "args": [],
    },
    "lifecycle-clean": {
        "handler": "project:handle_lifecycle_clean",
        "help": "Archiver de manière réversible les stories orphelines créées prématurément (Zéro Ghost Bias / L-08)",
        "args": [
            {
                "name": "--confirm",
                "action": "store_true",
                "help": "Confirmer l'archivage sécurisé des stories et preuves prématurées",
            },
        ],
    },
    "sync-antigravity": {
        "handler": "project:handle_sync_antigravity",
        "help": "Synchroniser les tokens et interactions de l'IDE Antigravity vers le Token Ledger",
        "args": [
            {
                "name": "--conversation-id",
                "type": str,
                "help": "ID d'une conversation spécifique à synchroniser",
            },
            {
                "name": "--all",
                "action": "store_true",
                "help": "Scanner toutes les conversations de l'historique Antigravity",
            },
        ],
        "no_project": True,
    },
    "install-hooks": {
        "handler": "project:handle_install_hooks",
        "help": "Installer/désinstaller le hook Git pre-commit déterministe (code-check + struct-check — MLOOP-105-BE)",
        "args": [
            {
                "name": "--uninstall",
                "action": "store_true",
                "help": "Désinstaller le hook pre-commit géré par mLoop (refusé sur hook étranger)",
            },
        ],
    },
    "hook": {
        "handler": "hook:handle_hook",
        "help": "Déclencher ou tester un hook de cycle de vie ou de pré-compaction (ADR-0364)",
        "args": [
            {
                "name": "--event",
                "default": "pre_compact",
                "help": "Nom de l'événement (pre_compact, post_compact, resume, session_start)",
            },
            {
                "name": "--format",
                "choices": ["text", "json", "markdown"],
                "default": "text",
                "help": "Format de sortie",
            },
            {
                "name": "--story",
                "default": None,
                "help": "Identifiant de la story cible (optionnel)",
            },
        ],
    },
    "notebooklm": {
        "handler": "notebooklm:handle_notebooklm",
        "help": "Gestion, export SSOT et connexion au carnet Google NotebookLM officiel",
        "args": [
            {
                "name": "--bundle",
                "action": "store_true",
                "help": "Générer les bundles Markdown prêts pour l'import NotebookLM",
            },
            {
                "name": "--status",
                "action": "store_true",
                "help": "Vérifier l'état de l'authentification et les métadonnées",
            },
            {
                "name": "--auth",
                "action": "store_true",
                "help": "Lancer l'assistant interactif de connexion Chrome",
            },
        ],
        "no_project": True,
    },
    # ── Analyse ────────────────────────────────────────────
    "sync": {
        "handler": "analysis:handle_sync",
        "help": "WikiFix + Synchronisation d'état et modélisation Hypergraphe",
        "args": [
            {"name": "--verbose", "action": "store_true", "help": "Affichage détaillé"},
            {
                "name": "--incremental",
                "action": "store_true",
                "help": "Synchronisation différentielle incrémentale (ADR-0343)",
            },
            {
                "name": "--fast",
                "action": "store_true",
                "help": "Mode rapide : saute les exports lourds (Graphify) pour l'inner-loop",
            },
            {
                "name": "--story",
                "type": str,
                "help": "Cibler la synchronisation et l'EvidencePack sur une User Story spécifique",
            },
        ],
    },
    "wikifix": {
        "handler": "analysis:handle_sync",
        "help": "Alias de sync (audit de cohérence WikiFix)",
        "args": [
            {"name": "--verbose", "action": "store_true", "help": "Affichage détaillé"},
            {
                "name": "--incremental",
                "action": "store_true",
                "help": "Synchronisation différentielle incrémentale (ADR-0343)",
            },
            {
                "name": "--fast",
                "action": "store_true",
                "help": "Mode rapide : saute les exports lourds (Graphify) pour l'inner-loop",
            },
            {
                "name": "--story",
                "type": str,
                "help": "Cibler la synchronisation et l'EvidencePack sur une User Story spécifique",
            },
        ],
    },
    "export-obsidian": {
        "handler": "analysis:handle_export_obsidian",
        "help": "Exporter l'hypergraphe sous forme de coffre Obsidian avec wikilinks (ADR-0337 / ADR-0343)",
        "args": [
            {
                "name": "--out",
                "type": str,
                "help": "Répertoire de sortie (défaut: docs/07-obsidian-vault)",
            },
        ],
    },
    "hyper-query": {
        "handler": "analysis:handle_hyper_query",
        "help": "Interroger l'hypergraphe pour une User Story ou inspecter les statistiques (ADR-0343)",
        "args": [
            {"name": "--story", "type": str, "help": "Identifiant de la User Story"},
        ],
    },
    "dream": {
        "handler": "dream:handle_dream",
        "help": "Routine d'auto-consolidation et hygiène de mémoire Overnight Dreamer (ADR-0310)",
        "args": [],
    },
    "drill": {
        "handler": "analysis:handle_drill",
        "help": "Drill d'analyse approfondie",
        "args": [],
    },
    "confidence": {
        "handler": "analysis:handle_confidence",
        "help": "Évaluer le score de confiance d'un fichier",
        "args": [
            {"name": "--file", "type": str, "required": True, "help": "Fichier cible"},
        ],
    },
    "struct-check": {
        "handler": "analysis:handle_struct_check",
        "help": "Gatekeeper structurel Read-Only : hiérarchie titres, format listes, cohérence du gabarit blueprint (pré-Sentinel)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Story .md à vérifier (tous les récits du backlog si absent)",
            },
            {
                "name": "--strict",
                "action": "store_true",
                "help": "Mode strict : écarts H3/H4 et séparateurs = BLOCKING",
            },
            {
                "name": "--verbose",
                "action": "store_true",
                "help": "Affiche le détail de tous les checks (pass + fail)",
            },
        ],
    },
    "code-check": {
        "handler": "build_harness:handle_code_check",
        "help": "Linter statique AST déterministe mLoop (modularité ADR-0202, standards ADR-0369 & ADR-0381)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Chemin du fichier Python à auditer",
            },
            {
                "name": "--story",
                "type": str,
                "help": "Identifiant du récit dont les fichiers associés doivent être audités",
            },
            {
                "name": "--all",
                "action": "store_true",
                "help": "Auditer l'ensemble des modules Python sous src/",
            },
        ],
        "no_project": True,
    },
    "code-tournament": {
        "handler": "build_harness:handle_code_tournament",
        "help": "Moteur de tournoi multi-draft et arbitrage Pareto (ADR-0373, ADR-0381)",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit (ex. MLOOP-072-BE)",
            },
            {
                "name": "--target",
                "type": str,
                "required": True,
                "help": "Chemin du fichier cible de production à promouvoir",
            },
            {
                "name": "--test-file",
                "type": str,
                "help": "Chemin explicite du banc de test unitaire pytest",
            },
        ],
        "no_project": True,
    },
    "tdd-enforce": {
        "handler": "build_harness:handle_tdd_enforce",
        "help": "Protocole TDD Red-Green Enforcement et verrou Gate 3 (ADR-0381)",
        "args": [
            {
                "name": "--phase",
                "type": str,
                "required": True,
                "choices": ["red", "green", "verify"],
                "help": "Phase du protocole TDD (red: échec initial, green: succès complet, verify: contrôle Gate 3)",
            },
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit (ex. MLOOP-082-BE)",
            },
            {
                "name": "--test-file",
                "type": str,
                "help": "Chemin du banc de test unitaire",
            },
            {
                "name": "--source-file",
                "type": str,
                "help": "Chemin du fichier source de production (requis pour la phase green)",
            },
        ],
        "no_project": True,
    },
    "validate-sprint": {
        "handler": "validation:handle_validate_sprint",
        "help": "Certification déterministe de sprint Phase 4 (tests, linter AST, CEL 4-piliers) (ADR-0383 / MLOOP-090-BE)",
        "args": [
            {
                "name": "--timeout",
                "type": float,
                "default": 240.0,
                "help": "Délai maximal d'exécution du banc de test pytest (secondes)",
            },
            {
                "name": "--test-dir",
                "type": str,
                "help": "Répertoire ou fichier de test spécifique pour la certification",
            },
        ],
    },
    "story-clean": {
        "handler": "analysis:handle_story_clean",
        "help": "Nettoie les blocs de traçabilité injectés dans les récits (post-decouplage)",
        "args": [],
    },
    "rubber-duck": {
        "handler": "analysis:handle_rubber_duck",
        "help": "Agent Sentinel — revue contradictoire de fond (Avocat du Diable avec discernement & rigueur)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Fichier spécifique à évaluer (optionnel)",
            },
            {
                "name": "--suggest-patch",
                "action": "store_true",
                "help": "Générer et afficher des blocs Gherkin de remédiation chirurgicale",
            },
        ],
    },
    "multi-draft": {
        "handler": "multi_draft:handle_multi_draft",
        "help": "Challenge d'évaluation comparative locale multi-branches (struct-check + Sentinel) — ADR-0373",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit (ex: REC-010-BE)",
            },
            {
                "name": "--eval-only",
                "action": "store_true",
                "help": "Évaluer les drafts existants sans en générer de nouveaux",
            },
            {
                "name": "--strict",
                "action": "store_true",
                "default": True,
                "help": "Mode strict : violations struct-check = BLOCKING (défaut: True)",
            },
        ],
    },
    "memo-search": {
        "handler": "memo_search:handle_memo_search",
        "help": "Sélectionner la stratégie mémoire ALMA optimale",
        "args": [
            {
                "name": "--query",
                "type": str,
                "help": "Mot-clé ou domaine cible (ex: cmp, invest, maui)",
            },
        ],
    },
    "blast": {
        "handler": "analysis:handle_blast",
        "help": "Calcul du rayon d'impact (Blast Radius) d'un fichier ou composant",
        "args": [
            {"name": "--file", "type": str, "help": "Fichier source cible"},
            {"name": "--target", "type": str, "help": "Symbole ou composant cible"},
        ],
    },
    "chunk": {
        "handler": "analysis:handle_chunk",
        "help": "Découpage sémantique d'un fichier Markdown (ADR-0323)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "required": True,
                "help": "Fichier Markdown à découper",
            },
        ],
    },
    "agentic-extract": {
        "handler": "analysis:handle_agentic_extract",
        "help": "Extraction documentaire agentique multi-passes (ADR-0323)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "required": True,
                "help": "Fichier Markdown à analyser",
            },
        ],
    },
    "eval-harvest": {
        "handler": "analysis:handle_eval_harvest",
        "help": "Moissonner les anomalies d'audit en cas d'évaluation Evals (ADR-0326)",
        "args": [],
    },
    "context-watch": {
        "handler": "analysis:handle_context_watch",
        "help": "Surveiller l'occupation de la fenêtre de contexte et alerter la Dumb-Zone (ADR-0326)",
        "args": [],
    },
    "token-tracker": {
        "handler": "analysis:handle_token_tracker",
        "no_project": True,
        "help": "Auditer la consommation de tokens et de coûts par interaction, projet et clé LiteLLM (ADR-0329)",
        "args": [
            {
                "name": "--today",
                "action": "store_true",
                "help": "Filtrer uniquement sur la date du jour",
            },
            {
                "name": "--date",
                "type": str,
                "default": None,
                "help": "Filtrer sur une date spécifique (YYYY-MM-DD)",
            },
            {
                "name": "--top",
                "type": int,
                "default": 10,
                "help": "Nombre d'interactions les plus lourdes à afficher (défaut: 10)",
            },
        ],
    },
    "supersession-sync": {
        "handler": "analysis:handle_supersession_sync",
        "help": "Synchroniser le registre de supersession des règles et décisions (ADR-0326)",
        "args": [],
    },
    "distill-invest": {
        "handler": "analysis:handle_distill_invest",
        "help": "Générer un jeu de données de distillation pour l'audit INVEST et Gherkin (ADR-0328)",
        "args": [],
    },
    "parent-resolve": {
        "handler": "analysis:handle_parent_resolve",
        "help": "Résoudre le bloc parent contextuel d'un extrait ou d'une règle (ADR-0328)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Fichier source Markdown à inspecter",
            },
            {
                "name": "--query",
                "type": str,
                "default": "",
                "help": "Extrait sémantique à localiser",
            },
        ],
    },
    "story-clean": {
        "handler": "analysis:handle_story_clean",
        "help": "Nettoyer les sections de mémoire temporaires (Suite Mémoire, Notes de Traçabilité) des stories (ADR-0301)",
        "args": [
            {
                "name": "--verbose",
                "action": "store_true",
                "help": "Afficher le détail de chaque fichier inspecté",
            },
        ],
    },
    "extract": {
        "handler": "extraction:handle_extract",
        "help": "Extraction déclarative YAML vers Knowledge Abstracts structurés (ADR-0342)",
        "args": [
            {
                "name": "--template",
                "type": str,
                "help": "Nom du template (business_rules, data_models, api_contracts, ui_matrix)",
            },
            {
                "name": "--source",
                "type": str,
                "help": "Fichier Markdown source à distiller",
            },
            {
                "name": "--target",
                "type": str,
                "help": "Répertoire de destination personnalisé (optionnel)",
            },
            {
                "name": "--format",
                "type": str,
                "choices": ["markdown", "json"],
                "default": "markdown",
                "help": "Format de sortie (défaut: markdown)",
            },
            {
                "name": "--list",
                "action": "store_true",
                "help": "Lister les templates d'extraction déclarative disponibles",
            },
        ],
    },
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
    # ── Validation ─────────────────────────────────────────
    "aoep": {
        "handler": "validation:handle_aoep",
        "help": "Évaluation AOEP (Agent Operational Excellence Protocol)",
        "args": [],
    },
    "audit-loop": {
        "handler": "validation:handle_audit_loop",
        "help": "Audit de boucle complet",
        "args": [],
    },
    "eval": {
        "handler": "validation:handle_eval",
        "help": "Évaluation automatisée du projet",
        "args": [],
    },
    "calibrate": {
        "handler": "validation:handle_calibrate",
        "help": "Auto-étalonnage de l'écosystème mLoop",
        "args": [],
    },
    "plugin-validate": {
        "handler": "validation:handle_plugin_validate",
        "help": "Valider la conformité Agent Plugin 1.0",
        "args": [
            {
                "name": "--plugin-root",
                "type": str,
                "help": "Racine du plugin (défaut: .agents/)",
            },
            {
                "name": "--strict",
                "action": "store_true",
                "help": "Mode strict (warnings = erreurs)",
            },
        ],
    },
    # ── Tooling ────────────────────────────────────────────
    "dashboard": {
        "handler": "dashboard:handle_dashboard",
        "help": "Tableau de bord d'observabilité et supervision souverain mLoop (FastAPI / Zero-Docker)",
        "no_project": True,
        "aliases": ["ui", "supervision"],
        "args": [
            {"name": "--port", "type": int, "default": 8080, "help": "Port du serveur web local"},
            {
                "name": "--no-browser",
                "action": "store_true",
                "help": "Ne pas ouvrir automatiquement le navigateur",
            },
        ],
    },
    "drawdb": {
        "handler": "tooling:handle_drawdb",
        "help": "Pipeline DrawDB (serveur, export, import, sync)",
        "no_project": True,
        "args": [
            {
                "name": "--action",
                "type": str,
                "choices": ["serve", "export", "import", "sync"],
                "default": "serve",
            },
            {"name": "--input", "type": str, "help": "Fichier d'entrée"},
            {"name": "--output", "type": str, "help": "Fichier de sortie"},
            {"name": "--port", "type": int, "default": 8080},
        ],
    },
    "optimize": {
        "handler": "tooling:handle_optimize",
        "help": "Optimisation RHO",
        "args": [
            {
                "name": "--keyword",
                "type": str,
                "required": True,
                "help": "Mot-clé pour RHO optimize",
            },
            {
                "name": "--msg",
                "type": str,
                "required": True,
                "help": "Message pour RHO optimize",
            },
            {
                "name": "--scope",
                "type": str,
                "choices": ["project", "global"],
                "default": "project",
                "help": "Portée",
            },
        ],
    },
    "svg-optimize": {
        "handler": "tooling:handle_svg_optimize",
        "help": "Optimisation et minification des fichiers SVG",
        "args": [
            {
                "name": "--input",
                "type": str,
                "help": "Fichier, dossier ou motif (*.svg)",
            },
        ],
    },
    "hill-climb": {
        "handler": "tooling:handle_hill_climb",
        "help": "Test Hill-Climbing (mutation-évaluation)",
        "args": [],
    },
    "archify": {
        "handler": "tooling:handle_archify",
        "help": "Générer et valider des diagrammes d'architecture interactifs vectoriels (Archify)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Chemin du fichier JSON de spécification",
            },
            {
                "name": "--output",
                "type": str,
                "help": "Chemin du fichier HTML de sortie (défaut: même nom .html)",
            },
            {
                "name": "--type",
                "type": str,
                "default": None,
                "choices": [
                    "architecture",
                    "workflow",
                    "sequence",
                    "dataflow",
                    "lifecycle",
                    "flow",
                ],
                "help": "Type de diagramme (architecture, workflow, sequence, dataflow, lifecycle - auto-détecté si omis)",
            },
            {
                "name": "--quality",
                "type": str,
                "default": "showcase",
                "choices": ["draft", "standard", "showcase"],
                "help": "Profil de qualité",
            },
            {
                "name": "--validate-only",
                "action": "store_true",
                "help": "Effectuer uniquement la validation Showcase sans générer le HTML",
            },
            {
                "name": "--open",
                "action": "store_true",
                "help": "Ouvrir automatiquement dans le navigateur par défaut",
            },
            {
                "name": "--doctor",
                "action": "store_true",
                "help": "Vérifier la santé, les gabarits et les validateurs du moteur Archify",
            },
        ],
        "no_project": True,
    },
    "drawdb": {
        "handler": "tooling:handle_drawdb",
        "help": "Lancer le hub souverain local de visualisation de schéma de base de données (ERD & Tables)",
        "args": [
            {
                "name": "--port",
                "type": int,
                "default": 8080,
                "help": "Port d'écoute du serveur local (défaut: 8080)",
            },
            {
                "name": "--no-open",
                "action": "store_true",
                "help": "Ne pas ouvrir automatiquement le navigateur",
            },
        ],
        "no_project": True,
    },
    # ── Export ─────────────────────────────────────────────
    "jira_sync": {
        "handler": "export:handle_jira_sync",
        "aliases": ["jira-sync"],
        "help": (
            "Synchronisation ciblée Jira Cloud (Fail-Closed). "
            "Requiert --story ou --stories pour cibler des tickets. "
            "Le mode dry-run est actif par défaut ; utiliser --apply + --confirm-scope pour écrire."
        ),
        "args": [
            {
                "name": "--story",
                "type": str,
                "default": None,
                "help": "Clé Jira ou ID logique d'un récit unique à synchroniser (ex: MMA-4651 ou US-01).",
            },
            {
                "name": "--stories",
                "type": str,
                "default": None,
                "help": "Liste de clés/IDs séparées par des virgules (ex: MMA-4651,MMA-4652).",
            },
            {
                "name": "--apply",
                "action": "store_true",
                "default": False,
                "help": "Active l'écriture réelle sur Jira. Doit être combiné avec --confirm-scope.",
            },
            {
                "name": "--confirm-scope",
                "type": str,
                "default": None,
                "help": (
                    "Confirmation du périmètre exact (même liste que --story/--stories). "
                    "Doit correspondre exactement aux tickets éligibles. Fail-Closed si divergence."
                ),
            },
            {
                "name": "--all",
                "action": "store_true",
                "default": False,
                "help": "[ADMINISTRATEUR] Synchronise toutes les stories éligibles. Requiert aussi --apply et --confirm-all-project-stories.",
            },
            {
                "name": "--confirm-all-project-stories",
                "action": "store_true",
                "default": False,
                "help": "[ADMINISTRATEUR] Confirmation explicite du mode global. Utilisé uniquement avec --all.",
            },
            {
                "name": "--allow-in-analyze",
                "action": "store_true",
                "default": False,
                "help": "Déroge au blocage des statuts IN_ANALYZE pour provisionnement d'une coquille Jira.",
            },
            {
                "name": "--dry-run",
                "action": "store_true",
                "default": False,
                "help": "Force l'affichage du rapport de prévisualisation sans écriture (comportement par défaut sans --apply).",
            },
        ],
    },
    "jira-read": {
        "handler": "export:handle_jira_read",
        "help": (
            "Lecture Read-Only d'un ticket Jira Cloud (API v3) : restitue la description "
            "ADF convertie en Markdown lisible (diff Jira <-> récit local). Aucune écriture."
        ),
        "args": [
            {
                "name": "--issue",
                "type": str,
                "default": None,
                "help": "Clé Jira du ticket à lire (ex: COUVBOIRE-1062).",
            },
            {
                "name": "--out",
                "type": str,
                "default": None,
                "help": "Chemin de sortie Markdown optionnel. Si absent, affiche dans la console.",
            },
        ],
        "no_project": True,
    },
    "plugin-export": {
        "handler": "export:handle_plugin_export",
        "help": "Exporter un package Agent Plugin 1.0 portable",
        "args": [
            {
                "name": "--output",
                "type": str,
                "help": "Répertoire de sortie pour l'export",
            },
        ],
    },
    "cycle-status": {
        "handler": "export:handle_cycle_status",
        "help": "Afficher le statut du cycle courant",
        "aliases": ["timeline", "status"],
        "args": [],
    },
    "self-dev": {
        "handler": "export:handle_self_dev",
        "help": "Auto-développement du framework mLoop",
        "args": [],
    },
    "unlearn": {
        "handler": "export:handle_unlearn",
        "help": "Désapprentissage d'un concept",
        "args": [
            {
                "name": "--concept",
                "type": str,
                "required": True,
                "help": "Concept à désapprendre",
            },
        ],
    },
    "canvas": {
        "handler": "export:handle_canvas",
        "help": "Générer et synchroniser les toiles interactives 2D Obsidian Canvas (.canvas) (ADR-0337)",
        "args": [],
    },
    # ── Skill Registry (SEP-2640 / MLOOP-011-BE) ───────────
    "skill-list": {
        "handler": "skill:handle_skill_list",
        "help": "Lister les compétences enregistrées dans le registre skill:// (SEP-2640)",
        "args": [],
    },
    "skill-invoke": {
        "handler": "skill:handle_skill_invoke",
        "help": "Invoquer une compétence via son URI skill:// (SEP-2640)",
        "args": [
            {
                "name": "--uri",
                "type": str,
                "required": True,
                "help": "URI de la compétence (ex: skill://preload-context)",
            },
        ],
    },
    "skill-doctor": {
        "handler": "skill:handle_skill_doctor",
        "no_project": True,
        "help": "Auditer l'hygiène et le coût en jetons des compétences .agents/skills/ (ADR-0348 / Claude Code v2.1.261)",
        "args": [
            {
                "name": "--threshold",
                "type": int,
                "default": 2000,
                "help": "Seuil d'alerte en jetons par compétence (défaut: 2000)",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Sortie structurée en JSON",
            },
            {
                "name": "--no-tombstone",
                "action": "store_true",
                "help": "Désactiver les suggestions de mise en TOMBSTONE",
            },
        ],
    },
    "doctor": {
        "handler": "skill:handle_skill_doctor",
        "no_project": True,
        "help": "Bilan de santé global et diagnostic d'hygiène des compétences et agents mLoop (ADR-0377)",
        "args": [
            {
                "name": "--skills",
                "action": "store_true",
                "help": "Auditer l'hygiène contextuelle des compétences",
            },
            {
                "name": "--agents",
                "action": "store_true",
                "help": "Sonder la disponibilité et les versions des agents CLI locaux (ADR-0377)",
            },
            {
                "name": "--threshold",
                "type": int,
                "default": 2000,
                "help": "Seuil d'alerte en jetons par compétence (défaut: 2000)",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Sortie structurée en JSON",
            },
            {
                "name": "--no-tombstone",
                "action": "store_true",
                "help": "Désactiver les suggestions de mise en TOMBSTONE",
            },
        ],
    },
    "agent-probe": {
        "handler": "skill:handle_agent_probe",
        "no_project": True,
        "help": "Sonder les runtimes et CLI des agents locaux aval (Herdr, OpenCode, Claude Code... - ADR-0377)",
        "args": [
            {
                "name": "--agent",
                "type": str,
                "help": "Cibler un agent spécifique (ex: herdr, opencode)",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Sortie structurée en JSON",
            },
        ],
    },

    # ── Code Intelligence (CodeGraph - ADR-0204) ───────────
    "code-init": {
        "handler": "code_intelligence:handle_code_init",
        "help": "Initialiser l'index CodeGraph sur le code source",
        "args": [
            {
                "name": "--path",
                "type": str,
                "help": "Chemin explicite du code source à indexer",
            },
        ],
    },
    "code-explore": {
        "handler": "code_intelligence:handle_code_explore",
        "help": "Explorer le code source via CodeGraph (AST & Call Paths)",
        "args": [
            {
                "name": "--query",
                "type": str,
                "required": True,
                "help": "Symbole, méthode ou question d'architecture",
            },
            {
                "name": "--path",
                "type": str,
                "help": "Chemin explicite du projet source",
            },
            {
                "name": "--compact",
                "action": "store_true",
                "help": "Restituer un résumé condensé sans corps de code verbatim (Token Budget Guardrail)",
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
            {
                "name": "--path",
                "type": str,
                "help": "Chemin explicite du projet source",
            },
        ],
        "no_project": True,
    },
    "code-affected": {
        "handler": "code_intelligence:handle_code_affected",
        "help": "Identifier les tests affectés par les changements de code",
        "args": [
            {
                "name": "--files",
                "nargs": "*",
                "help": "Liste de fichiers sources modifiés",
            },
            {
                "name": "--path",
                "type": str,
                "help": "Chemin explicite du projet source",
            },
        ],
        "no_project": True,
    },
    "code-status": {
        "handler": "code_intelligence:handle_code_status",
        "help": "Afficher les statistiques de l'index CodeGraph",
        "args": [
            {
                "name": "--path",
                "type": str,
                "help": "Chemin explicite du projet source",
            },
        ],
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
                "help": "Cibler le graphe racine global mLoop",
            },
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
                "help": "Nombre maximal de résultats restitués (budget de tokens)",
            },
            {
                "name": "--global",
                "dest": "global_graph",
                "action": "store_true",
                "help": "Cibler le graphe racine global mLoop",
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
                "help": "Cibler le graphe racine global mLoop",
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
                "help": "Cibler le graphe racine global mLoop",
            },
        ],
        "no_project": True,
    },
    # ── Runnable Gates & Depth Tree (ADR-0341) ─────────────
    "gates": {
        "handler": "gates:handle_gates",
        "help": "Exécuter, vérifier ou auditer les portails d'acceptation (Runnable Gates - ADR-0341)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Chemin du fichier de gates .gates.md spécifique",
            },
            {
                "name": "--scope",
                "type": str,
                "help": "Filtrer sur un périmètre ou sous-projet",
            },
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
    # ── Herdr Runtime & Subagents (ADR-0029 / ADR-0205) ────
    "worker-spawn": {
        "handler": "worker:handle_worker_spawn",
        "help": "Instancier un sous-agent Herdr isolé pour un récit spécifique (Clean Slate)",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit (ex: MMA-4651 ou US-01-FOOD)",
            },
            {
                "name": "--kind",
                "type": str,
                "default": "opencode",
                "help": f"Type d'agent ({WORKER_KIND_HELP})",
            },
            {
                "name": "--model",
                "type": str,
                "default": None,
                "help": "Modèle spécifique sur LiteLLM (ex: nmedia_cloud/claude-opus-4.8)",
            },
            {
                "name": "--task-type",
                "type": str,
                "default": None,
                "choices": [
                    "deepening",
                    "validation",
                    "deepsearch",
                    "build",
                    "compaction",
                ],
                "help": "Type de mission pour sélection dynamique du meilleur modèle",
            },
        ],
    },
    "worker-status": {
        "handler": "worker:handle_worker_status",
        "help": "Afficher le statut et la santé des workers Herdr actifs (ou d'un récit spécifique)",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": False,
                "help": "Identifiant du récit pour inspection ciblée et non-bloquante via PTY read",
            },
        ],
    },
    "worker-harvest": {
        "handler": "worker:handle_worker_harvest",
        "help": "Moissonner les preuves d'exécution PTY du worker et mettre à jour l'EvidencePack",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit",
            },
            {
                "name": "--lines",
                "type": int,
                "default": 150,
                "help": "Nombre de lignes de log PTY à moissonner",
            },
        ],
    },
    "worker-close": {
        "handler": "worker:handle_worker_close",
        "help": "Fermer le volet d'un worker Herdr et libérer ses ressources",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit ou nom du volet",
            },
        ],
    },
    "worker-reap": {
        "handler": "worker:handle_worker_reap",
        "help": "Purger les volets et agents orphelins ou inactifs (ADR-0355 Stall Detection)",
        "args": [
            {
                "name": "--timeout",
                "type": int,
                "default": 300,
                "help": "Délai d'inactivité en secondes pour considérer un worker comme bloqué",
            },
            {
                "name": "--force",
                "action": "store_true",
                "help": "Forcer la fermeture des volets sans attendre de confirmation",
            },
        ],
    },
    "worker-handoff-test": {
        "handler": "worker:handle_worker_handoff_test",
        "help": "Tester la complétude et clarté d'une story par un dev naïf (Zero-Ask Simulator)",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant de la story à tester",
            },
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Mode simulation sans appel de modèle",
            },
        ],
    },
    "worker-legacy-mine": {
        "handler": "worker:handle_worker_legacy_mine",
        "help": "Extraire les règles métier et calculs d'une base de code legacy",
        "args": [
            {
                "name": "--source",
                "type": str,
                "required": True,
                "help": "Chemin du dossier source legacy",
            },
            {
                "name": "--domain",
                "type": str,
                "default": None,
                "help": "Nom de domaine métier",
            },
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Mode simulation sans appel de modèle",
            },
        ],
    },
    "worker-shadow-estimate": {
        "handler": "worker:handle_worker_shadow_estimate",
        "help": "Générer un contre-chiffrage contradictoire pessimiste basé sur les risques",
        "args": [
            {
                "name": "--epic",
                "type": str,
                "default": "EPIC-GLOBAL",
                "help": "Identifiant de l'Epic ou SOW",
            },
            {
                "name": "--desc",
                "type": str,
                "default": None,
                "help": "Description ou contexte du scope",
            },
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Mode simulation sans appel de modèle",
            },
        ],
    },
    "worker-visual-dissect": {
        "handler": "worker:handle_worker_visual_dissect",
        "help": "Dissecter une maquette et extraire la matrice des 8 états UI",
        "args": [
            {
                "name": "--asset",
                "type": str,
                "required": True,
                "help": "Chemin du fichier maquette (SVG, PNG)",
            },
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Mode simulation sans appel de modèle",
            },
        ],
    },
    "worker-janitor-watch": {
        "handler": "worker:handle_worker_janitor_watch",
        "help": "Auditer silencieusement l'intégrité de la mémoire et des liens",
        "args": [
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Mode simulation sans appel de modèle",
            },
        ],
    },
    # ── Daemon & Architecture Codex Extensions ─────────────
    "app-server": {
        "handler": "daemon:handle_app_server",
        "help": "Démarrer le démon d'interfaçage JSON-RPC 2.0 mLoop App-Server",
        "args": [],
        "no_project": True,
    },
    "guardian-status": {
        "handler": "daemon:handle_guardian_status",
        "help": "Afficher l'état du Guardian Auto-Reviewer et du Circuit Breaker",
        "args": [],
    },
    "role-list": {
        "handler": "daemon:handle_role_list",
        "help": "Lister les manifestes de rôles agentiques déclaratifs disponibles",
        "args": [],
    },
    # ── Semantic Cache & LLM Optimizations (ADR-0336) ─────
    "cache-stats": {
        "handler": "cache:handle_cache_stats",
        "help": "Afficher les statistiques du cache sémantique déterministe LLM",
        "args": [],
        "no_project": True,
    },
    "cache-clear": {
        "handler": "cache:handle_cache_clear",
        "help": "Effacer le cache sémantique déterministe LLM",
        "args": [
            {
                "name": "--model",
                "type": str,
                "default": None,
                "help": "Modèle spécifique à purger",
            },
        ],
        "no_project": True,
    },
    # ── Fact-Check & NLI Ground Truth (ADR-0326 / ADR-0352) ──
    "fact-check": {
        "handler": "fact_check:handle_fact_check",
        "help": "Exécuter l'audit Fact-Check NLI sur une User Story et émettre son certificat",
        "args": [
            {
                "name": "--story",
                "type": str,
                "help": "Identifiant ou requête vers le récit à auditer",
            },
            {
                "name": "--strict",
                "action": "store_true",
                "help": "Mode strict : échoue si des exigences sont sans preuve",
            },
        ],
    },
    "fact-search": {
        "handler": "fact_search:handle_fact_search",
        "help": "Recherche factuelle haute précision dans l'index FTS5 SSOT documentaire",
        "args": [
            {
                "name": "--query",
                "type": str,
                "required": True,
                "help": "Requête de recherche factuelle",
            },
            {
                "name": "--limit",
                "type": int,
                "default": 5,
                "help": "Nombre maximal de faits à retourner (défaut: 5)",
            },
            {
                "name": "--layer",
                "type": str,
                "default": None,
                "help": "Filtrer par couche SSOT (ex: 01-architecture, 02-business-rules)",
            },
            {
                "name": "--no-synonyms",
                "action": "store_true",
                "help": "Désactiver l'expansion synonymique automatique",
            },
            {
                "name": "--include-superseded",
                "action": "store_true",
                "help": "Inclure les documents obsolètes/remplacés avec pénalité",
            },
        ],
        "no_project": True,
    },
    "dossier-init": {
        "handler": "analysis:handle_dossier_init",
        "help": "Initialise le Dossier de Preuves Documentaires (_fact_dossier.md) pour un récit",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant ou chemin du récit cible (ex: INC-003-BE)",
            },
            {
                "name": "--force",
                "action": "store_true",
                "help": "Écraser si le fichier existe déjà",
            },
        ],
    },
    # ── Verification Leakage Gate (ADR-0354) ────────────────
    "check-leakage": {
        "handler": "gates:handle_check_leakage",
        "help": "Vérifier l'absence de fuites de spécification et assertions tautologiques (ADR-0354)",
        "args": [
            {
                "name": "--file",
                "type": str,
                "help": "Fichier de test spécifique à auditer",
            },
        ],
        "no_project": True,
    },
    # ── Contradiction Engine NLI (ADR-0326 / MLOOP-091-BE) ──
    "nli-audit": {
        "handler": "validation:handle_nli_audit",
        "help": "Audit de non-contradiction sémantique NLI et fuites de tests (ADR-0326 / ADR-0354)",
        "args": [],
        "phase": "validate",
    },

    # ── Visual Review & Annotation (Plannotator ADR-0305 / ADR-0307) ──
    "review": {
        "handler": "plannotator:handle_review",
        "help": "Revue de code visuelle interactive via Plannotator (diff Git local ou PR)",
        "args": [
            {
                "name": "--pr",
                "type": str,
                "help": "URL de Pull Request GitHub/GitLab à réviser",
            },
            {
                "name": "--tailscale",
                "action": "store_true",
                "help": "Partager la session sur le réseau Tailnet HTTPS",
            },
            {
                "name": "--no-local",
                "action": "store_true",
                "help": "Pour revue PR, diff seul sans checkout local",
            },
        ],
        "no_project": True,
    },
    "annotate": {
        "handler": "plannotator:handle_annotate",
        "help": "Annotation visuelle de récits, ADRs, documents ou URLs avec porte de décision",
        "args": [
            {
                "name": "--story",
                "type": str,
                "help": "Identifiant du récit à annoter (ex: US-042)",
            },
            {
                "name": "--adr",
                "type": str,
                "help": "Numéro ou mot-clé de l'ADR à annoter (ex: 0305)",
            },
            {
                "name": "--file",
                "type": str,
                "help": "Chemin vers un fichier local Markdown, HTML ou texte",
            },
            {
                "name": "--url",
                "type": str,
                "help": "URL d'une application web locale ou distante à annoter",
            },
            {
                "name": "--no-gate",
                "action": "store_true",
                "help": "Désactiver le bouton d'approbation (lecture et annotation libre)",
            },
            {
                "name": "--require-approval",
                "action": "store_true",
                "help": "Bloquer l'exécution tant que le réviseur n'approuve pas dans l'UI",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Émettre le résultat de validation structuré en JSON",
            },
            {
                "name": "--result-file",
                "type": str,
                "help": "Chemin où écrire le JSON de décision de manière atomique",
            },
            {
                "name": "--tailscale",
                "action": "store_true",
                "help": "Partager la session d'annotation sur le réseau Tailnet HTTPS",
            },
        ],
        "no_project": True,
    },
    "guide-export": {
        "handler": "plannotator:handle_guide_export",
        "help": "Exporter un guide de revue autonome HTML portable via Plannotator",
        "args": [
            {
                "name": "--snapshot",
                "type": str,
                "help": "Fichier snapshot JSON d'un guide",
            },
            {
                "name": "--id",
                "type": str,
                "help": "Identifiant d'un guide Plannotator existant",
            },
            {
                "name": "--out",
                "type": str,
                "help": "Chemin du fichier HTML de sortie",
            },
        ],
        "no_project": True,
    },
    # ── Moteur Tabulaire & CSV (ADR-0368) ──────────────────
    "csv-normalize": {
        "handler": "tooling:handle_csv_normalize",
        "help": "Normaliser l'encodage (BOM/CP1252) et les séparateurs d'un CSV vers UTF-8 propre",
        "args": [
            {
                "name": "--file",
                "type": str,
                "required": True,
                "help": "Chemin du fichier CSV à normaliser",
            },
            {"name": "--out", "type": str, "help": "Chemin du fichier de sortie normalisé"},
        ],
        "no_project": True,
    },
    "csv-validate": {
        "handler": "tooling:handle_csv_validate",
        "help": "Valider un fichier CSV en flux continu selon un schéma JSON déclaratif",
        "args": [
            {
                "name": "--file",
                "type": str,
                "required": True,
                "help": "Chemin du fichier CSV à valider",
            },
            {
                "name": "--schema",
                "type": str,
                "required": True,
                "help": "Chemin du fichier JSON de schéma",
            },
        ],
        "no_project": True,
    },
    "csv-anonymize": {
        "handler": "tooling:handle_csv_anonymize",
        "help": "Anonymiser déterministement les colonnes PII sensibles et échantillonner",
        "args": [
            {
                "name": "--file",
                "type": str,
                "required": True,
                "help": "Chemin du fichier CSV source",
            },
            {
                "name": "--fields",
                "type": str,
                "required": True,
                "help": "Colonnes sensibles séparées par virgule (ex: 'email,nom')",
            },
            {"name": "--out", "type": str, "help": "Chemin du fichier de sortie anonymisé"},
            {
                "name": "--sample",
                "type": int,
                "help": "Nombre de lignes à échantillonner via Reservoir Sampling",
            },
        ],
        "no_project": True,
    },
    "csv-diff": {
        "handler": "tooling:handle_csv_diff",
        "help": "Comparer deux instantanés de CSV et identifier les deltas sur clé primaire",
        "args": [
            {
                "name": "--old",
                "type": str,
                "required": True,
                "help": "Chemin de l'ancienne version du CSV",
            },
            {
                "name": "--new",
                "type": str,
                "required": True,
                "help": "Chemin de la nouvelle version du CSV",
            },
            {
                "name": "--key",
                "type": str,
                "required": True,
                "help": "Nom de la colonne clé primaire",
            },
        ],
        "no_project": True,
    },
    # ── Résilience Agentique & Point-in-Time Recovery (ADR-0371) ──────────
    "agent-resilience": {
        "handler": "resilience:handle_agent_resilience",
        "help": "Audit de la posture de cyber-résilience agentique (ADR-0371)",
        "args": [
            {
                "name": "--json",
                "action": "store_true",
                "help": "Sortie au format JSON brut",
            },
        ],
    },
    "topology": {
        "handler": "resilience:handle_topology",
        "help": "Cartographie topologique des agents et calcul du Blast Radius (ADR-0371)",
        "args": [
            {
                "name": "--agent",
                "type": str,
                "help": "Rôle spécifique d'agent à analyser (ex: orchestrator, worker, research, qa, crawler, sentinel)",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Sortie au format JSON brut",
            },
        ],
    },
    "rollback": {
        "handler": "resilience:handle_rollback",
        "help": "Restauration déterministe point-in-time de l'état et de la mémoire (ADR-0371)",
        "args": [
            {
                "name": "--step",
                "type": int,
                "help": "Numéro d'étape du checkpoint à restaurer (1 = plus récent)",
            },
            {
                "name": "--target",
                "type": str,
                "help": "Partition de mémoire spécifique à restaurer sélectivement",
            },
        ],
    },
    # ── Dream RSI — Simulateur Replay Hors-Ligne & Auto-Amélioration (ADR-0372) ─
    "dream-rsi": {
        "handler": "dream_rsi:handle_dream_rsi",
        "help": "Exécuter le cycle Dream RSI (simulateur replay hors-ligne & optimisation de politique)",
        "args": [
            {
                "name": "--simulate",
                "action": "store_true",
                "help": "Simuler le cycle d'évaluation sur les traces sans persistance",
            },
            {
                "name": "--apply",
                "action": "store_true",
                "help": "Sauvegarder la méta-politique sélectionnée dans la configuration du harnais (.mloop/dream_policy.json)",
            },
            {
                "name": "--json",
                "action": "store_true",
                "help": "Sortie au format JSON brut",
            },
        ],
    },
}


