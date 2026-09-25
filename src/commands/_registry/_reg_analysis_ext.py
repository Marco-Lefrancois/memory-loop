"""
Sous-registre déclaratif CLI — Domaine Analyse Étendue (MLOOP-175-BE).

Commandes : story-clean[1], rubber-duck, multi-draft, memo-search, blast,
             chunk, agentic-extract, eval-harvest, context-watch, token-tracker,
             supersession-sync, distill-invest, parent-resolve, story-clean[2],
             extract.

Note doublons : story-clean apparaît deux fois dans le registre original.
Le second (avec --verbose) remplace le premier (comportement Python dict).

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

ANALYSIS_EXT_COMMANDS: dict[str, dict] = {
    # ── Analyse Étendue ────────────────────────────────────
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
    # story-clean redéclaré ici (second = dernier gagne, comportement dict Python)
    "story-clean": {  # noqa: F601
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
                "help": "Lister les templates d'extraction déclaratifs disponibles",
            },
        ],
    },
    # ── Verrou Anti-Promotion (MLOOP-270-BE / ADR-011) ─────
    "story-approve": {
        "handler": "story_approve:handle_story_approve",
        "help": "Approbation humaine d'un récit : stamps validated_by/validated_at + entrée journal atomique (MLOOP-270-BE)",
        "args": [
            {
                "name": "--story",
                "type": str,
                "required": True,
                "help": "Identifiant du récit (ex: MLOOP-270-BE)",
            },
            {
                "name": "--approver",
                "type": str,
                "default": None,
                "help": 'Nom de l\'approbateur humain (ex: "Marco") — identifiants machine refusés',
            },
        ],
    },
    "story-backfill": {
        "handler": "story_backfill:handle_story_backfill",
        "help": "Rétro-équiper le journal des transitions (origin: backfill) + stamps récits actifs — CA-5 : sans approbateur = zéro écriture (MLOOP-270-BE)",
        "args": [
            {
                "name": "--approver",
                "type": str,
                "default": None,
                "help": 'Nom de l\'approbateur humain (ex: "Marco") — obligatoire pour toute écriture',
            },
        ],
    },
}
