"""
Handlers Code Intelligence : Intégration de CodeGraph dans le framework mLoop (ADR-0204).
Fournit une passerelle déterministe pour l'exploration AST, l'analyse d'impact et les tests affectés.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def _find_target_source_path(project_path: Path, explicit_path: Optional[str] = None) -> Path:
    """Résout le chemin du code source à interroger ou indexer."""
    if explicit_path:
        p = Path(explicit_path)
        if p.is_absolute() and p.exists():
            return p
        candidate = project_path / explicit_path
        if candidate.exists():
            return candidate

    # 1. Vérifier si un index .codegraph existe déjà dans project_path
    if (project_path / ".codegraph").exists():
        return project_path

    # 2. Chercher un sous-dossier contenant .codegraph (ex: reference/metro_food)
    for dot_cg in project_path.glob("**/.codegraph"):
        if dot_cg.is_dir():
            return dot_cg.parent

    # 3. Chercher dans reference/
    ref_dir = project_path / "reference"
    if ref_dir.exists():
        for child in ref_dir.iterdir():
            if child.is_dir():
                return child

    return project_path


def _get_codegraph_binary() -> Optional[str]:
    """Trouve l'exécutable codegraph dans le PATH."""
    return shutil.which("codegraph")


def _run_codegraph_command(args_list: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Exécute une commande CodeGraph de façon multi-plateforme (Windows & Unix)."""
    bin_path = _get_codegraph_binary() or "codegraph"
    full_cmd = [bin_path] + args_list
    use_shell = sys.platform == "win32"
    return subprocess.run(
        full_cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
        shell=use_shell,
        encoding="utf-8",
        errors="replace",
    )


def handle_code_init(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Initialise l'indexation CodeGraph sur le code source d'un projet."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas installée dans le PATH. Exécutez 'npm install -g @colbymchenry/codegraph'.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1("CodeGraph Init", f"Initialisation du graphe de code sur : {target_dir}")

    try:
        res = _run_codegraph_command(["init", str(target_dir)])
        if res.returncode == 0:
            print(res.stdout)
            ZeroFluffConsole.success(f"Index CodeGraph initialisé avec succès sur {target_dir}")
            return 0
        else:
            ZeroFluffConsole.error(f"Échec de codegraph init : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors de l'exécution de codegraph init : {e}")
        return 1


def handle_code_explore(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Explore le code source physique via CodeGraph (AST, symboles verbatim, chemins d'appels)."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible. Exécutez 'npm install -g @colbymchenry/codegraph'.")
        return 1

    query = getattr(args, "query", "")
    if not query:
        ZeroFluffConsole.error("L'argument --query est obligatoire pour l'exploration de code.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1("CodeGraph Explore", f"Recherche de '{query}' dans {target_dir}")

    try:
        res = _run_codegraph_command(["explore", "-p", str(target_dir), str(query)])
        if res.returncode == 0:
            print(res.stdout)
            return 0
        else:
            ZeroFluffConsole.error(f"Erreur codegraph explore : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'exécution : {e}")
        return 1


def handle_code_impact(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Calcule le rayon d'impact (Blast Radius) d'un symbole dans la base de code."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible.")
        return 1

    symbol = getattr(args, "symbol", "")
    if not symbol:
        ZeroFluffConsole.error("L'argument --symbol est obligatoire.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1("CodeGraph Impact", f"Calcul de l'impact pour '{symbol}' dans {target_dir}")

    try:
        res = _run_codegraph_command(["impact", str(symbol)], cwd=target_dir)
        if res.returncode == 0:
            print(res.stdout)
            return 0
        else:
            ZeroFluffConsole.error(f"Erreur codegraph impact : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'exécution : {e}")
        return 1


def handle_code_affected(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Identifie les tests affectés par les changements de code source."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible.")
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
            ZeroFluffConsole.error(f"Erreur codegraph affected : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'exécution : {e}")
        return 1


def handle_code_status(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Affiche les statistiques de l'index CodeGraph."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    try:
        res = _run_codegraph_command(["status", str(target_dir)])
        print(res.stdout if res.returncode == 0 else (res.stderr or res.stdout))
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'exécution : {e}")
        return 1
