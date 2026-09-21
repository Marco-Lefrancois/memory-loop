"""
Primitives partagees Code Intelligence (MLOOP-142-BE / ADR-0202 decoupage modulaire).

Regroupe les fonctions utilitaires deterministes consommees par les handlers
`code_intelligence.py` (resolution de chemin source, invocation CodeGraph avec
deadline stricte ADR-0369, compaction de sortie AST, cache memoire et routage
d'erreurs instrumente LoggingConsole). Isole de la surface handler pour maintenir
chaque module sous le plafond de 300 lignes (ADR-0202).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from src.cli import LoggingConsole
from src.utils.logger import get_logger

logger = get_logger("handler.code_intelligence")

# Message unifie d'absence de la CLI CodeGraph (deduplique sur tous les handlers).
_CG_ABSENT = (
    "La CLI 'codegraph' n'est pas disponible. Executez 'npm install -g @colbymchenry/codegraph'."
)

# Cache Singleton en memoire pour eviter les relances repetitives de sous-processus.
_CODEGRAPH_CACHE: dict[str, str] = {}


def _log_err(command: str, msg: str, args: Any = None, **ctx: Any) -> None:
    """Route une erreur handler vers LoggingConsole.error avec contexte standardise (MLOOP-142-BE)."""
    LoggingConsole.error(msg, command=command, project=getattr(args, "project", None), **ctx)


def _find_target_source_path(
    project_path: Optional[Path] = None, explicit_path: Optional[str] = None
) -> Path:
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
    except Exception as e:
        logger.debug(
            "Resolution du projet actif SQLite echouee (non-bloquant, repli sur racine workspace).",
            exc_info=True,
            extra={"command": "code-intelligence", "phase": "resolve_source_path", "error": str(e)},
        )

    # 3. En dernier ressort : la racine du workspace ou reside la base globale (928 Mo)
    return Path(".")


def _get_codegraph_binary() -> Optional[str]:
    """Trouve l'executable codegraph dans le PATH."""
    return shutil.which("codegraph")


def _run_codegraph_command(
    args_list: list[str], cwd: Optional[Path] = None, timeout: float = 30.0
) -> subprocess.CompletedProcess:
    """Execute une commande CodeGraph avec deadline stricte (ADR-0369)."""
    bin_path = _get_codegraph_binary() or "codegraph"
    full_cmd = [bin_path] + args_list
    use_shell = sys.platform == "win32"
    try:
        return subprocess.run(
            full_cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
            shell=use_shell,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=full_cmd,
            returncode=124,
            stdout="",
            stderr=f"[CodeGraph Timeout] Délai d'attente de {timeout}s expiré pour {' '.join(full_cmd)}",
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
        if (
            line.startswith("===")
            or line.startswith("File:")
            or line.startswith("Symbol:")
            or "Called by:" in line
            or "Calls:" in line
        ):
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
                compacted.append(
                    "    ... [Corps de code tronque pour preserver le budget de tokens. Utiliser sans --compact pour le verbatim complet]"
                )
            continue

        # Lignes d'annotations ou de resume finales
        if "output truncated" in line or "[OK]" in line:
            compacted.append(line)
            continue

        if not in_code_block or code_block_count <= max_code_lines:
            compacted.append(line)

    return "\n".join(compacted)
