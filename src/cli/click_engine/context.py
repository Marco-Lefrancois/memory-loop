"""
Contexte Click & middleware Lifecycle Gates (MLOOP-190-BE / EPIC-19 — ADR-0339).
Symboles : ``MLoopContext`` (CA-1), ``build_context`` (CA-3/CA-5), ``pass_mloop_context``
(CA-2), ``lifecycle_gate_guard`` (CA-4). Interne CLI, aucune route HTTP (ADR-0319).
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, Optional, TypeVar, cast

import click

from src.cli import ZeroFluffConsole
from src.core.lifecycle import ProjectLifecycleManager
from src.utils.lexicon_resolver import SemanticLexiconResolver
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.state import LoopState

logger = get_logger("cli.click_engine.context")

F = TypeVar("F", bound=Callable[..., Any])
PROJECTS_DIR = Path("Projects")

__all__ = ["MLoopContext", "build_context", "lifecycle_gate_guard", "pass_mloop_context"]


class MLoopContext:
    """État d'exécution mLoop dans ``click.Context.obj`` (CA-1) : expose
    ``project_name``, ``project_path``, ``state`` (lazy), ``timing_start``, ``command``.
    """

    def __init__(
        self,
        project_name: Optional[str] = None,
        project_path: Optional[Path] = None,
        command: Optional[str] = None,
        *,
        state: Optional["LoopState"] = None,
        timing_start: Optional[float] = None,
        requires_project: bool = True,
        task_type: Optional[str] = None,
    ) -> None:
        self.project_name = project_name
        self.project_path = project_path
        self.command = command
        self.requires_project = requires_project
        self.task_type = task_type
        self.timing_start = time.time() if timing_start is None else timing_start
        self._state = state

    @property
    def state(self) -> Optional["LoopState"]:
        """LoopState chargé paresseusement au premier accès (CA-1)."""
        if self._state is None and self.project_name:
            self._state = self._load_state()
        return self._state

    @property
    def elapsed_seconds(self) -> float:
        """Durée écoulée depuis ``timing_start`` (traçabilité d'exécution)."""
        return time.time() - self.timing_start

    def _load_state(self) -> "LoopState":
        """Charge LoopState via audit, repli graphe (ADR-0369, aucun except nu)."""
        from src.state import LoopState  # import paresseux (démarrage rapide EPIC-19)

        state = LoopState(project_name=self.project_name or "")
        if self.project_path is not None and self.project_path.exists():
            extra = {"command": self.command, "project": self.project_name, "phase": "context"}
            try:
                state.load_from_audit(self.project_path)
            except Exception:
                logger.debug("Audit state échoué, repli graphe.", exc_info=True, extra=extra)
                try:
                    state.load_from_graph(self.project_path)
                except Exception:
                    logger.debug("Graphe state échoué, état neuf.", exc_info=True, extra=extra)
        state.project_name = self.project_name or ""
        return state


def _list_known_projects() -> list[str]:
    """Projets connus sous ``Projects/`` (parité ``src/commands/router.py``)."""
    if not PROJECTS_DIR.exists():
        return []
    return sorted(
        p.name for p in PROJECTS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def _read_active_project() -> Optional[str]:
    """Projet actif : ``MLOOP_ACTIVE_PROJECT`` puis ``memory/active_project.json``."""
    env_name = os.environ.get("MLOOP_ACTIVE_PROJECT", "").strip()
    if env_name:
        return env_name
    from src.core.layout import ProjectLayout  # import paresseux

    active_json = Path(ProjectLayout.ACTIVE_PROJECT_FILE)
    if not active_json.exists():
        return None
    try:
        with open(active_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        logger.debug(
            "active_project.json illisible.",
            exc_info=True,
            extra={"command": "build_context", "project": None, "phase": "context"},
        )
        return None
    return str(data.get("active_project", "") or "").strip() or None


def _fail_missing_project(command: Optional[str]) -> NoReturn:
    """CA-3 / Pilier 4 : erreur listant ``Projects/``, exit 1, zéro traceback."""
    projs = _list_known_projects()
    detail = f"Projets connus disponibles : {projs}" if projs else "Aucun projet sous Projects/."
    ZeroFluffConsole.error(f"Le paramètre --project est requis pour cette commande. {detail}")
    logger.error(
        "Commande invoquée sans paramètre --project requis.",
        extra={
            "command": command,
            "project": None,
            "phase": "validate",
            "reason": "missing_project",
            "exit_code": 1,
        },
    )
    raise SystemExit(1)


def build_context(
    project: Optional[str],
    command: str,
    *,
    no_project: bool = False,
    task_type: Optional[str] = None,
    create_if_missing: bool = False,
) -> MLoopContext:
    """Construit le ``MLoopContext`` de l'invocation Click (CA-3, CA-5, Pilier 3).

    ``no_project=True`` → exempt ; sinon ``--project`` ou projet actif requis.
    Alias non canoniques résolus via ``SemanticLexiconResolver`` + message info.
    """
    timing_start = time.time()
    if no_project:
        return MLoopContext(
            command=command,
            timing_start=timing_start,
            requires_project=False,
            task_type=task_type,
        )

    raw = (project or "").strip() or _read_active_project() or ""
    if not raw:
        _fail_missing_project(command)

    try:
        canonical = SemanticLexiconResolver.resolve_project_alias(raw)
    except Exception:
        logger.debug(
            "Résolution d'alias indisponible.",
            exc_info=True,
            extra={"command": command, "project": raw, "phase": "context"},
        )
        canonical = None
    if canonical and canonical != raw:
        ZeroFluffConsole.info(f"Alias projet '{raw}' résolu vers le nom canonique '{canonical}'.")
        raw = canonical

    from src.swarm import get_project_context  # import paresseux (anti-cycle)

    try:
        state, project_path = get_project_context(raw, create_if_missing=create_if_missing)
    except ValueError:
        ZeroFluffConsole.error(
            f"Projet '{raw}' introuvable sous Projects/. "
            f"Projets connus disponibles : {_list_known_projects()}"
        )
        logger.error(
            "Résolution de projet échouée.",
            extra={
                "command": command,
                "project": raw,
                "phase": "resolve",
                "reason": "unknown_project",
                "exit_code": 1,
            },
        )
        raise SystemExit(1) from None

    os.environ["MLOOP_ACTIVE_PROJECT"] = state.project_name
    return MLoopContext(
        project_name=state.project_name,
        project_path=project_path,
        command=command,
        state=state,
        timing_start=timing_start,
        requires_project=True,
        task_type=task_type,
    )


def _accepts_mloop_context(annotation: Any) -> bool:
    """Vérifie que l'annotation du 1er paramètre accepte un MLoopContext (CA-2)."""
    if annotation is inspect.Parameter.empty or annotation in (Any, object, MLoopContext):
        return True
    if isinstance(annotation, str):
        return "MLoopContext" in annotation or "Any" in annotation or annotation == "object"
    if isinstance(annotation, type):
        try:
            return issubclass(MLoopContext, annotation)
        except TypeError:
            logger.debug(
                "Annotation non testable via issubclass.",
                exc_info=True,
                extra={"command": None, "project": None, "phase": "context"},
            )
            return True
    return True  # Optional[...], Union[...] et formes composées : acceptées.


def pass_mloop_context(func: F) -> F:
    """Injecte ``ctx.obj`` (``MLoopContext``) en 1er argument du callable (CA-2).

    Usage : ``@group.command()`` puis ``@pass_mloop_context`` puis
    ``def cmd(mctx: MLoopContext) -> None: ...``
    """
    params = list(inspect.signature(func).parameters.values())
    if not params:
        raise TypeError(f"@pass_mloop_context exige un paramètre MLoopContext : {func!r}.")
    if not _accepts_mloop_context(params[0].annotation):
        raise TypeError(
            f"Le 1er paramètre de {func!r} doit être annoté MLoopContext "
            f"(reçu : {params[0].annotation!r})."
        )

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        click_ctx = click.get_current_context()
        obj = click_ctx.obj
        if not isinstance(obj, MLoopContext):
            raise click.ClickException(
                "Contexte mLoop absent : MLoopContext non initialisé dans "
                "click.Context.obj (invoquez via le groupe racine Click)."
            )
        return func(obj, *args, **kwargs)

    return cast(F, wrapper)


def lifecycle_gate_guard(
    ctx: click.Context, cmd_name: str, task_type: Optional[str] = None
) -> bool:
    """Middleware Lifecycle Gates avant dispatch (CA-4 / ADR-0339) : en violation,
    ``ZeroFluffConsole.error("[LIFECYCLE GATE VIOLATION] …")``, journal structuré
    {command, project, phase, reason, exit_code}, exit 1 — handler JAMAIS appelé.
    Retourne True si autorisé (exemptions ``no_project=True`` incluses).
    """
    mctx = ctx.obj if isinstance(ctx.obj, MLoopContext) else None
    if mctx is None:
        raise click.ClickException(
            "Contexte mLoop absent : MLoopContext non initialisé dans click.Context.obj."
        )
    if mctx.project_path is None:
        if mctx.requires_project:
            _fail_missing_project(cmd_name)  # CA-3 : exit 1, zéro traceback
        return True  # CA-5 : commande exemptée de projet

    allowed, reason = ProjectLifecycleManager.can_execute_command(
        mctx.project_path, cmd_name, task_type=task_type or mctx.task_type
    )
    if not allowed:
        ZeroFluffConsole.error(f"[LIFECYCLE GATE VIOLATION] {reason}")
        logger.error(
            "Violation de la porte de cycle de vie (Lifecycle Gate).",
            extra={
                "command": cmd_name,
                "project": mctx.project_name,
                "phase": "lifecycle_gate",
                "reason": reason,
                "exit_code": 1,
            },
        )
        raise SystemExit(1)
    logger.debug(
        "Lifecycle Gate franchie.",
        extra={"command": cmd_name, "project": mctx.project_name, "phase": "lifecycle_gate"},
    )
    return True
