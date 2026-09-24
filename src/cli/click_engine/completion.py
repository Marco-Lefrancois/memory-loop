"""
Complétion shell native & installation (MLOOP-192-BE / EPIC-19 — ADR-0202/0369/0370).

Symboles publics : ``complete_projects`` (CA-2 / Pilier 1), ``complete_stories``
(CA-3 / Pilier 2), ``complete_task_types`` (types de mission workers) et la commande
``completion-setup`` via ``run_completion_setup`` (CA-5 / Pilier 4).

Contrat Click 8.5 : un compléteur reçoit ``(ctx, param, incomplete)``, filtre
**lui-même** par préfixe (``Parameter.shell_complete`` n'applique aucun filtre
postérieur — vérifié sur click 8.5.0) et renvoie des ``str`` que Click convertit
automatiquement en ``CompletionItem``. Aucun réseau, aucun subprocess : CA-4 (< 15 ms)
repose sur un unique ``os.scandir()`` par appel (détection Windows préchargée).

Pilier 3 (ADR-0369) : toute exception I/O est journalisée en DEBUG
(``exc_info=True`` + ``extra={...}``) puis convertie en liste vide — jamais de
``except`` nu, jamais de trace affichée dans le shell. Interne CLI, aucune route
HTTP (ADR-0319). Rollback : flag ``MLOOP_CLI_ENGINE``.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path

import click

from src.utils.logger import get_logger

logger = get_logger("cli.click_engine.completion")

PROJECTS_DIR = Path("Projects")

# CA-2 : dossiers cachés ('.' → .git) et archivés/système ('_' → _archive,
# _DEPRECATED) exclus de la complétion des projets.
_EXCLUDED_PREFIXES = (".", "_")

# Parité stricte avec les `choices` de `--task-type` dans
# src/commands/_registry/_reg_workers.py (entrée worker-spawn) — ADR-0370.
TASK_TYPES: tuple[str, ...] = (
    "deepening",
    "validation",
    "deepsearch",
    "build",
    "compaction",
)

# Ids de récits : MLOOP-192-BE, REC-001, US-01-FOOD. Les namespaces non-récits
# référencés dans le sprint_backlog (EPIC-*, ADR-*, RM-*) sont écartés : ce sont
# respectivement des épopées, des décisions d'architecture et des règles métier.
_STORY_ID_RE = re.compile(r"\b[A-Z][A-Z0-9_]{1,15}-\d{1,6}(?:-[A-Z0-9]{1,12})*\b")
_NON_STORY_PREFIXES = ("EPIC-", "ADR-", "RM-")

# Instructions d'activation officielles Click 8.5 (littérales, non reformulées).
SHELL_SOURCES: dict[str, str] = {
    "powershell": "$env:_LOOP_COMPLETE = 'powershell_source'",
    "bash": 'eval "$(_LOOP_COMPLETE=bash_source loop)"',
    "zsh": 'eval "$(_LOOP_COMPLETE=zsh_source loop)"',
}

SHELL_LABELS: dict[str, str] = {
    "powershell": "PowerShell 5.1 / pwsh 7+  (à coller dans votre $PROFILE)",
    "bash": "Bash — Git Bash / WSL / Linux  (à coller dans ~/.bashrc)",
    "zsh": "Zsh  (à coller dans ~/.zshrc)",
}

__all__ = [
    "SHELL_SOURCES",
    "TASK_TYPES",
    "complete_projects",
    "complete_stories",
    "complete_task_types",
    "detect_shell",
    "render_completion_setup",
    "run_completion_setup",
]


def _filter_prefix(candidates: Iterable[str], incomplete: str) -> list[str]:
    """Filtre par préfixe (Click n'filtre pas lui-même) et trie de façon déterministe."""
    prefix = incomplete or ""
    return sorted(name for name in candidates if name.startswith(prefix))


def _scan_names(directory: Path, *, files_only: bool = False) -> list[str]:
    """Scan unique ``os.scandir()`` (CA-4) ; I/O en échec → DEBUG + liste vide (Pilier 3)."""
    try:
        with os.scandir(directory) as entries:
            if files_only:
                names = [entry.name for entry in entries if entry.is_file()]
            else:
                names = [entry.name for entry in entries if entry.is_dir()]
    except OSError:
        # Pilier 3 + ADR-0369 : journal structuré requis avant de dégrader en [].
        logger.debug(
            "Lecture du répertoire impossible, complétion shell dégradée en liste vide.",
            exc_info=True,
            extra={
                "command": "completion",
                "project": None,
                "phase": "shell_complete",
                "directory": str(directory),
            },
        )
        return []
    return names


def complete_projects(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """CA-2 / Pilier 1 : projets éligibles sous ``Projects/`` pour ``--project``.

    Exclut les dossiers système/archivés (``.git``, ``_archive``, ``_DEPRECATED``)
    puis filtre par le préfixe saisi (ex: ``Metro_F`` → ``Metro_FOOD``).
    """
    del ctx, param  # contrat Click : paramètres positionnels non consommés
    names = _scan_names(PROJECTS_DIR)
    eligible = (name for name in names if not name.startswith(_EXCLUDED_PREFIXES))
    return _filter_prefix(eligible, incomplete)


def _project_from_ctx(ctx: click.Context | None) -> str | None:
    """Projet porté par ``--project`` : ``ctx.params`` puis ``ctx.parent.params`` (CA-3).

    **Aucun** repli sur l'environnement (``MLOOP_ACTIVE_PROJECT``) : si ``--project``
    est omis ou invalide, la complétion reste vide — Pilier 2, littéralement.
    """
    if ctx is None:
        return None
    params = getattr(ctx, "params", None) or {}
    name = params.get("project")
    if not name:
        parent = getattr(ctx, "parent", None)
        parent_params = (getattr(parent, "params", None) or {}) if parent else {}
        name = parent_params.get("project")
    if isinstance(name, str):
        name = name.strip()
    return name or None


def _story_ids_from_sprint_backlog(project: str) -> set[str]:
    """Source 2 du récit : ids référencés dans ``backlog/sprint_backlog.md``."""
    path = PROJECTS_DIR / project / "backlog" / "sprint_backlog.md"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        logger.debug(
            "sprint_backlog.md illisible, complétion restreinte à backlog/stories/.",
            exc_info=True,
            extra={
                "command": "completion",
                "project": project,
                "phase": "shell_complete",
            },
        )
        return set()
    return {
        match.group(0)
        for match in _STORY_ID_RE.finditer(text)
        if not match.group(0).startswith(_NON_STORY_PREFIXES)
    }


def complete_stories(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """CA-3 / Pilier 2 : identifiants de récits du projet passé à ``--project``.

    Union de ``backlog/stories/*.md`` (source 1) et des ids référencés dans
    ``sprint_backlog.md`` (source 2). Projet absent/invalide → ``[]`` sans exception.
    """
    del param  # contrat Click : paramètre non consommé (le ctx porte le projet)
    project = _project_from_ctx(ctx)
    if not project:
        return []
    stories_dir = PROJECTS_DIR / project / "backlog" / "stories"
    names = _scan_names(stories_dir, files_only=True)
    ids = {Path(name).stem for name in names if name.endswith(".md")}
    ids |= _story_ids_from_sprint_backlog(project)
    return _filter_prefix(ids, incomplete)


def complete_task_types(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """Types de mission workers autorisés (``--task-type``), filtrés par préfixe."""
    del ctx, param
    return _filter_prefix(TASK_TYPES, incomplete)


def detect_shell() -> str:
    """Shell hôte déterministe, sans subprocess : ``$SHELL`` d'abord, sinon Windows → PowerShell.

    ``$SHELL`` prime sur la présence de ``PSModulePath`` : une session Git Bash
    hérite de ``PSModulePath`` de son parent PowerShell et doit rester « bash ».
    """
    shell_path = (os.environ.get("SHELL") or "").strip().lower()
    if shell_path.endswith("zsh"):
        return "zsh"
    if shell_path.endswith(("bash", "/sh")):
        return "bash"
    if os.name == "nt":
        return "powershell"
    return "bash"


def _profile_candidates() -> list[Path]:
    """Emplacements ``$PROFILE`` connus (best-effort, aucun lancement de processus)."""
    home = Path.home()
    if os.name == "nt":
        return [
            home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
            home / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
        ]
    return [home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"]


def _profile_hint() -> str:
    """``$PROFILE`` existant privilégié ; sinon défaut pwsh 7+ avec alternative 5.1."""
    try:
        candidates = _profile_candidates()
    except (OSError, RuntimeError):
        logger.debug(
            "Détermination de $PROFILE impossible, emplacement non renseigné.",
            exc_info=True,
            extra={
                "command": "completion-setup",
                "project": None,
                "phase": "shell_setup",
            },
        )
        return "(emplacement $PROFILE non déterminable sur ce compte)"
    existing = [str(path) for path in candidates if path.exists()]
    if existing:
        return " ; ".join(existing)
    if os.name == "nt" and len(candidates) == 2:
        return f"{candidates[0]} (pwsh 7+) ou {candidates[1]} (Windows PowerShell 5.1)"
    return str(candidates[0])


def render_completion_setup(shell: str | None = None) -> str:
    """CA-5 / Pilier 4 : instruction exacte du shell détecté + ``$PROFILE`` + alternatives.

    L'ordre des blocs place le shell détecté en tête ; les deux autres restent
    affichés (l'utilisateur bascule facilement d'environnement).
    """
    detected = shell if shell in SHELL_SOURCES else detect_shell()
    order = [detected, *(name for name in SHELL_SOURCES if name != detected)]
    lines = [
        "ACTIVATION DE L'AUTOCOMPLÉTION SHELL MLOOP (Click 8.5+)",
        "",
        f"Shell détecté : {detected}",
        "",
    ]
    for index, name in enumerate(order, start=1):
        lines.append(f"{index}) {SHELL_LABELS[name]} :")
        lines.append(f"   {SHELL_SOURCES[name]}")
        if name == "powershell":
            lines.append(f"   $PROFILE : {_profile_hint()}")
        lines.append("")
    lines.extend(
        [
            "Note moteur (vérifiée empiriquement) : la complétion est servie par le",
            "moteur Click du CLI — ajoutez également à votre profil :",
            "  PowerShell : $env:MLOOP_CLI_ENGINE = 'click'",
            "  Bash / Zsh : export MLOOP_CLI_ENGINE=click",
            "Le moteur argparse (défaut actuel, rollback A3) ignore la variable",
            "_LOOP_COMPLETE : sans ce drapeau, TAB reste muet.",
        ]
    )
    return "\n".join(lines)


def run_completion_setup() -> int:
    """Commande ``completion-setup`` : affiche l'instruction puis sort en 0 (CA-5).

    Sortie en ``print()`` brut (pas de console riche) : les lignes d'activation
    doivent rester copiables telles quelles, sans reflow de largeur de colonne.
    """
    print(render_completion_setup())
    return 0
