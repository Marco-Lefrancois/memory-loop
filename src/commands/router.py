"""
mLoop CLI Router — Dispatch dynamique basé sur le registre déclaratif.

Ce module construit le parser argparse depuis `_registry.COMMANDS`,
résout les handlers par lazy import, et centralise le sys.exit().
"""
import argparse
import importlib
import os
import sys
from pathlib import Path

from src.cli import ZeroFluffConsole
from src.swarm import get_project_context
from src.commands._registry import COMMANDS


def _resolve_handler(handler_ref: str):
    """Résout 'module:function' en callable via lazy import.

    Exemple : 'project:handle_init' → src.commands.handlers.project.handle_init
    """
    module_name, func_name = handler_ref.split(":")
    module = importlib.import_module(f"src.commands.handlers.{module_name}")
    return getattr(module, func_name)


def _build_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI dynamiquement depuis le registre COMMANDS."""
    project_parser = argparse.ArgumentParser(add_help=False)
    project_parser.add_argument("--project", type=str, required=False, help="Nom du projet cible")

    parser = argparse.ArgumentParser(
        description="mLoop State & Validation Backend",
        parents=[project_parser],
    )
    parser.add_argument("--batch", action="store_true", help="Mode d'exécution headless non-interactif")
    parser.add_argument("--resume", action="store_true", help="Reprendre depuis le dernier checkpoint")
    parser.add_argument("--max-turns", type=int, default=10, help="Nombre maximal de tours de boucle")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Pipeline à exécuter")

    # Chargement défensif et résilient du registre sous accès concurrent (L-06 / ADR-0370)
    import src.commands._registry as reg_mod
    cmds = dict(reg_mod.COMMANDS)
    vital_commands = {"gate-approve", "resume", "vibe-check", "sync", "lifecycle-status", "worker-spawn"}
    missing_vital = vital_commands - set(cmds.keys())
    if missing_vital:
        importlib.reload(reg_mod)
        cmds = dict(reg_mod.COMMANDS)

    for cmd_name, cmd_def in sorted(cmds.items()):
        aliases = cmd_def.get("aliases", [])
        sub = subparsers.add_parser(cmd_name, aliases=aliases, parents=[project_parser], help=cmd_def.get("help", ""))
        for arg_def in cmd_def.get("args", []):
            # Extraire le nom positionnel et les kwargs
            kwargs = {k: v for k, v in arg_def.items() if k != "name"}
            sub.add_argument(arg_def["name"], **kwargs)
        sub.set_defaults(_handler_ref=cmd_def["handler"], _no_project=cmd_def.get("no_project", False))

    return parser


def execute_cli() -> None:
    """Point d'entrée principal de la CLI mLoop."""
    ZeroFluffConsole.section("Memory Loop - Framework Backend CLI")

    parser = _build_parser()
    args = parser.parse_args()

    # Commandes sans contexte projet (ex: drawdb)
    if getattr(args, "_no_project", False):
        handler = _resolve_handler(args._handler_ref)
        exit_code = handler(args, None, None)
        sys.exit(exit_code or 0)

    # Validation du projet
    if not args.project:
        ZeroFluffConsole.error("Le paramètre --project est requis pour cette commande.")
        projects_dir = Path("Projects")
        if projects_dir.exists():
            projs = sorted([p.name for p in projects_dir.iterdir() if p.is_dir() and not p.name.startswith(".")])
            if projs:
                ZeroFluffConsole.info(f"Projets connus disponibles : {projs}")
        sys.exit(1)

    # Résolution du contexte projet
    state, project_path = get_project_context(args.project, create_if_missing=(args.command == "init"))
    args.project = state.project_name
    os.environ["MLOOP_ACTIVE_PROJECT"] = state.project_name

    # Contrôle de cycle de vie déterministe (Quality Gate Enforcement - ADR-0339)
    from src.core.lifecycle import ProjectLifecycleManager
    task_type = getattr(args, "task_type", None)
    allowed, reason = ProjectLifecycleManager.can_execute_command(
        project_path, args.command, task_type=task_type
    )
    if not allowed:
        ZeroFluffConsole.error(f"[LIFECYCLE GATE VIOLATION] {reason}")
        sys.exit(1)

    # Dispatch vers le handler résolu
    handler = _resolve_handler(args._handler_ref)
    exit_code = handler(args, state, project_path)
    sys.exit(exit_code or 0)
