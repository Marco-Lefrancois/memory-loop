"""
Sous-registre déclaratif CLI — Domaine Validation & Outillage (MLOOP-175-BE).

Validation : aoep, audit-loop, eval, calibrate, plugin-validate.
Tooling : dashboard, drawdb[1], optimize, svg-optimize, hill-climb, archify,
          drawdb[2].
CSV : csv-normalize, csv-validate, csv-anonymize, csv-diff.

Note doublon : drawdb apparaît deux fois (handlers différents).
Le second (sans --action, avec --no-open) remplace le premier.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

VALIDATE_TOOL_COMMANDS: dict[str, dict] = {
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
    # drawdb redéclaré (second = dernier gagne, comportement dict Python)
    "drawdb": {  # noqa: F601
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
}
