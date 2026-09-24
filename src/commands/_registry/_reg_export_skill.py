"""
Sous-registre déclaratif CLI — Domaine Export & Skill Registry (MLOOP-175-BE).

Export : jira_sync, jira-read, plugin-export, cycle-status, self-dev,
         unlearn, canvas.
Skill Registry (SEP-2640) : skill-list, skill-invoke, skill-doctor,
                              doctor, agent-probe.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
"""

EXPORT_SKILL_COMMANDS: dict[str, dict] = {
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
}
