"""Handlers Architecture — Analysis (deepen, diagnose, goal-cascade, to-sow)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

def handle_deepen(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un rapport HTML de profondeur d'architecture."""
    from src.pipelines.arch_analyzer import ArchAnalyzerEngine

    aa = ArchAnalyzerEngine(project_path)
    report_path = aa.generate_html_report()
    ZeroFluffConsole.success(
        f"Rapport HTML de profondeur d'architecture généré : {report_path}"
    )
    return 0


def handle_diagnose(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un harnais de reproduction déterministe."""
    from src.pipelines.diagnostics import DiagnosticEngine

    de = DiagnosticEngine(project_path)
    harness_path = de.create_harness(
        symptom_name=getattr(args, "symptom", "Symptome_Inconnu"),
        symptom_description="Régression ou anomalie d'état constatée.",
        command_invocation="python src/swarm.py confidence --file ...",
        initial_output="ECHEC / SIGNAL ROUGE",
    )
    ZeroFluffConsole.success(
        f"Harnais de reproduction déterministe généré : {harness_path}"
    )
    return 0


def handle_goal_cascade(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Alignement stratégique et Goal-Cascading (Wayfinder -> Epics -> Stories)."""
    from src.pipelines.goal_cascade import run_goal_cascade

    report = run_goal_cascade(project_path)
    ZeroFluffConsole.success(
        f"Goal-Cascading : {report['aligned_stories']}/{report['total_stories']} récit(s) alignés (Score: {report['alignment_score']}%)."
    )
    return 0


def handle_to_sow(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génère un Énoncé des Travaux (SOW) et Évaluation Budgétaire depuis le gabarit officiel."""
    from src.pipelines.sow_engine import SOWEngine
    from src.pipelines.sync import run_sync

    title = getattr(args, "title", None)
    size = getattr(args, "size", None) or "M"

    engine = SOWEngine(project_path)
    sow_path = engine.generate_sow(title=title, target_size=size)
    ZeroFluffConsole.success(f"Énoncé des Travaux (SOW) généré : {sow_path}")

    # ADR-0331 §2.2 Règle #3 : Interdiction Formelle des Libellés Génériques
    granularity_violations = engine.validate_task_granularity(sow_path)
    if granularity_violations:
        ZeroFluffConsole.warning(
            f"[ADR-0331] {len(granularity_violations)} libellé(s) générique(s) "
            f"détecté(s) dans le tableau de chiffrage détaillé :"
        )
        for v in granularity_violations:
            ZeroFluffConsole.warning(f"  - {v}")

    return 0
