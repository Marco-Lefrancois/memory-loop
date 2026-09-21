"""
Handlers CLI mLoop pour le Harnais Déterministe de Phase 3 (ADR-0381 / EPIC-8).
Regroupe les commandes de vérification statique AST (code-check), tournoi (code-tournament)
et protocole TDD Red-Green (tdd-enforce).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from typing import Any

from src.cli import ZeroFluffConsole, LoggingConsole
from src.core.ast_checker import check_file_ast, format_audit_report

if TYPE_CHECKING:
    from src.state import LoopState


def _log_err(command: str, msg: str, args: Any = None, **ctx: Any) -> None:
    """Route une erreur handler vers LoggingConsole.error avec contexte standardise (MLOOP-142-BE)."""
    LoggingConsole.error(msg, command=command, project=getattr(args, "project", None), **ctx)


def handle_code_check(
    args: argparse.Namespace,
    state: Optional[LoopState] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Exécute l'audit statique AST déterministe sur un ou plusieurs fichiers."""
    file_arg = getattr(args, "file", None)
    all_arg = getattr(args, "all", False)
    story_arg = getattr(args, "story", None)

    files_to_check: list[Path] = []

    if file_arg:
        p = Path(file_arg)
        if not p.is_absolute() and project_path and (project_path / file_arg).exists():
            files_to_check.append(project_path / file_arg)
        else:
            files_to_check.append(p)
    elif story_arg:
        ZeroFluffConsole.info(f"Recherche des fichiers liés au récit {story_arg}...")
        # Chercher dans src/ et tests/
        patterns = [f"*{story_arg.lower()}*.py", f"*{story_arg.replace('-', '_').lower()}*.py"]
        for root_dir in [Path("src"), Path("tests")]:
            if root_dir.exists():
                for pat in patterns:
                    files_to_check.extend(root_dir.rglob(pat))
        if not files_to_check:
            ZeroFluffConsole.warning(f"Aucun fichier trouvé pour le motif {story_arg}.")
            return 1
    elif all_arg:
        ZeroFluffConsole.info("Audit statique AST de tous les modules sous src/...")
        src_dir = Path("src")
        if src_dir.exists():
            files_to_check = [
                f
                for f in src_dir.rglob("*.py")
                if "__pycache__" not in str(f) and ".venv" not in str(f)
            ]
    else:
        _log_err(
            "code-check",
            "Veuillez spécifier --file <chemin>, --story <ID> ou --all.",
            args,
            story_id=story_arg,
        )
        return 1

    total_violations = 0
    total_passed = 0

    for f_path in files_to_check:
        report = check_file_ast(f_path)
        if report.passed:
            total_passed += 1
            ZeroFluffConsole.info(
                f"[PASS] {f_path.as_posix()} ({report.line_count} lignes, {report.duration_ms:.1f}ms)"
            )
        else:
            total_violations += len(report.violations)
            print(format_audit_report(report), file=sys.stderr)

    ZeroFluffConsole.step_s1(
        "Bilan code-check AST",
        f"{total_passed}/{len(files_to_check)} conformes | {total_violations} violation(s)",
    )
    return 0 if total_violations == 0 else 1


def handle_code_tournament(
    args: argparse.Namespace,
    state: Optional[LoopState] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Exécute le tournoi multi-draft et la matrice de décision Pareto."""
    from src.pipelines.code_tournament import (
        CodeTournamentEngine,
        format_tournament_report,
        NoQualifiedCandidateError,
        DraftFolderNotFoundError,
    )

    story_id = getattr(args, "story", None)
    target_arg = getattr(args, "target", None)
    test_arg = getattr(args, "test_file", None)

    if not story_id or not target_arg:
        _log_err(
            "code-tournament",
            "Arguments obligatoires manquants : --story <ID> et --target <chemin>.",
            args,
            story_id=story_id,
        )
        return 1

    target_path = Path(target_arg)
    target_proj = getattr(args, "project", None) or os.getenv("MLOOP_ACTIVE_PROJECT", "mLoop")
    if project_path:
        base_dir = project_path
    elif (Path("Projects") / target_proj).exists():
        base_dir = Path("Projects") / target_proj
    else:
        base_dir = Path(".")

    drafts_dir = base_dir / "memory" / "drafts" / "code" / story_id
    if not drafts_dir.exists() and (Path("memory") / "drafts" / "code" / story_id).exists():
        drafts_dir = Path("memory") / "drafts" / "code" / story_id

    if test_arg:
        test_file = Path(test_arg)
    else:
        # Résolution automatique du banc de test
        story_slug = story_id.lower().replace("-", "_")
        candidates = list(Path("tests").glob(f"*{story_slug}*.py"))
        if not candidates:
            _log_err(
                "code-tournament",
                f"Aucun banc de test trouvé pour {story_id} sous tests/.",
                args,
                story_id=story_id,
            )
            return 1
        test_file = candidates[0]

    ZeroFluffConsole.step_s1("Tournoi de Code", f"Évaluation des candidats pour {story_id}...")
    try:
        engine = CodeTournamentEngine(
            story_id=story_id,
            drafts_dir=drafts_dir,
            target_path=target_path,
            test_file=test_file,
        )
        report = engine.run_tournament()
        print(format_tournament_report(report))
        ZeroFluffConsole.info(
            f"Golden Master promu avec succès : {report.winner_id} -> {target_path.as_posix()}"
        )
        return 0
    except (DraftFolderNotFoundError, NoQualifiedCandidateError) as e:
        _log_err(
            "code-tournament",
            f"Échec du tournoi de code : {e}",
            args,
            story_id=story_id,
            exc_info=True,
        )
        return 1
    except Exception as e:
        _log_err(
            "code-tournament",
            f"Erreur inattendue pendant le tournoi : {e}",
            args,
            story_id=story_id,
            exc_info=True,
        )
        return 1


# handle_tdd_enforce est extrait dans build_harness_tdd.py (découpage ADR-0202) et
# réexporté ci-dessous pour préserver le routing '_registry.py' (build_harness:handle_tdd_enforce).
from src.commands.handlers.build_harness_tdd import handle_tdd_enforce  # noqa: E402,F401
