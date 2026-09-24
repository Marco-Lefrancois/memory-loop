"""
Sous-registre déclaratif CLI — Domaine Écosystème Tooling & Runtimes (MLOOP-220-BE, MLOOP-221-BE, MLOOP-222-BE / ADR-014).

Commandes : opencode, plannotator, wayfinder.
Contraintes : ADR-0202 (<=300L/15Ko), ADR-0369.
"""

TOOLING_ECOSYSTEM_COMMANDS: dict[str, dict] = {
    # ── OpenCode CLI Runtime (MLOOP-220-BE) ────────────────
    "opencode": {
        "handler": "opencode:handle_opencode",
        "help": "Pilotage souverain du runtime OpenCode CLI (init, run, status)",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "status",
                "choices": ["init", "run", "status"],
                "help": "Sous-commande OpenCode : init, run, status (défaut: status)",
            },
            {
                "name": "--prompt",
                "type": str,
                "default": None,
                "help": "Consigne initiale transmise à OpenCode",
            },
            {
                "name": "--headless",
                "action": "store_true",
                "help": "Exécution non-interactive d'OpenCode",
            },
        ],
    },
    # ── Plannotator Visual Review & Approval (MLOOP-221-BE) ──
    "plannotator": {
        "handler": "plannotator:handle_plannotator",
        "help": "Harnais d'orchestration visuelle et d'approbation Plannotator (open, approve, status)",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "open",
                "choices": ["open", "approve", "status"],
                "help": "Action Plannotator : open, approve, status (défaut: open)",
            },
            {
                "name": "--story",
                "type": str,
                "default": None,
                "help": "Identifiant du récit utilisateur",
            },
            {
                "name": "--file",
                "type": str,
                "default": None,
                "help": "Chemin explicite vers un fichier de plan",
            },
            {
                "name": "--approve",
                "action": "store_true",
                "help": "Validation headless déterministe pour environnement automatisé CI/CD",
            },
        ],
    },
    # ── Wayfinder Decision Pipeline (MLOOP-222-BE) ─────────
    "wayfinder": {
        "handler": "architecture:handle_wayfinder",
        "help": "Pipeline décisionnel Wayfinder : initialiser la carte, afficher la frontière ou résoudre un ticket",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "frontier",
                "choices": ["init-map", "frontier", "resolve", "status"],
                "help": "Action Wayfinder : init-map, frontier, resolve (défaut: frontier)",
            },
            {
                "name": "--title",
                "type": str,
                "default": None,
                "help": "Titre de l'initiative",
            },
            {
                "name": "--goal",
                "type": str,
                "default": None,
                "help": "Objectif stratégique de l'initiative",
            },
            {
                "name": "--ticket",
                "type": str,
                "default": None,
                "help": "Identifiant du ticket de décision à résoudre (ex: T-01)",
            },
            {
                "name": "--decision",
                "type": str,
                "default": None,
                "help": "Arbitrage consigné pour clore le ticket",
            },
        ],
    },
}
