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
