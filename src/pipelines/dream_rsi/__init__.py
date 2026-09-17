"""
src/pipelines/dream_rsi/__init__.py — Package Dream RSI (ADR-0202 & ADR-0372).

Expose les composants modulaires pour l'auto-amélioration récursive hors-ligne :
- ReplaySimulator : simulateur sans inférence LLM sur arbres de traces historiques.
- ModularHarnessIsolator : isolation et diagnostic des défaillances du harnais.
- DreamExplorer : exploration de méta-politiques avec garantie de non-régression.
- DreamRSIStage : étape composable PipelineStage (src/pipelines/base.py).
"""
from src.pipelines.dream_rsi.simulator import (
    PolicyParams,
    ReplayNode,
    SimulationResult,
    ReplaySimulator,
)
from src.pipelines.dream_rsi.harness_isolator import (
    HarnessFailureCategory,
    HarnessDiagnosis,
    ModularHarnessIsolator,
)
from src.pipelines.dream_rsi.explorer import DreamExplorer
from src.pipelines.dream_rsi.stage import DreamRSIStage

__all__ = [
    "PolicyParams",
    "ReplayNode",
    "SimulationResult",
    "ReplaySimulator",
    "HarnessFailureCategory",
    "HarnessDiagnosis",
    "ModularHarnessIsolator",
    "DreamExplorer",
    "DreamRSIStage",
]
