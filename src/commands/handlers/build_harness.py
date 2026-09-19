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

from src.cli import ZeroFluffConsole
from src.core.ast_checker import check_file_ast, format_audit_report

if TYPE_CHECKING:
    from src.state import LoopState


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
                f for f in src_dir.rglob("*.py")
                if "__pycache__" not in str(f) and ".venv" not in str(f)
            ]
    else:
        ZeroFluffConsole.error("Veuillez spécifier --file <chemin>, --story <ID> ou --all.")
        return 1

    total_violations = 0
    total_passed = 0

    for f_path in files_to_check:
        report = check_file_ast(f_path)
        if report.passed:
            total_passed += 1
            ZeroFluffConsole.info(f"[PASS] {f_path.as_posix()} ({report.line_count} lignes, {report.duration_ms:.1f}ms)")
        else:
            total_violations += len(report.violations)
            print(format_audit_report(report), file=sys.stderr)

    ZeroFluffConsole.step_s1(
        "Bilan code-check AST",
        f"{total_passed}/{len(files_to_check)} conformes | {total_violations} violation(s)"
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
        ZeroFluffConsole.error("Arguments obligatoires manquants : --story <ID> et --target <chemin>.")
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
            ZeroFluffConsole.error(f"Aucun banc de test trouvé pour {story_id} sous tests/.")
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
        ZeroFluffConsole.info(f"Golden Master promu avec succès : {report.winner_id} -> {target_path.as_posix()}")
        return 0
    except (DraftFolderNotFoundError, NoQualifiedCandidateError) as e:
        ZeroFluffConsole.error(f"Échec du tournoi de code : {e}")
        return 1
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur inattendue pendant le tournoi : {e}")
        return 1


def handle_tdd_enforce(
    args: argparse.Namespace,
    state: Optional[LoopState] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Commande d'enforcement et de traçabilité du cycle TDD Red-Green (ADR-0381)."""
    from src.core.tdd_enforcer import (
        TddEnforcer,
        format_tdd_status,
        MissingRedSnapshotError,
        UnexpectedPassingTestError,
        TestFailureError,
        AstViolationError,
    )

    phase = getattr(args, "phase", None)
    story_id = getattr(args, "story", None)
    test_arg = getattr(args, "test_file", None)
    source_arg = getattr(args, "source_file", None)

    if not phase or not story_id:
        ZeroFluffConsole.error("Arguments obligatoires : --phase [red|green|verify] et --story <ID>.")
        return 1

    target_proj = getattr(args, "project", None) or os.getenv("MLOOP_ACTIVE_PROJECT", "mLoop")
    if project_path:
        base_dir = project_path
    elif (Path("Projects") / target_proj).exists():
        base_dir = Path("Projects") / target_proj
    else:
        base_dir = Path(".")

    evidence_file = base_dir / "memory" / "evidence" / f"{story_id}_evidence.json"
    if not evidence_file.exists() and (Path("Projects") / "mLoop" / "memory" / "evidence" / f"{story_id}_evidence.json").exists():
        evidence_file = Path("Projects") / "mLoop" / "memory" / "evidence" / f"{story_id}_evidence.json"

    enforcer = TddEnforcer()

    try:
        if phase == "red":
            if not test_arg:
                story_slug = story_id.lower().replace("-", "_")
                candidates = list(Path("tests").glob(f"*{story_slug}*.py"))
                if not candidates:
                    ZeroFluffConsole.error(f"Spécifier --test-file pour la phase RED de {story_id}.")
                    return 1
                test_file = candidates[0]
            else:
                test_file = Path(test_arg)

            ZeroFluffConsole.step_s1("TDD Enforcer [RED]", f"Vérification de l'échec initial pour {story_id}...")
            red = enforcer.record_red(story_id, test_file, evidence_file)
            ZeroFluffConsole.info(f"Sceau RED validé : exit_code={red.exit_code} | SHA-256={red.test_sha256[:12]}...")
            return 0

        elif phase == "green":
            if not test_arg or not source_arg:
                ZeroFluffConsole.error("La phase GREEN exige --test-file et --source-file.")
                return 1

            ZeroFluffConsole.step_s1("TDD Enforcer [GREEN]", f"Vérification du succès complet pour {story_id}...")
            green = enforcer.record_green(story_id, Path(test_arg), Path(source_arg), evidence_file)
            ZeroFluffConsole.info(f"Sceau GREEN validé : exit_code={green.exit_code} | AST=OK | SHA-256={green.source_sha256[:12]}...")
            return 0

        elif phase == "verify":
            ZeroFluffConsole.step_s1("TDD Enforcer [VERIFY]", f"Vérification conformité Gate 3 pour {story_id}...")
            compliant = enforcer.verify_gate_3_compliance(story_id, evidence_file)
            if compliant:
                ZeroFluffConsole.info(f"Récit {story_id} certifié TDD Red-Green. Approbation Gate 3 déverrouillée.")
                return 0
            else:
                ZeroFluffConsole.error(f"Récit {story_id} non conforme TDD (couple Red/Green incomplet).")
                return 1
        else:
            ZeroFluffConsole.error(f"Phase inconnue : {phase} (valeurs admises : red, green, verify).")
            return 1

    except (MissingRedSnapshotError, UnexpectedPassingTestError, TestFailureError, AstViolationError) as e:
        ZeroFluffConsole.error(f"Violation TDD Enforcer : {e}")
        return 1
    except Exception as e:
        ZeroFluffConsole.error(f"Erreur TDD Enforcer : {e}")
        return 1


