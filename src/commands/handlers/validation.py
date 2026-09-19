"""Handlers Validation : aoep, audit-loop, eval, calibrate, plugin-validate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_aoep(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Évaluation AOEP (Agent Operational Excellence Protocol)."""
    from src.pipelines.aoep_runner import run_aoep_eval
    res = run_aoep_eval(args.project)
    print(json.dumps(res, indent=2))
    return 0 if res["aoep_score"] == "PASS" else 1


def handle_audit_loop(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Audit de boucle complet."""
    from src.pipelines.loop_audit import run_loop_audit
    res = run_loop_audit(args.project)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["status"] == "PASS" else 1


def handle_eval(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Évaluation automatisée du projet."""
    from src.pipelines.evals import EvalsEngine
    evals = EvalsEngine(project_name=args.project or "mLoop")
    report = evals.run_evals(state=state)
    return 0 if report.get("score", 0) >= 80 else 1


def handle_calibrate(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Auto-étalonnage de l'écosystème mLoop."""
    from src.pipelines.calibrate import EcosystemCalibrator
    calibrator = EcosystemCalibrator(
        root_dir=Path("."),
        project_name=args.project or "default",
        auto_repair=True,
    )
    success = calibrator.run_full_calibration()
    return 0 if success else 1


def handle_plugin_validate(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Valide la conformité Agent Plugin 1.0."""
    from src.pipelines.plugin_validate import run_plugin_validate
    result = run_plugin_validate(
        project_name=args.project,
        plugin_root=getattr(args, "plugin_root", None),
        strict=getattr(args, "strict", False),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "PASS" else 1


def handle_validate_sprint(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Certification déterministe de sprint Phase 4 (ADR-0383 / MLOOP-090-BE)."""
    from src.pipelines.qa_certifier import QaCertifierEngine, format_qa_markdown
    project_name = getattr(args, "project", None) or (project_path.name if project_path else "mLoop")
    timeout = getattr(args, "timeout", 240.0)
    test_dir_raw = getattr(args, "test_dir", None)
    test_dir = Path(test_dir_raw) if test_dir_raw else None
    engine = QaCertifierEngine(project_path=project_path, project_name=project_name, default_timeout=timeout)
    report = engine.certify_sprint(save_reports=True, test_dir=test_dir)
    print(format_qa_markdown(report))
    ZeroFluffConsole.step_s1(
        "Bilan Certification QA Sprint",
        f"Résultat : {'CERTIFIÉ CONFORME' if report.is_certified else 'REJETÉ (NON CONFORME)'}"
    )
    return 0 if report.is_certified else 1


def handle_nli_audit(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Audit contradictoire NLI et Verification Leakage Gate (ADR-0326 & ADR-0354 / MLOOP-091-BE)."""
    from src.pipelines.nli_auditor import NliAuditorEngine
    project_name = getattr(args, "project", None) or (project_path.name if project_path else "mLoop")
    engine = NliAuditorEngine(project_path=project_path, project_name=project_name)
    leakage, nli = engine.run_full_audit()
    ZeroFluffConsole.step_s1(
        "Audit Anti-Fuite (Verification Leakage Gate)",
        f"{'PASS' if leakage.passed else 'FAIL'} ({leakage.critical_violations} critique(s), {leakage.files_audited} fichier(s))"
    )
    ZeroFluffConsole.step_s1(
        "Audit Contradiction NLI (Documentation vs Invariants)",
        f"{'PASS' if nli.passed else 'FAIL'} ({nli.contradictions} contradiction(s), {nli.claims_verified} assertion(s))"
    )
    if leakage.details:
        for d in leakage.details:
            ZeroFluffConsole.warning(f"  * {d}")
    if nli.details:
        for d in nli.details:
            ZeroFluffConsole.warning(f"  * {d}")
    return 0 if (leakage.passed and nli.passed) else 1

