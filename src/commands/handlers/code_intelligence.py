"""
Handlers Code Intelligence : Integration de CodeGraph dans le framework mLoop (ADR-0204 et ADR-0363).
Fournit une passerelle deterministe pour l'exploration AST, l'analyse d'impact et les tests affectes
avec support autonome de projet (no_project: True), cache memoire et Token Budget Guardrail (--compact).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole
from src.commands.handlers._codegraph_common import (
    _CG_ABSENT,
    _CODEGRAPH_CACHE,
    _compact_explore_output,
    _find_target_source_path,
    _get_codegraph_binary,
    _log_err,
    _run_codegraph_command,
)

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_code_init(
    args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None
) -> int:
    """Initialise l'indexation CodeGraph sur le code source d'un projet."""
    if not _get_codegraph_binary():
        _log_err("code-init", _CG_ABSENT, args)
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1(
        "CodeGraph Init", f"Initialisation du graphe de code sur : {target_dir}"
    )

    try:
        res = _run_codegraph_command(["init", str(target_dir)])
        if res.returncode == 0:
            print(res.stdout)
            ZeroFluffConsole.success(f"Index CodeGraph initialise avec succes sur {target_dir}")
            return 0
        else:
            _log_err(
                "code-init",
                f"Echec de codegraph init : {res.stderr or res.stdout}",
                args,
                target_keys=str(target_dir),
            )
            return res.returncode
    except Exception as e:
        _log_err(
            "code-init",
            f"Erreur lors de l'execution de codegraph init : {e}",
            args,
            target_keys=str(target_dir),
            exc_info=True,
        )
        return 1


def handle_code_explore(
    args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None
) -> int:
    """Explore le code source physique via CodeGraph (AST, symboles verbatim, chemins d'appels)."""
    if not _get_codegraph_binary():
        _log_err("code-explore", _CG_ABSENT, args)
        return 1

    query = getattr(args, "query", "").strip()
    if not query:
        _log_err(
            "code-explore", "L'argument --query est obligatoire pour l'exploration de code.", args
        )
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    compact = getattr(args, "compact", False)
    cache_key = f"explore:{target_dir}:{query}:{compact}"

    if cache_key in _CODEGRAPH_CACHE:
        print(_CODEGRAPH_CACHE[cache_key])
        return 0

    ZeroFluffConsole.step_s1(
        "CodeGraph Explore",
        f"Recherche de '{query}' dans {target_dir}{' (Mode Compact)' if compact else ''}",
    )

    try:
        res = _run_codegraph_command(["explore", "-p", str(target_dir), str(query)])
        if res.returncode == 0:
            out = res.stdout
            if compact:
                out = _compact_explore_output(out)
            _CODEGRAPH_CACHE[cache_key] = out
            print(out)
            return 0
        else:
            _log_err(
                "code-explore",
                f"Erreur codegraph explore : {res.stderr or res.stdout}",
                args,
                target_keys=query,
            )
            return res.returncode
    except Exception as e:
        _log_err(
            "code-explore",
            f"Erreur d'execution : {e}",
            args,
            target_keys=query,
            exc_info=True,
        )
        return 1


def handle_code_impact(
    args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None
) -> int:
    """Calcule le rayon d'impact (Blast Radius) d'un symbole dans la base de code."""
    if not _get_codegraph_binary():
        _log_err("code-impact", _CG_ABSENT, args)
        return 1

    symbol = getattr(args, "symbol", "").strip()
    if not symbol:
        _log_err("code-impact", "L'argument --symbol est obligatoire.", args)
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    cache_key = f"impact:{target_dir}:{symbol}"

    if cache_key in _CODEGRAPH_CACHE:
        print(_CODEGRAPH_CACHE[cache_key])
        return 0

    ZeroFluffConsole.step_s1(
        "CodeGraph Impact", f"Calcul de l'impact pour '{symbol}' dans {target_dir}"
    )

    try:
        res = _run_codegraph_command(["impact", str(symbol)], cwd=target_dir)
        if res.returncode == 0:
            _CODEGRAPH_CACHE[cache_key] = res.stdout
            print(res.stdout)
            return 0
        else:
            _log_err(
                "code-impact",
                f"Erreur codegraph impact : {res.stderr or res.stdout}",
                args,
                target_keys=symbol,
            )
            return res.returncode
    except Exception as e:
        _log_err(
            "code-impact",
            f"Erreur d'execution : {e}",
            args,
            target_keys=symbol,
            exc_info=True,
        )
        return 1


def handle_code_affected(
    args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None
) -> int:
    """Identifie les tests affectes par les changements de code source."""
    if not _get_codegraph_binary():
        _log_err("code-affected", _CG_ABSENT, args)
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    cmd_args = ["affected"]

    files = getattr(args, "files", None)
    if files:
        cmd_args.extend(files)

    try:
        res = _run_codegraph_command(cmd_args, cwd=target_dir)
        if res.returncode == 0:
            print(res.stdout)
            return 0
        else:
            _log_err(
                "code-affected",
                f"Erreur codegraph affected : {res.stderr or res.stdout}",
                args,
                target_keys=",".join(files) if files else None,
            )
            return res.returncode
    except Exception as e:
        _log_err(
            "code-affected",
            f"Erreur d'execution : {e}",
            args,
            target_keys=",".join(files) if files else None,
            exc_info=True,
        )
        return 1


def handle_code_status(
    args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None
) -> int:
    """Affiche les statistiques de l'index CodeGraph."""
    if not _get_codegraph_binary():
        _log_err("code-status", _CG_ABSENT, args)
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1("CodeGraph Status", f"Indexation physique du code sur : {target_dir}")
    try:
        res = _run_codegraph_command(["status", str(target_dir)])
        print(res.stdout if res.returncode == 0 else (res.stderr or res.stdout))
        return res.returncode
    except Exception as e:
        _log_err(
            "code-status",
            f"Erreur d'execution : {e}",
            args,
            target_keys=str(target_dir),
            exc_info=True,
        )
        return 1
