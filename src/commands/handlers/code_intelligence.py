"""
Handlers Code Intelligence : Integration de CodeGraph dans le framework mLoop (ADR-0204 et ADR-0363).
Fournit une passerelle deterministe pour l'exploration AST, l'analyse d'impact et les tests affectes
avec support autonome de projet (no_project: True), cache memoire et Token Budget Guardrail (--compact).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

# Cache Singleton en memoire pour eviter les relances repetitives de sous-processus
_CODEGRAPH_CACHE: dict[str, str] = {}


def _find_target_source_path(project_path: Optional[Path] = None, explicit_path: Optional[str] = None) -> Path:
    """Resout le chemin du code source a interroger ou indexer de facon autonome."""
    if explicit_path:
        p = Path(explicit_path)
        if p.is_absolute() and p.exists():
            return p
        if project_path:
            candidate = project_path / explicit_path
            if candidate.exists():
                return candidate
        root_candidate = Path(".") / explicit_path
        if root_candidate.exists():
            return root_candidate

    # 1. Si un project_path explicite est fourni
    if project_path and project_path.exists():
        if (project_path / ".codegraph").exists():
            return project_path
        for dot_cg in project_path.glob("**/.codegraph"):
            if dot_cg.is_dir():
                return dot_cg.parent
        ref_dir = project_path / "reference"
        if ref_dir.exists():
            for child in ref_dir.iterdir():
                if child.is_dir():
                    return child
        return project_path

    # 2. Si aucun project_path, verifier le projet actif en base SQLite
    try:
        from src.loop_mem.db import get_active_project
        act_proj = get_active_project()
        if act_proj:
            act_path = Path("Projects") / act_proj
            if act_path.exists():
                # Verifier si ce projet a un sous-dossier avec .codegraph ou du code reference
                for dot_cg in act_path.glob("**/.codegraph"):
                    if dot_cg.is_dir():
                        return dot_cg.parent
                ref_dir = act_path / "reference"
                if ref_dir.exists():
                    for child in ref_dir.iterdir():
                        if child.is_dir():
                            return child
    except Exception:
        pass

    # 3. En dernier ressort : la racine du workspace ou reside la base globale (928 Mo)
    return Path(".")


def _get_codegraph_binary() -> Optional[str]:
    """Trouve l'executable codegraph dans le PATH."""
    return shutil.which("codegraph")


def _run_codegraph_command(args_list: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Execute une commande CodeGraph de facon multi-plateforme (Windows & Unix)."""
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


def _compact_explore_output(raw: str, max_code_lines: int = 8) -> str:
    """
    Token Budget Guardrail : condense la sortie d'exploration AST pour eviter d'inonder
    la fenetre d'inference de l'agent de blocs de code verbatim massifs (> 1000 lignes).
    """
    lines = raw.splitlines()
    if len(lines) <= 60:
        return raw

    compacted: list[str] = []
    in_code_block = False
    code_block_count = 0

    for line in lines:
        # Detecter les separateurs ou en-tetes de symboles
        if line.startswith("===") or line.startswith("File:") or line.startswith("Symbol:") or "Called by:" in line or "Calls:" in line:
            in_code_block = False
            code_block_count = 0
            compacted.append(line)
            continue

        # Ligne numerotee de code (ex: "314\t if status not in...")
        if re.match(r"^\d+\s", line) or re.match(r"^\d+\t", line):
            if not in_code_block:
                in_code_block = True
                code_block_count = 0

            code_block_count += 1
            if code_block_count <= max_code_lines:
                compacted.append(line)
            elif code_block_count == max_code_lines + 1:
                compacted.append("    ... [Corps de code tronque pour preserver le budget de tokens. Utiliser sans --compact pour le verbatim complet]")
            continue

        # Lignes d'annotations ou de resume finales
        if "output truncated" in line or "[OK]" in line:
            compacted.append(line)
            continue

        if not in_code_block or code_block_count <= max_code_lines:
            compacted.append(line)

    return "\n".join(compacted)


def handle_code_init(args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None) -> int:
    """Initialise l'indexation CodeGraph sur le code source d'un projet."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas installee dans le PATH. Executez 'npm install -g @colbymchenry/codegraph'.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1("CodeGraph Init", f"Initialisation du graphe de code sur : {target_dir}")

    try:
        res = _run_codegraph_command(["init", str(target_dir)])
        if res.returncode == 0:
            print(res.stdout)
            ZeroFluffConsole.success(f"Index CodeGraph initialise avec succes sur {target_dir}")
            return 0
        else:
            ZeroFluffConsole.error(f"Echec de codegraph init : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur lors de l'execution de codegraph init : {e}")
        return 1


def handle_code_explore(args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None) -> int:
    """Explore le code source physique via CodeGraph (AST, symboles verbatim, chemins d'appels)."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible. Executez 'npm install -g @colbymchenry/codegraph'.")
        return 1

    query = getattr(args, "query", "").strip()
    if not query:
        ZeroFluffConsole.error("L'argument --query est obligatoire pour l'exploration de code.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    compact = getattr(args, "compact", False)
    cache_key = f"explore:{target_dir}:{query}:{compact}"

    if cache_key in _CODEGRAPH_CACHE:
        print(_CODEGRAPH_CACHE[cache_key])
        return 0

    ZeroFluffConsole.step_s1("CodeGraph Explore", f"Recherche de '{query}' dans {target_dir}{' (Mode Compact)' if compact else ''}")

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
            ZeroFluffConsole.error(f"Erreur codegraph explore : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'execution : {e}")
        return 1


def handle_code_impact(args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None) -> int:
    """Calcule le rayon d'impact (Blast Radius) d'un symbole dans la base de code."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible.")
        return 1

    symbol = getattr(args, "symbol", "").strip()
    if not symbol:
        ZeroFluffConsole.error("L'argument --symbol est obligatoire.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    cache_key = f"impact:{target_dir}:{symbol}"

    if cache_key in _CODEGRAPH_CACHE:
        print(_CODEGRAPH_CACHE[cache_key])
        return 0

    ZeroFluffConsole.step_s1("CodeGraph Impact", f"Calcul de l'impact pour '{symbol}' dans {target_dir}")

    try:
        res = _run_codegraph_command(["impact", str(symbol)], cwd=target_dir)
        if res.returncode == 0:
            _CODEGRAPH_CACHE[cache_key] = res.stdout
            print(res.stdout)
            return 0
        else:
            ZeroFluffConsole.error(f"Erreur codegraph impact : {res.stderr or res.stdout}")
            return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'execution : {e}")
        return 1


def handle_code_affected(args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None) -> int:
    """Identifie les tests affectes par les changements de code source."""
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
        ZeroFluffConsole.error(f"Erreur d'execution : {e}")
        return 1


def handle_code_status(args: argparse.Namespace, state: Optional[LoopState] = None, project_path: Optional[Path] = None) -> int:
    """Affiche les statistiques de l'index CodeGraph."""
    if not _get_codegraph_binary():
        ZeroFluffConsole.error("La CLI 'codegraph' n'est pas disponible.")
        return 1

    target_dir = _find_target_source_path(project_path, getattr(args, "path", None))
    ZeroFluffConsole.step_s1("CodeGraph Status", f"Indexation physique du code sur : {target_dir}")
    try:
        res = _run_codegraph_command(["status", str(target_dir)])
        print(res.stdout if res.returncode == 0 else (res.stderr or res.stdout))
        return res.returncode
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur d'execution : {e}")
        return 1