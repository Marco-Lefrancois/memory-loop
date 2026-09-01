"""
Orchestrateur Asymétrique Système 1 / Système 2 (MLOOP-002-BE / MLOOP-003-BE).
"""
from typing import Optional
from src.state import LoopState, LoopPhase, ProjectMode
from src.agents.base import BaseAgent
from src.agents.circuit_breaker import FinancialCircuitBreaker


class AsymmetricOrchestrator:
    """
    Règles de routage asymétrique :
    - SPEC & PLAN : Toujours routés vers Système 2 (LLM Cognitif).
    - CLIENT / VALIDATE : Routé vers Système 1 (Audit local WikiFix / FTS5).
    - CLIENT / BUILD & SHIP : Interdits (lèvent RuntimeError).
    - MLOOP / BUILD, VALIDATE, SHIP : Routés vers Système 1 (Exécution locale).
    - ERROR : Aucun agent n'est invoqué.
    """

    def __init__(
        self,
        s1_agent: BaseAgent,
        s2_agent: BaseAgent,
        circuit_breaker: Optional[FinancialCircuitBreaker] = None,
    ) -> None:
        self.s1_agent = s1_agent
        self.s2_agent = s2_agent
        self.circuit_breaker = circuit_breaker

    def execute_step(self, state: LoopState) -> LoopState:
        """Exécute un tour d'orchestration selon la phase et le mode du projet."""
        if state.current_phase == LoopPhase.ERROR:
            return state

        # 1. Détermination de la cible de routage
        target = None
        if state.current_phase in (LoopPhase.SPEC, LoopPhase.PLAN):
            target = "s2"
        elif state.project_mode == ProjectMode.CLIENT:
            if state.current_phase == LoopPhase.VALIDATE:
                target = "s1"
            elif state.current_phase in (LoopPhase.BUILD, LoopPhase.SHIP):
                raise RuntimeError(
                    f"Phase '{state.current_phase.value}' non routeable en mode 'client' (réservé à l'humain)."
                )
        elif state.project_mode == ProjectMode.MLOOP:
            if state.current_phase in (LoopPhase.BUILD, LoopPhase.VALIDATE, LoopPhase.SHIP):
                target = "s1"

        if target is None:
            raise RuntimeError(f"Routage impossible pour phase '{state.current_phase}' en mode '{state.project_mode}'.")

        # 2. Exécution Système 2 avec Circuit Breaker
        if target == "s2":
            if self.circuit_breaker:
                try:
                    self.circuit_breaker.check(state)
                except Exception as e:
                    object.__setattr__(state, "current_phase", LoopPhase.ERROR)
                    object.__setattr__(state, "current_state_id", LoopPhase.ERROR.value)
                    state.add_to_journal("orchestrator:circuit_breaker_error", str(e))
                    return state

            try:
                state.add_to_journal("orchestrator:routing", f"Délégation S2 ({self.s2_agent.name})")
                return self.s2_agent.execute(state)
            except Exception as e:
                object.__setattr__(state, "current_phase", LoopPhase.ERROR)
                object.__setattr__(state, "current_state_id", LoopPhase.ERROR.value)
                state.add_to_journal("orchestrator:s2_failure", str(e))
                return state

        # 3. Exécution Système 1 (exempt de circuit breaker)
        state.add_to_journal("orchestrator:routing", f"Délégation S1 ({self.s1_agent.name})")
        return self.s1_agent.execute(state)
