"""
Sous-registre déclaratif CLI — Domaine Hygiène & Rétention des Données (MLOOP-230-BE à MLOOP-234-FULL / ADR-015).

Commandes : memory (health, vacuum), logs (rotate), crawler (prune), scratch (prune).
Contraintes : ADR-0202 (<=300L/15Ko), ADR-0369.
"""

DATA_HYGIENE_COMMANDS: dict[str, dict] = {
    # ── Moteur de Maintenance & Défragmentation SQLite (MLOOP-230-BE) ──
    "memory": {
        "handler": "memory_maintenance:handle_memory",
        "no_project": True,
        "help": "Maintenance et défragmentation SQLite (health, vacuum)",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "health",
                "choices": ["health", "vacuum"],
                "help": "Action de maintenance : health, vacuum (défaut: health)",
            },
            {
                "name": "--force",
                "action": "store_true",
                "help": "Forcer le compactage VACUUM même si la fragmentation est inférieure à 15%",
            },
        ],
    },
    # ── Middleware de Rotation & Archivage Rotatif des Journaux (MLOOP-231-BE) ──
    "logs": {
        "handler": "log_rotation:handle_logs",
        "no_project": True,
        "help": "Rotation et archivage rotatif des journaux (rotate)",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "rotate",
                "choices": ["rotate"],
                "help": "Action de journalisation : rotate (défaut: rotate)",
            },
            {
                "name": "--force",
                "action": "store_true",
                "help": "Forcer la rotation des journaux même si la taille est inférieure à 5 Mo",
            },
        ],
    },
    # ── Gestionnaire de Cycle de Vie & TTL du Cache Crawler (MLOOP-232-BE) ──
    "crawler": {
        "handler": "crawler_prune:handle_crawler",
        "no_project": True,
        "help": "Gestion du cycle de vie et élagage du cache crawler (prune)",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "prune",
                "choices": ["prune"],
                "help": "Action crawler : prune (défaut: prune)",
            },
            {
                "name": "--ttl-days",
                "type": int,
                "default": 60,
                "help": "Durée de rétention maximale en jours pour les pages en cache (défaut: 60)",
            },
            {
                "name": "--dry-run",
                "action": "store_true",
                "help": "Simuler l'élagage sans supprimer physiquement les fichiers",
            },
        ],
    },
    # ── Nettoyage Automatique & Rétention des Artefacts de Session (MLOOP-233-BE) ──
    "scratch": {
        "handler": "scratch_prune:handle_scratch",
        "no_project": True,
        "help": "Nettoyage des résidus temporaires scratch et checkpoints (prune)",
        "args": [
            {
                "name": "action",
                "type": str,
                "nargs": "?",
                "default": "prune",
                "choices": ["prune"],
                "help": "Action scratch : prune (défaut: prune)",
            },
            {
                "name": "--older-than-hours",
                "type": int,
                "default": 48,
                "help": "Âge minimal en heures des fichiers temporaires à supprimer (défaut: 48)",
            },
            {
                "name": "--all",
                "action": "store_true",
                "help": "Purger tous les artefacts scratch et tmp indépendamment de leur âge",
            },
        ],
    },
}

