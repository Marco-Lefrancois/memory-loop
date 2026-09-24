"""
Sous-registre déclaratif CLI — Domaine Projet (MLOOP-175-BE).

Commandes : guide, init, resume, focus, vibe-check, gate-approve,
             lifecycle-status, lifecycle-clean, sync-antigravity,
             install-hooks, hook.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

PROJECT_COMMANDS: dict[str, dict] = {
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
}
