"""
Tests unitaires — AsymmetricOrchestrator (MLOOP-002-BE refactor ProjectMode).

Valide :
1. Routage vers S2 en SPEC/PLAN (commun aux deux modes).
2. Routage vers S1 en VALIDATE mode CLIENT.
3. Routage vers S1 en BUILD/VALIDATE/SHIP mode MLOOP.
4. RuntimeError si BUILD/SHIP appelé en mode CLIENT.
5. Panne S2 → bascule ERROR.
6. Journalisation du routage.
7. Phase ERROR → aucun agent invoqué.
"""
import pytest
from src.state import LoopState, LoopPhase, ProjectMode
from src.agents.base import BaseAgent
from src.agents.orchestrator import AsymmetricOrchestrator


# ─── Doubles de test ──────────────────────────────────────────────────────────

class _TrackingAgent(BaseAgent):
    def __init__(self, label: str) -> None:
        self._label = label
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._label

    def execute(self, state: LoopState) -> LoopState:
        self.call_count += 1
        return state


class _FailingAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "failing_s2"

    def execute(self, state: LoopState) -> LoopState:
        raise ConnectionError("Timeout API NMedia Cloud.")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_state(phase: LoopPhase, mode: ProjectMode = ProjectMode.CLIENT) -> LoopState:
    state = LoopState(project_name="test-orchestrator", project_mode=mode)
    object.__setattr__(state, "current_phase", phase)
    object.__setattr__(state, "current_state_id", phase.value)
    return state


# ─── Tests communs (S2 pour SPEC/PLAN) ───────────────────────────────────────

@pytest.mark.parametrize("phase", [LoopPhase.SPEC, LoopPhase.PLAN])
@pytest.mark.parametrize("mode", [ProjectMode.CLIENT, ProjectMode.MLOOP])
def test_spec_plan_always_routed_to_s2(phase, mode):
    """SPEC et PLAN sont routés vers S2 dans les deux modes."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    orch.execute_step(_make_state(phase, mode))

    assert s2.call_count == 1
    assert s1.call_count == 0


# ─── Tests mode CLIENT ────────────────────────────────────────────────────────

def test_client_validate_routed_to_s1():
    """En mode CLIENT, VALIDATE (audit WikiFix backlog) est délégué à S1."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    orch.execute_step(_make_state(LoopPhase.VALIDATE, ProjectMode.CLIENT))

    assert s1.call_count == 1
    assert s2.call_count == 0


def test_client_build_raises_runtime_error():
    """En mode CLIENT, tenter d'exécuter BUILD doit lever RuntimeError."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    with pytest.raises(RuntimeError, match="non routeable en mode 'client'"):
        orch.execute_step(_make_state(LoopPhase.BUILD, ProjectMode.CLIENT))


def test_client_ship_raises_runtime_error():
    """En mode CLIENT, tenter d'exécuter SHIP doit lever RuntimeError."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    with pytest.raises(RuntimeError, match="non routeable en mode 'client'"):
        orch.execute_step(_make_state(LoopPhase.SHIP, ProjectMode.CLIENT))


# ─── Tests mode MLOOP ────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase", [LoopPhase.BUILD, LoopPhase.VALIDATE, LoopPhase.SHIP])
def test_mloop_s1_phases_routed_correctly(phase):
    """En mode MLOOP, BUILD/VALIDATE/SHIP sont routés vers S1 uniquement."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    orch.execute_step(_make_state(phase, ProjectMode.MLOOP))

    assert s1.call_count == 1
    assert s2.call_count == 0


# ─── Tests généraux ──────────────────────────────────────────────────────────

def test_s2_failure_transitions_to_error():
    """Panne S2 → bascule automatique en ERROR (circuit breaker LLM)."""
    s1 = _TrackingAgent("s1")
    orch = AsymmetricOrchestrator(s1, _FailingAgent())

    result = orch.execute_step(_make_state(LoopPhase.SPEC, ProjectMode.CLIENT))

    assert result.current_phase == LoopPhase.ERROR
    assert result.current_state_id == LoopPhase.ERROR.value


def test_routing_logged_in_journal():
    """Chaque délégation doit apparaître dans le journal."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    state = _make_state(LoopPhase.PLAN, ProjectMode.CLIENT)
    orch.execute_step(state)

    assert any("orchestrator" in e.event for e in state.journal)


def test_error_phase_no_delegation():
    """Phase ERROR → aucun agent n'est invoqué."""
    s1 = _TrackingAgent("s1")
    s2 = _TrackingAgent("s2")
    orch = AsymmetricOrchestrator(s1, s2)

    orch.execute_step(_make_state(LoopPhase.ERROR, ProjectMode.MLOOP))

    assert s1.call_count == 0
    assert s2.call_count == 0
