"""
Sous-registre déclaratif CLI — Domaine Herdr Workers (MLOOP-175-BE).

Herdr Runtime (ADR-0029 / ADR-0205) : worker-spawn, worker-status,
    worker-harvest, worker-close, worker-reap, worker-handoff-test,
    worker-legacy-mine, worker-shadow-estimate, worker-visual-dissect,
    worker-janitor-watch.

Contraintes : ADR-0202 (≤300L/15Ko), ADR-0369 (zéro import circulaire).
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
WORKER_KIND_HELP: str = _worker_runtime_kinds()

WORKERS_COMMANDS: dict[str, dict] = {
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
                "help": "Modèle LiteLLM (ex: nmedia_cloud/claude-opus-4.8)",
            },
            {
                "name": "--task-type",
                "type": str,
                "default": None,
                "choices": ["deepening", "validation", "deepsearch", "build", "compaction"],
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
                "help": "Identifiant du récit pour inspection ciblée via PTY",
            },
        ],
    },
    "worker-harvest": {
        "handler": "worker:handle_worker_harvest",
        "help": "Moissonner les preuves d'exécution PTY du worker et mettre à jour l'EvidencePack",
        "args": [
            {"name": "--story", "type": str, "required": True, "help": "Identifiant du récit"},
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
                "help": "Délai d'inactivité en secondes",
            },
            {
                "name": "--force",
                "action": "store_true",
                "help": "Forcer la fermeture des volets sans confirmation",
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
            {"name": "--domain", "type": str, "default": None, "help": "Nom de domaine métier"},
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
}
