# src/state/_state_accessors.py — Mixin Accesseurs LoopState (MLOOP-173-BE)
# Familles : transitions FSM, query_graph, search_nodes
# INTERDIT : instancier LoopState ou ProjectState ici (§3.2 singleton)

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.state._state_core import (
    AnalysisResult,
    IntegrityError,
    JournalEntry,
    LoopPhase,
    MaxRevisionsReached,
    ProjectMode,
    QAReport,
    SavepointManager,
    logger,
)


class StateAccessorsMixin:
    """
    Mixin portant les méthodes FSM et de requête graph de LoopState.
    Ne contient aucune instanciation de LoopState (règle §3.2).
    Doit être combiné avec StateSerializerMixin et BaseModel.
    """

    # ─── Typing stubs (résolus par LoopState au runtime via BaseModel) ───
    project_name: str
    project_mode: "ProjectMode"
    current_phase: "LoopPhase"
    previous_phase: Optional["LoopPhase"]
    current_state_id: Optional[str]
    last_checkpoint_timestamp: float
    checkpoint_interval_seconds: int
    analysis: Optional["AnalysisResult"]
    plan: Any
    qa_report: Optional["QAReport"]
    journal: List["JournalEntry"]

    def should_checkpoint(self, interval_seconds: Optional[int] = None) -> bool:
        """Vérifie si le délai temporel (60 à 90s) depuis le dernier checkpoint est dépassé."""
        import time

        target_interval = interval_seconds or self.checkpoint_interval_seconds
        return (time.time() - self.last_checkpoint_timestamp) >= target_interval

    def restore_latest_checkpoint(self, project_path: Optional[Path] = None) -> bool:
        """Restaure l'état depuis le plus récent checkpoint valide."""
        target_proj = project_path or (
            Path("Projects") / self.project_name if self.project_name else None
        )
        state_dict = SavepointManager.load_latest_checkpoint(target_proj)
        if not state_dict:
            return False
        try:
            # Import local pour éviter la circularité : LoopState est défini dans __init__.py
            from src.state import LoopState  # noqa: PLC0415

            loaded = LoopState.model_validate(state_dict)
            for field in self.__class__.model_fields:
                if field not in ("sprint_backlog", "knowledge_graph"):
                    setattr(self, field, getattr(loaded, field))
            return True
        except Exception as e:
            logger.warning(f"Erreur lors de la validation du checkpoint restauré: {e}")
            return False

    def can_transition_to(self, target_phase: "LoopPhase") -> bool:
        """Vérifie si une transition de phase est légale selon le mode et l'état."""
        if target_phase == LoopPhase.ERROR:
            return True
        if self.project_mode == ProjectMode.CLIENT:
            if self.current_phase == LoopPhase.SPEC and target_phase == LoopPhase.PLAN:
                return True
            if self.current_phase == LoopPhase.PLAN and target_phase == LoopPhase.VALIDATE:
                return True
            return False
        elif self.project_mode == ProjectMode.MLOOP:
            if self.current_phase == LoopPhase.SPEC and target_phase == LoopPhase.PLAN:
                return True
            if self.current_phase == LoopPhase.PLAN and target_phase == LoopPhase.BUILD:
                return True
            if self.current_phase == LoopPhase.BUILD and target_phase == LoopPhase.VALIDATE:
                return True
            if self.current_phase == LoopPhase.VALIDATE and target_phase == LoopPhase.SHIP:
                return True
            if self.current_phase == LoopPhase.VALIDATE and target_phase == LoopPhase.PLAN:
                if self.qa_report and self.qa_report.revisions_count > 5:
                    return False
                return True
            return False
        return False

    def transition_to(self, target_phase: "LoopPhase") -> None:
        """Effectue une transition de phase avec vérification stricte d'intégrité."""
        if target_phase == LoopPhase.ERROR:
            self.previous_phase = self.current_phase
            self.current_phase = LoopPhase.ERROR
            self.current_state_id = LoopPhase.ERROR.value
            return

        if target_phase == LoopPhase.PLAN:
            if self.current_phase == LoopPhase.SPEC:
                if self.analysis is None:
                    raise IntegrityError("AnalysisResult requis pour passer en phase PLAN.")
                if self.analysis.missing_information:
                    raise IntegrityError(
                        "Des informations manquantes bloquent le passage en phase PLAN."
                    )
            elif (
                self.current_phase == LoopPhase.VALIDATE and self.project_mode == ProjectMode.MLOOP
            ):
                if self.qa_report and self.qa_report.revisions_count > 5:
                    self.current_phase = LoopPhase.ERROR
                    self.current_state_id = LoopPhase.ERROR.value
                    raise MaxRevisionsReached(
                        "Circuit Breaker : Nombre maximal de révisions dépassé (> 5)."
                    )

        if (
            target_phase == LoopPhase.VALIDATE
            and self.current_phase == LoopPhase.PLAN
            and self.project_mode == ProjectMode.CLIENT
        ):
            if self.plan is None:
                raise IntegrityError("PlanResult requis pour passer en phase VALIDATE.")

        if target_phase == LoopPhase.BUILD and self.current_phase == LoopPhase.PLAN:
            if self.project_mode == ProjectMode.CLIENT:
                raise ValueError(
                    "Transition de phase invalide : BUILD est interdit en mode CLIENT."
                )
            if self.plan is None:
                raise IntegrityError("PlanResult requis pour passer en phase BUILD.")

        if not self.can_transition_to(target_phase):
            raise ValueError(
                f"Transition de phase invalide : '{self.current_phase.value}' -> '{target_phase.value}' en mode '{self.project_mode.value}'."
            )

        self.previous_phase = self.current_phase
        self.current_phase = target_phase
        self.current_state_id = target_phase.value

    def query_graph(self, question: str) -> str:
        """Recherche in-memory ultra-rapide (remplace l'appel shell coûteux vers graphify)."""
        from src.loop_mem.db import search_in_memory

        project_path = Path("Projects") / self.project_name
        results = search_in_memory(project_path, question, limit=10)
        if not results:
            return "Aucun résultat trouvé dans la mémoire."

        output = [f"--- Résultats in-memory pour '{question}' ---"]
        for r in results:
            output.append(
                f"[{r.get('category', 'Node')}] {r.get('label', r.get('id'))} (ID: {r['id']}) - Score: {r['score']:.1f}"
            )
            snippet = r.get("snippet", "").replace("\n", " ")
            output.append(f"  > {snippet}")
        return "\n".join(output)

    def explain_node(self, node_label: str) -> str:
        """Explique un nœud via in-memory search."""
        return self.query_graph(node_label)

    def search_nodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche rapide en mémoire dans le graphe consolidé."""
        from src.loop_mem.db import search_in_memory

        project_path = Path("Projects") / self.project_name
        return search_in_memory(project_path, query, limit)


__all__ = ["StateAccessorsMixin"]
