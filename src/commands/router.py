"""
mLoop CLI Router — Dispatch dynamique basé sur le registre déclaratif.

Ce module construit le parser argparse depuis `_registry.COMMANDS`,
résout les handlers par lazy import, et centralise le sys.exit().
"""

import argparse
import importlib
import os
import sys
import time
from pathlib import Path

from src.cli import ZeroFluffConsole
from src.swarm import get_project_context
from src.commands._registry import COMMANDS
from src.utils.logger import get_logger

logger = get_logger("cli.router")


def _resolve_handler(handler_ref: str):
    """Résout 'module:function' en callable via lazy import.

    Exemple : 'project:handle_init' → src.commands.handlers.project.handle_init
    """
    try:
        module_name, func_name = handler_ref.split(":")
        module = importlib.import_module(f"src.commands.handlers.{module_name}")
        return getattr(module, func_name)
    except (ValueError, ImportError, AttributeError):
        logger.error(
            "Résolution du handler CLI échouée.",
            extra={
                "command": "_resolve_handler",
                "project": os.environ.get("MLOOP_ACTIVE_PROJECT"),
                "phase": "dispatch",
                "handler_ref": handler_ref,
            },
            exc_info=True,
        )
        raise


def _build_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI dynamiquement depuis le registre COMMANDS."""
    project_parser = argparse.ArgumentParser(add_help=False)
    project_parser.add_argument("--project", type=str, required=False, help="Nom du projet cible")

    parser = argparse.ArgumentParser(
        description="mLoop State & Validation Backend",
        parents=[project_parser],
    )
    parser.add_argument(
        "--batch", action="store_true", help="Mode d'exécution headless non-interactif"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Reprendre depuis le dernier checkpoint"
    )
    parser.add_argument(
        "--max-turns", type=int, default=10, help="Nombre maximal de tours de boucle"
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Pipeline à exécuter")

    # Chargement défensif et résilient du registre sous accès concurrent (L-06 / ADR-0370)
    import src.commands._registry as reg_mod

    cmds = dict(reg_mod.COMMANDS)
    vital_commands = {
        "gate-approve",
        "resume",
        "vibe-check",
        "sync",
        "lifecycle-status",
        "worker-spawn",
    }
    missing_vital = vital_commands - set(cmds.keys())
    if missing_vital:
        importlib.reload(reg_mod)
        cmds = dict(reg_mod.COMMANDS)

    for cmd_name, cmd_def in sorted(cmds.items()):
        try:
            aliases = cmd_def.get("aliases", [])
            sub = subparsers.add_parser(
                cmd_name, aliases=aliases, parents=[project_parser], help=cmd_def.get("help", "")
            )
            for arg_def in cmd_def.get("args", []):
                # Extraire le nom positionnel et les kwargs
                kwargs = {k: v for k, v in arg_def.items() if k != "name"}
                sub.add_argument(arg_def["name"], **kwargs)
            sub.set_defaults(
                _handler_ref=cmd_def["handler"], _no_project=cmd_def.get("no_project", False)
            )
        except (KeyError, argparse.ArgumentError) as e:
            logger.error(
                "Construction du sous-parser CLI échouée pour une commande du registre.",
                extra={
                    "command": "_build_parser",
                    "project": os.environ.get("MLOOP_ACTIVE_PROJECT"),
                    "phase": "parse",
                    "failed_command": cmd_name,
                },
                exc_info=True,
            )
            raise RuntimeError(f"Registre CLI corrompu pour la commande '{cmd_name}': {e}") from e

    return parser


def _run_cli() -> int:
    """Corps d'exécution de la CLI mLoop. Retourne le code de sortie."""
    parser = _build_parser()
    args = parser.parse_args()

    # Contexte de traçabilité extrait au plus tôt.
    command = getattr(args, "command", None)
    project = getattr(args, "project", None)
    story_id = getattr(args, "story", None) or getattr(args, "story_id", None)

    # Commandes sans contexte projet (ex: drawdb)
    if getattr(args, "_no_project", False):
        handler = _resolve_handler(args._handler_ref)
        exit_code = handler(args, None, None)
        return exit_code or 0

    # Validation du projet
    if not args.project:
        ZeroFluffConsole.error("Le paramètre --project est requis pour cette commande.")
        logger.error(
            "Commande invoquée sans paramètre --project requis.",
            extra={
                "command": command,
                "project": None,
                "phase": "validate",
                "story_id": story_id,
                "exit_code": 1,
            },
        )
        projects_dir = Path("Projects")
        if projects_dir.exists():
            projs = sorted(
                [
                    p.name
                    for p in projects_dir.iterdir()
                    if p.is_dir() and not p.name.startswith(".")
                ]
            )
            if projs:
                ZeroFluffConsole.info(f"Projets connus disponibles : {projs}")
        return 1

    # Résolution du contexte projet
    state, project_path = get_project_context(
        args.project, create_if_missing=(args.command == "init")
    )
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
        logger.error(
            "Violation de la porte de cycle de vie (Lifecycle Gate).",
            extra={
                "command": command,
                "project": state.project_name,
                "phase": "lifecycle_gate",
                "story_id": story_id,
                "reason": reason,
                "exit_code": 1,
            },
        )
        return 1

    # Dispatch vers le handler résolu
    handler = _resolve_handler(args._handler_ref)
    exit_code = handler(args, state, project_path)
    return exit_code or 0


def execute_cli() -> None:
    """Point d'entrée principal de la CLI mLoop.

    Instrumente l'exécution complète (ADR-0369) : trace INFO du cycle de vie
    (commande, projet, durée, exit_code) dans mloop.log et capture ERROR de
    toute exception non gérée dans errors.log avec contexte structuré.
    """
    ZeroFluffConsole.section("Memory Loop - Framework Backend CLI")

    # Tentative d'extraction précoce de la commande pour le contexte de log
    # (best-effort : argparse peut sortir avant si arguments invalides).
    command = None
    project = os.environ.get("MLOOP_ACTIVE_PROJECT")
    for _arg in sys.argv[1:]:
        if not _arg.startswith("-"):
            command = _arg
            break

    start_time = time.perf_counter()
    exit_code = 0
    try:
        logger.info(
            "Démarrage de l'exécution CLI.",
            extra={
                "command": command,
                "project": project,
                "phase": "run",
                "story_id": None,
            },
        )
        exit_code = _run_cli()
    except SystemExit as se:
        # argparse et les gardes internes lèvent SystemExit ; propager le code réel.
        exit_code = se.code if isinstance(se.code, int) else (0 if se.code is None else 1)
        raise
    except Exception:
        exit_code = 1
        logger.error(
            "Exception non gérée durant l'exécution CLI.",
            extra={
                "command": command,
                "project": os.environ.get("MLOOP_ACTIVE_PROJECT", project),
                "phase": "run",
                "story_id": None,
                "exit_code": 1,
            },
            exc_info=True,
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_level = logger.info if (isinstance(exit_code, int) and exit_code == 0) else logger.error
        log_level(
            "Fin de l'exécution CLI.",
            extra={
                "command": command,
                "project": os.environ.get("MLOOP_ACTIVE_PROJECT", project),
                "phase": "run",
                "duration_ms": duration_ms,
                "exit_code": exit_code,
            },
        )
    sys.exit(exit_code)
