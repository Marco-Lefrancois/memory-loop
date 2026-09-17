"""
src/pipelines/dream_rsi/stage.py — Étape de Pipeline Composable Dream RSI (ADR-0372).

Intègre l'auto-amélioration récursive dans l'orchestration pipeline mLoop (PipelineStage).
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import logging
from pathlib import Path
from typing import Optional

from src.cli import ZeroFluffConsole
from src.pipelines.base import PipelineStage
from src.pipelines.dream_rsi.explorer import DreamExplorer
from src.pipelines.dream_rsi.harness_isolator import ModularHarnessIsolator
from src.pipelines.dream_rsi.simulator import ReplaySimulator
from src.state import JournalEntry, LoopState

logger = logging.getLogger(__name__)


class DreamRSIStage(PipelineStage):
    """
    Étape de pipeline mLoop composable (src/pipelines/base.py) :
        pipeline = IngestStage() | DreamRSIStage() | AgentResilienceStage()
    """

    def __init__(self, name: str = "DreamRSIStage", project_path: Optional[Path] = None):
        super().__init__(name=name)
        self.project_path = project_path
        self.last_result: Optional[dict] = None

    def execute(self, state: LoopState) -> LoopState:
        proj_name = state.project_name or "mLoop"
        proj_path = self.project_path or (
            Path("Projects") / proj_name if (Path("Projects") / proj_name).exists() else Path(".")
        )

        ZeroFluffConsole.step_s1(
            self.name, f"Lancement de la simulation hors-ligne Dream RSI pour '{proj_name}'..."
        )

        # 1. Chargement des traces dans le Replay Simulator
        episodes = ReplaySimulator.load_from_project(proj_path)
        ep_count = len(episodes)
        ZeroFluffConsole.step_s1(
            self.name, f"Simulateur de replay prêt : {ep_count} épisodes historiques chargés (coût LLM nul)."
        )

        # 2. Diagnostic d'isolation modulaire du harnais
        diagnosis = ModularHarnessIsolator.analyze(episodes)
        ZeroFluffConsole.step_s1(
            self.name,
            f"Isolation harnais : Goulot majeur [{diagnosis.primary_bottleneck}] (Score harnais: {diagnosis.isolated_harness_score}/100)",
        )

        # 3. Exploration méta-politique avec garantie de non-régression
        best_res, all_res = DreamExplorer.explore(episodes)
        gain = best_res.gain_vs_pi0
        ZeroFluffConsole.step_s1(
            self.name,
            f"Politique sélectionnée: {best_res.policy.name} | Succès: {best_res.simulated_success_rate * 100:.1f}% | Gain vs pi_0: +{gain:.1f}%",
        )

        # 4. Sauvegarde dans les résultats du stage et journalisation
        self.last_result = {
            "project_name": proj_name,
            "episodes_simulated": ep_count,
            "best_policy": {
                "name": best_res.policy.name,
                "branching_factor": best_res.policy.branching_factor,
                "patience": best_res.policy.patience,
                "early_stopping_threshold": best_res.policy.early_stopping_threshold,
                "strategy": best_res.policy.strategy,
            },
            "success_rate": best_res.simulated_success_rate,
            "gain_vs_pi0": gain,
            "harness_diagnosis": {
                "primary_bottleneck": diagnosis.primary_bottleneck,
                "distribution": diagnosis.distribution,
                "score": diagnosis.isolated_harness_score,
                "recommendations": diagnosis.recommendations,
            },
        }

        if hasattr(state, "journal") and isinstance(state.journal, list):
            state.journal.append(
                JournalEntry(
                    event="DREAM_RSI_OPTIMIZATION",
                    details=f"Politique: {best_res.policy.name} (Gain: +{gain:.1f}%) | Goulot: {diagnosis.primary_bottleneck}",
                )
            )

        return state
