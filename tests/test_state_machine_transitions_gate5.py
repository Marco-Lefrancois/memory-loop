"""
Tests unitaires pour MLOOP-312-BE :
Graphe de Transitions Déterministe & Auto-Clôture Gate 5 sans Validation Humaine
"""

import pytest
from src.pipelines.state_machine import StateMachineEngine, StateTransitionError
from src.state import StoryStatus
from src.core.lifecycle._lc_models import GATE_DEFINITIONS


def test_gate5_does_not_require_human():
    """CA-5 : GATE_DEFINITIONS[5]['requires_human'] est configuré à False."""
    assert GATE_DEFINITIONS[5]["requires_human"] is False


def test_allowed_transitions_5_phases():
    """CA-1, CA-2, CA-3, CA-4 : Enchaînement nominal et rétrogradation des 5 phases."""
    engine = StateMachineEngine(".")

    # CA-1 : IN_DEV -> READY_FOR_QA
    assert engine.validate_transition(StoryStatus.IN_DEV, StoryStatus.READY_FOR_QA) is True
    assert engine.validate_transition("IN_DEV", "READY_FOR_QA") is True

    # CA-2 : READY_FOR_QA -> QA_CERTIFIED
    assert engine.validate_transition(StoryStatus.READY_FOR_QA, StoryStatus.QA_CERTIFIED) is True
    assert engine.validate_transition("READY_FOR_QA", "QA_CERTIFIED") is True

    # CA-3 : Rétrogradation directe READY_FOR_QA -> IN_DEV en cas d'échec
    assert engine.validate_transition(StoryStatus.READY_FOR_QA, StoryStatus.IN_DEV) is True
    assert engine.validate_transition("READY_FOR_QA", "IN_DEV") is True

    # CA-4 : QA_CERTIFIED -> DONE autonome
    assert engine.validate_transition(StoryStatus.QA_CERTIFIED, StoryStatus.DONE) is True
    assert engine.validate_transition("QA_CERTIFIED", "DONE") is True

    # Passage intermédiaire READY_TO_SHIP
    assert engine.validate_transition(StoryStatus.QA_CERTIFIED, StoryStatus.READY_TO_SHIP) is True
    assert engine.validate_transition(StoryStatus.READY_TO_SHIP, StoryStatus.DONE) is True


def test_illegal_transitions_raise_error():
    """CA-6 : Tout saut illégitime lève immédiatement StateTransitionError."""
    engine = StateMachineEngine(".")

    # DRAFT -> READY_FOR_QA
    with pytest.raises(StateTransitionError, match=r"\[FSM BLOQUANT\]"):
        engine.validate_transition(StoryStatus.DRAFT, StoryStatus.READY_FOR_QA)

    # IN_ANALYZE -> DONE
    with pytest.raises(StateTransitionError, match=r"\[FSM BLOQUANT\]"):
        engine.validate_transition(StoryStatus.IN_ANALYZE, StoryStatus.DONE)

    # DRAFT -> DONE
    with pytest.raises(StateTransitionError, match=r"\[FSM BLOQUANT\]"):
        engine.validate_transition("DRAFT", "DONE")

    # READY_FOR_DEV -> DONE (saut de phase BUILD + QA)
    with pytest.raises(StateTransitionError, match=r"\[FSM BLOQUANT\]"):
        engine.validate_transition(StoryStatus.READY_FOR_DEV, StoryStatus.DONE)
