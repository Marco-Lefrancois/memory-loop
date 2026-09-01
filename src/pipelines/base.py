"""
src/pipelines/base.py — Core Composable Pipeline Engine.

Exploite les méthodes magiques Python (__call__, __or__, __repr__) pour permettre
la composition fluide et déclarative de pipelines de traitement agentiques :
    pipeline = IngestStage() | GrillStage() | WikiFixStage()
    final_state = pipeline(state)
"""

from typing import List, Callable, Dict, Any
from src.state import LoopState
from src.cli import ZeroFluffConsole


class PipelineStage:
    """
    Classe de base abstraite pour toutes les étapes de pipeline mLoop.
    """

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__

    def execute(self, state: LoopState) -> LoopState:
        """Méthode à dériver par chaque étape du pipeline."""
        raise NotImplementedError("Chaque sous-classe doit implémenter la méthode execute()")

    def __call__(self, state: LoopState) -> LoopState:
        """
        Surcharge de __call__ pour rendre l'étape exécutable comme une fonction :
        state = stage(state)
        """
        ZeroFluffConsole.step_s1(self.name, f"Exécution de l'étape de pipeline [{self.name}]...")
        return self.execute(state)

    def __or__(self, next_stage: "PipelineStage") -> "CompositePipeline":
        """
        Surcharge de l'opérateur pipe | pour composer dynamiquement des pipelines :
        pipeline = StageA() | StageB() | StageC()
        """
        if isinstance(next_stage, CompositePipeline):
            return CompositePipeline([self] + next_stage.stages)
        return CompositePipeline([self, next_stage])

    def __repr__(self) -> str:
        return f"<PipelineStage: {self.name}>"


class CompositePipeline(PipelineStage):
    """
    Pipeline composé résultant de l'association de plusieurs étapes via le pipe |.
    """

    def __init__(self, stages: List[PipelineStage]):
        super().__init__(name="CompositePipeline")
        self.stages = stages

    def execute(self, state: LoopState) -> LoopState:
        current_state = state
        for stage in self.stages:
            current_state = stage(current_state)
            if str(current_state.current_phase).lower() == "error":
                ZeroFluffConsole.error(f"[PIPELINE INTERRUPT] Arrêt sur erreur dans {stage.name}")
                break
        return current_state

    def __or__(self, next_stage: PipelineStage) -> "CompositePipeline":
        if isinstance(next_stage, CompositePipeline):
            return CompositePipeline(self.stages + next_stage.stages)
        return CompositePipeline(self.stages + [next_stage])

    def __repr__(self) -> str:
        stage_names = " | ".join(s.name for s in self.stages)
        return f"<Pipeline: {stage_names}>"
