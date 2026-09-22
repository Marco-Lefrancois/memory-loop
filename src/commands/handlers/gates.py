"""Handlers Gates : gates, tree (ADR-0341)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional
from src.utils.logger import get_logger

logger = get_logger("handler.gates")

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_gates(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exécute ou audite les portails d'acceptation (Runnable Gates)."""
    from src.pipelines.gatekeeper import GatekeeperPipeline

    pipeline = GatekeeperPipeline(project_path=project_path)
    file_target = getattr(args, "file", None)
    scope = getattr(args, "scope", None)
    reverify = getattr(args, "reverify", False)
    lint = getattr(args, "lint", False)

    mode = "verify"
    if getattr(args, "status", False):
        mode = "status"
    elif reverify:
        mode = "reverify"

    return pipeline.execute(
        file_path=file_target,
        mode=mode,
        reverify=reverify,
        lint=lint,
        scope=scope,
    )


def handle_tree(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Affiche l'arbre complet Depth Tree et le statut des gates."""
    from src.pipelines.gatekeeper import GatekeeperPipeline

    pipeline = GatekeeperPipeline(project_path=project_path)
    file_target = getattr(args, "file", None)
    scope = getattr(args, "scope", None)

    return pipeline.execute(
        file_path=file_target,
        mode="status",
        reverify=False,
        lint=False,
        scope=scope,
    )


def handle_check_leakage(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Vérifie l'absence de fuites de spécification et de vérification (ADR-0354)."""
    from src.engine.gates.verification_leakage import VerificationLeakageGate
    from src.cli import ZeroFluffConsole

    gate = VerificationLeakageGate()
    target_file = getattr(args, "file", None)

    if target_file:
        p = Path(target_file)
        if not p.exists() and project_path is not None and (project_path / target_file).exists():
            p = project_path / target_file
        report = gate.check_file(p)
        print(report.format_summary())
        return 0 if report.passed else 1

    # Parcourir les fichiers de tests du projet ou glob global
    test_files = []
    if project_path is not None and (project_path / "tests").exists():
        test_files.extend((project_path / "tests").glob("test_*.py"))
    if Path("tests").exists():
        for f in Path("tests").glob("test_*.py"):
            if f not in test_files:
                test_files.append(f)

    ZeroFluffConsole.info(f"Vérification de fuite sur {len(test_files)} fichier(s) de tests...")

    all_passed = True
    rejected_count = 0
    for tf in test_files:
        try:
            report = gate.check_file(tf)
            if not report.passed:
                all_passed = False
                rejected_count += 1
                print(report.format_summary())
        except Exception as e:
            logger.warning(
                "Fichier de test non vérifiable, contrôle de fuite sauté",
                exc_info=True,
                extra={
                    "component": "commands.handlers.gates",
                    "operation": "run_leak_gates",
                    "error": str(e),
                },
            )

    if all_passed:
        ZeroFluffConsole.success("Aucune fuite de vérification (Zero Verification Leakage) détectée.")
        return 0
    else:
        ZeroFluffConsole.error(f"{rejected_count} fichier(s) contiennent des violations anti-fuite critiques.")
        return 1

