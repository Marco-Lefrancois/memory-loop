"""
Routeur CLI Click lazy-loading (MLOOP-191-BE / EPIC-19 — ADR-0202/0369/0370).

Symboles : ``MLoopMultiCommand`` (CA-1/CA-2, sous-classe ``click.MultiCommand``),
``ArgsShim`` (CA-3, passerelle ``argparse.Namespace``), ``cli`` (groupe racine).
Les handlers ne sont importés qu'à l'exécution de la commande ciblée (CA-2) ;
le contrat historique ``handler(args, state, project_path)`` est préservé (CA-4).
Interne CLI, aucune route HTTP (ADR-0319). Rollback : flag ``MLOOP_CLI_ENGINE``.
"""

from __future__ import annotations

import argparse
import difflib
from typing import Any, Optional, cast

import click

from src.cli.click_engine.completion import complete_projects, complete_stories
from src.cli.click_engine.context import (
    MLoopContext,
    build_context,
    lifecycle_gate_guard,
)
from src.cli.click_engine.formatter import install_phase_help  # MLOOP-193-BE
from src.commands._registry import COMMANDS
from src.utils.logger import get_logger

logger = get_logger("cli.click_engine.router")

# click.MultiCommand : alias public Click 8.5 (deprec. → Group en 9.0) ; le
# sous-classement passe par cette binding pour rester littéralement conforme
# au récit MLOOP-191-BE tout en satisfaisant l'analyse statique.
_MULTI_COMMAND_BASE = cast(type, click.MultiCommand)


class _NoSuchCommandFallback(click.UsageError):
    """Fallback si NoSuchCommand absent de click.exceptions (ex: Click < 8.5)."""

    def __init__(
        self,
        command_name: str,
        possibilities: Optional[list[str]] = None,
        ctx: Optional[click.Context] = None,
    ) -> None:
        super().__init__(f"No such command '{command_name}'.", ctx=ctx)
        self.command_name = command_name
        self.possibilities = possibilities

    def format_message(self) -> str:
        if not self.possibilities:
            return self.message
        matches = difflib.get_close_matches(self.command_name, self.possibilities, n=3, cutoff=0.5)
        if not matches:
            return self.message
        match_str = ", ".join(sorted(matches))
        return f"{self.message} Did you mean {match_str}?"


# NoSuchCommand : exporté à l'exécution Click 8.5, replié sur fallback robuste
NoSuchCommand = getattr(click.exceptions, "NoSuchCommand", _NoSuchCommandFallback)

__all__ = ["ArgsShim", "MLoopMultiCommand", "cli"]


def _canonical(cmd_name: str) -> Optional[str]:
    """Nom canonique : id direct ou alias officiel du registre → id (sinon None)."""
    if cmd_name in COMMANDS:
        return cmd_name
    for canonical, definition in COMMANDS.items():
        if cmd_name in (definition.get("aliases") or ()):
            return canonical
    return None


def _click_params(cmd_def: dict) -> list[click.Parameter]:
    """Paramètres Click (options/args) d'une commande + ``--project`` (parité argparse)."""
    params: list[click.Parameter] = [
        click.Option(
            ["--project"],
            default=None,
            shell_complete=complete_projects,
            help="Nom du projet cible",
        ),
    ]
    for arg_def in cmd_def.get("args") or ():
        name, help_ = arg_def["name"], arg_def.get("help")
        if not name.startswith("-"):
            c_type = (
                click.Choice([str(c) for c in arg_def["choices"]])
                if arg_def.get("choices")
                else arg_def.get("type")
            )
            d_val = arg_def.get("default")
            req = (
                False
                if (d_val is not None or arg_def.get("nargs") == "?")
                else bool(arg_def.get("required", True))
            )
            params.append(click.Argument([name], type=c_type, default=d_val, required=req))
            continue
        if arg_def.get("action") == "store_true":
            opt = click.Option(
                [name],
                is_flag=True,
                default=bool(arg_def.get("default", False)),
                help=help_,
            )
        elif arg_def.get("nargs") == "*":
            opt = click.Option([name], multiple=True, default=(), help=help_)
        else:
            kwargs: dict[str, Any] = {"help": help_} if help_ is not None else {}
            if name == "--story":
                kwargs["shell_complete"] = complete_stories
            if arg_def.get("type") in (int, float):
                kwargs["type"] = arg_def["type"]
            if arg_def.get("choices"):
                kwargs["type"] = click.Choice([str(c) for c in arg_def["choices"]])
            if arg_def.get("default") is not None:
                kwargs["default"] = arg_def["default"]
            if arg_def.get("required"):
                kwargs["required"] = True
            opt = click.Option([name], **kwargs)
        if arg_def.get("dest"):
            opt.name = arg_def["dest"]
        params.append(opt)
    return params


class ArgsShim(argparse.Namespace):
    """Adaptateur Click → Namespace argparse (CA-3) : les handlers historiques
    consomment ``args.<param>`` sans altération (CA-4, contrat à 3 positions)."""

    @classmethod
    def from_click(cls, params: dict[str, Any], *, project: Optional[str]) -> "ArgsShim":
        shim = cls()
        for key, value in params.items():
            setattr(shim, key, list(value) if isinstance(value, tuple) else value)
        shim.project = project
        return shim


def _dispatch(
    canonical: str,
    raw_name: str,
    handler_ref: str,
    no_project: bool,
    params: dict[str, Any],
) -> int:
    """Exécute le handler résolu paresseusement avec le triplet historique."""
    root = click.get_current_context().find_root()
    mctx = root.obj
    if not isinstance(mctx, MLoopContext):
        raise click.ClickException(
            "Contexte mLoop absent : MLoopContext non initialisé dans click.Context.obj."
        )
    root_params = dict(root.params or {})
    merged = dict(params)
    for key in ("batch", "resume", "max_turns"):
        merged.setdefault(key, root_params.get(key))
    project = mctx.project_name or merged.get("project") or root_params.get("project")
    shim = ArgsShim.from_click(merged, project=project)
    shim.command = raw_name
    shim._handler_ref = handler_ref
    shim._no_project = no_project
    from src.commands.router import _resolve_handler  # import paresseux (CA-2)

    handler = _resolve_handler(handler_ref)
    logger.debug(
        "Dispatch de commande via le routeur Click.",
        extra={
            "command": raw_name,
            "project": project,
            "phase": "dispatch",
            "handler_ref": handler_ref,
        },
    )
    result = handler(shim, mctx.state, mctx.project_path)
    return result or 0


class MLoopMultiCommand(_MULTI_COMMAND_BASE):  # click.MultiCommand (public 8.5 → Group 9.0)
    """Routeur racine lazy (CA-1/CA-2) : surfaces ids+alias sans import handler,
    résolution paresseuse à l'exécution, did-you-mean sur commande inconnue."""

    _sub_params: dict = {}  # params autoritatifs de la sous-commande (Design C)

    def list_commands(self, ctx: click.Context) -> list[str]:
        names: set[str] = set()
        for name, definition in COMMANDS.items():
            names.add(name)
            names.update(definition.get("aliases") or ())
        return sorted(names)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        canonical = _canonical(cmd_name)
        if canonical is None:
            return None  # inconnue → NoSuchCommand géré par resolve_command
        cmd_def = COMMANDS[canonical]
        handler_ref = cmd_def["handler"]
        no_project = bool(cmd_def.get("no_project"))

        def _callback(**kwargs: Any) -> int:
            return _dispatch(canonical, cmd_name, handler_ref, no_project, kwargs)

        return click.Command(
            name=cmd_name,
            callback=_callback,
            params=_click_params(cmd_def),
            help=cmd_def.get("help", ""),
        )

    def resolve_command(self, ctx: click.Context, args: list):
        try:
            return super().resolve_command(ctx, args)
        except (NoSuchCommand, click.UsageError) as exc:  # type: ignore[misc]
            cmd_name = getattr(exc, "command_name", str(args[0]) if args else "")
            # self.commands est vide (lazy) : re-lever avec la surface ids+alias
            # pour activer difflib « did you mean » (Pilier 2, exit 2).
            raise NoSuchCommand(  # type: ignore[misc]
                cmd_name, possibilities=self.list_commands(ctx), ctx=ctx
            ) from None

    def invoke(self, ctx: click.Context) -> Any:
        """Fork de ``Group.invoke`` (click 8.5) — Design C : parse de la
        sous-commande AVANT le callback groupe → ``build_context``/gate
        consomment les params autoritatifs, à parité du flux argparse
        (parse → résolution projet → gate → dispatch)."""
        if not ctx._protected_args:
            if self.invoke_without_command:
                with ctx:
                    return click.Command.invoke(self, ctx)
            ctx.fail("Missing command.")
        args = [*ctx._protected_args, *ctx.args]
        ctx.args = []
        ctx._protected_args = []
        if self.chain:
            raise click.UsageError("MLoopMultiCommand n'autorise pas chain=True.")
        with ctx:
            cmd_name, cmd, rest = self.resolve_command(ctx, args)
            assert cmd is not None
            ctx.invoked_subcommand = cmd_name
            sub_ctx = cmd.make_context(cmd_name, rest, parent=ctx)  # 1. parse
            self._sub_params = dict(sub_ctx.params)
            click.Command.invoke(self, ctx)  # 2. callback groupe : contexte + gate
            sub_ctx.obj = ctx.obj  # obj hérité à la création = None ici
            with sub_ctx:  # 3. dispatch handler
                return sub_ctx.command.invoke(sub_ctx)


@click.group(cls=MLoopMultiCommand, help="mLoop State & Validation Backend")
@click.option(
    "--project", default=None, shell_complete=complete_projects, help="Nom du projet cible"
)
@click.option("--batch", is_flag=True, help="Mode d'exécution headless non-interactif")
@click.option("--resume", is_flag=True, help="Reprendre depuis le dernier checkpoint")
@click.option("--max-turns", type=int, default=10, help="Nombre maximal de tours de boucle")
def cli(
    project: Optional[str] = None,
    batch: bool = False,
    resume: bool = False,
    max_turns: int = 10,
) -> None:
    """Callback groupe : construit ``MLoopContext`` puis franchit la Lifecycle Gate
    avant tout dispatch handler (parité ``_run_cli`` legacy)."""
    gctx = click.get_current_context()
    grp = gctx.command
    assert isinstance(grp, MLoopMultiCommand)
    sub_params = dict(grp._sub_params)
    cmd_name = gctx.invoked_subcommand or ""
    canonical = _canonical(cmd_name) or cmd_name
    cmd_def = COMMANDS.get(canonical) or {}
    mctx = build_context(
        sub_params.get("project") or project,
        cmd_name,
        no_project=bool(cmd_def.get("no_project")),
        task_type=sub_params.get("task_type"),
        create_if_missing=(cmd_name == "init"),
    )
    gctx.obj = mctx
    lifecycle_gate_guard(gctx, cmd_name)


# MLOOP-193-BE : aide structurée par phases souveraines (SSOT CLI_PIPELINE_GUIDE).
install_phase_help(MLoopMultiCommand)
