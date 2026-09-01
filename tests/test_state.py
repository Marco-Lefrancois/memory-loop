"""
Tests unitaires — LoopState + ProjectMode FSM (MLOOP-002-BE refactor).

Couvre :
- Workflow nominal en mode MLOOP (5 phases)
- Workflow nominal en mode CLIENT (3 phases SPEC/PLAN/VALIDATE)
- Transitions interdites par mode
- Gardes d'intégrité (AnalysisResult, PlanResult, missing_information)
- Circuit Breaker (max révisions en mode MLOOP)
"""
import pytest
from src.state import (
    LoopState,
    LoopPhase,
    ProjectMode,
    AnalysisResult,
    PlanResult,
    PlanStep,
    QAReport,
    IntegrityError,
    MaxRevisionsReached,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _analysis() -> AnalysisResult:
    return AnalysisResult(intent="test", constraints=[], missing_information=[])


def _plan() -> PlanResult:
    return PlanResult(steps=[PlanStep(step_id=1, action="run", expected_output="ok")])


# ─── Mode MLOOP : Workflow complet 5 phases ───────────────────────────────────

def test_mloop_nominal_workflow():
    """Cycle complet MLOOP : SPEC → PLAN → BUILD → VALIDATE → SHIP."""
    state = LoopState(project_name="TestProject", project_mode=ProjectMode.MLOOP)
    assert state.current_phase == LoopPhase.SPEC

    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)
    assert state.current_phase == LoopPhase.PLAN

    state.plan = _plan()
    state.transition_to(LoopPhase.BUILD)
    assert state.current_phase == LoopPhase.BUILD

    state.qa_report = QAReport(is_valid=True, score=1.0)
    state.transition_to(LoopPhase.VALIDATE)
    assert state.current_phase == LoopPhase.VALIDATE

    state.transition_to(LoopPhase.SHIP)
    assert state.current_phase == LoopPhase.SHIP


def test_mloop_validate_can_loop_back_to_plan():
    """En mode MLOOP, VALIDATE → PLAN (boucle de révision) est autorisé."""
    state = LoopState(project_name="TestProject", project_mode=ProjectMode.MLOOP)
    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)
    state.plan = _plan()
    state.transition_to(LoopPhase.BUILD)
    state.transition_to(LoopPhase.VALIDATE)

    # La boucle de révision est permise (circuit breaker pas encore déclenché)
    assert state.can_transition_to(LoopPhase.PLAN) is True


# ─── Mode CLIENT : Workflow linéaire 3 phases ─────────────────────────────────

def test_client_nominal_workflow():
    """Cycle CLIENT : SPEC → PLAN → VALIDATE (audit backlog). Linéaire, sans boucle."""
    state = LoopState(project_name="ClientProject", project_mode=ProjectMode.CLIENT)
    assert state.current_phase == LoopPhase.SPEC

    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)
    assert state.current_phase == LoopPhase.PLAN

    state.plan = _plan()
    state.transition_to(LoopPhase.VALIDATE)
    assert state.current_phase == LoopPhase.VALIDATE


def test_client_validate_is_terminal():
    """En mode CLIENT, VALIDATE est terminal : aucune transition valide sauf ERROR."""
    state = LoopState(project_name="ClientProject", project_mode=ProjectMode.CLIENT)
    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)
    state.plan = _plan()
    state.transition_to(LoopPhase.VALIDATE)

    # Aucune transition de suite n'est valide hormis ERROR
    assert state.can_transition_to(LoopPhase.PLAN) is False
    assert state.can_transition_to(LoopPhase.SHIP) is False
    assert state.can_transition_to(LoopPhase.BUILD) is False
    assert state.can_transition_to(LoopPhase.ERROR) is True


def test_client_build_is_forbidden():
    """En mode CLIENT, la transition PLAN → BUILD doit lever ValueError."""
    state = LoopState(project_name="ClientProject", project_mode=ProjectMode.CLIENT)
    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)

    with pytest.raises(ValueError, match="Transition de phase invalide"):
        state.transition_to(LoopPhase.BUILD)


def test_client_ship_is_forbidden():
    """En mode CLIENT, SHIP n'est jamais accessible depuis aucune phase."""
    state = LoopState(project_name="ClientProject", project_mode=ProjectMode.CLIENT)
    assert state.can_transition_to(LoopPhase.SHIP) is False


def test_default_project_mode_is_client():
    """Le mode par défaut d'un LoopState est CLIENT."""
    state = LoopState(project_name="AnyProject")
    assert state.project_mode == ProjectMode.CLIENT


# ─── Gardes d'intégrité (inchangées, vérifiées dans les deux modes) ──────────

def test_invalid_transitions():
    """Saut direct SPEC → VALIDATE invalide en mode CLIENT (défaut)."""
    state = LoopState(project_name="TestProject")
    with pytest.raises(ValueError, match="Transition de phase invalide"):
        state.transition_to(LoopPhase.VALIDATE)


def test_integrity_error_missing_analysis():
    state = LoopState(project_name="TestProject")
    with pytest.raises(IntegrityError, match="AnalysisResult"):
        state.transition_to(LoopPhase.PLAN)


def test_integrity_error_missing_info():
    state = LoopState(project_name="TestProject")
    state.analysis = AnalysisResult(intent="test", missing_information=["Where?"])
    with pytest.raises(IntegrityError, match="informations manquantes"):
        state.transition_to(LoopPhase.PLAN)


def test_integrity_error_missing_plan():
    state = LoopState(project_name="TestProject")
    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)
    with pytest.raises(IntegrityError, match="PlanResult"):
        state.transition_to(LoopPhase.VALIDATE)


def test_circuit_breaker_max_revisions():
    """Circuit breaker MLOOP : > 5 révisions en VALIDATE → PLAN → ERROR."""
    state = LoopState(project_name="TestProject", project_mode=ProjectMode.MLOOP)
    state.analysis = _analysis()
    state.transition_to(LoopPhase.PLAN)
    state.plan = _plan()
    state.transition_to(LoopPhase.BUILD)
    state.transition_to(LoopPhase.VALIDATE)
    state.qa_report = QAReport(is_valid=False, revisions_count=6)

    with pytest.raises(MaxRevisionsReached, match="Circuit Breaker"):
        state.transition_to(LoopPhase.PLAN)
    assert state.current_phase == LoopPhase.ERROR
