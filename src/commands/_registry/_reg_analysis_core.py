"""
Sous-registre déclaratif CLI — Domaine Analyse Core (MLOOP-175-BE).

Commandes : sync, wikifix, export-obsidian, hyper-query, dream[analysis],
             drill, confidence, struct-check, code-check, code-tournament,
             tdd-enforce, validate-sprint.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

ANALYSIS_CORE_COMMANDS: dict[str, dict] = {
    # ── Analyse Core ───────────────────────────────────────
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
    "rollover-archive": {
        "handler": "analysis_sync:handle_rollover_archive",
        "help": "Archivage automatique des épopées scellées vers backlog/archive/ (ADR-0391)",
        "args": [
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Simulation sans déplacement de fichiers",
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
}
