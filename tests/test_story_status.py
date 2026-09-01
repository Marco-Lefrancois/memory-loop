"""
Tests unitaires — StoryStatus & StoryType enums.

Couvre :
1. Parsing nominal depuis le frontmatter YAML (case-insensitive).
2. Fail-open sur valeur inconnue → OPEN / FEATURE.
3. Normalisation des variantes (espaces, tirets, casse).
4. Propriété grilled : True pour READY_FOR_GROOMING, READY_FOR_DEV, IN_DEV, IN_QA, DONE, ACCEPTED.
5. SprintBacklogItem.status et SprintBacklogItem.type correctement typés.
6. StoryType.from_raw() pour Feature, Architecture, Technical_Debt, Bug, Spike.
"""
import pytest
from src.state import StoryStatus, StoryType, SprintBacklogItem
from src.pipelines.state_machine import StateMachineEngine, ALLOWED_TRANSITIONS


# ─── Tests StoryType.from_raw() ───────────────────────────────────────────────

def test_story_type_from_raw():
    assert StoryType.from_raw("Feature") == StoryType.FEATURE
    assert StoryType.from_raw("feature") == StoryType.FEATURE
    assert StoryType.from_raw("Architecture") == StoryType.ARCHITECTURE
    assert StoryType.from_raw("architecture") == StoryType.ARCHITECTURE
    assert StoryType.from_raw("technical_debt") == StoryType.TECHNICAL_DEBT
    assert StoryType.from_raw("Technical_Debt") == StoryType.TECHNICAL_DEBT
    assert StoryType.from_raw("tech_debt") == StoryType.TECHNICAL_DEBT
    assert StoryType.from_raw("bug") == StoryType.BUG
    assert StoryType.from_raw("spike") == StoryType.SPIKE
    assert StoryType.from_raw("") == StoryType.FEATURE
    assert StoryType.from_raw("unknown_type") == StoryType.FEATURE


# ─── Tests StoryStatus.from_raw() ─────────────────────────────────────────────

def test_from_raw_exact_match():
    assert StoryStatus.from_raw("SHIPPED") == StoryStatus.SHIPPED
    assert StoryStatus.from_raw("ACCEPTED") == StoryStatus.ACCEPTED
    assert StoryStatus.from_raw("DONE") == StoryStatus.DONE
    assert StoryStatus.from_raw("IN_DEV") == StoryStatus.IN_DEV
    assert StoryStatus.from_raw("IN_QA") == StoryStatus.IN_QA


def test_from_raw_case_insensitive():
    assert StoryStatus.from_raw("shipped") == StoryStatus.SHIPPED
    assert StoryStatus.from_raw("In_Analyze") == StoryStatus.IN_ANALYZE
    assert StoryStatus.from_raw("ready_for_grooming") == StoryStatus.READY_FOR_GROOMING
    assert StoryStatus.from_raw("in_dev") == StoryStatus.IN_DEV
    assert StoryStatus.from_raw("accepted") == StoryStatus.ACCEPTED


def test_from_raw_spaces_normalized():
    """Les variantes avec espaces du frontmatter YAML doivent être normalisées."""
    assert StoryStatus.from_raw("ready for grooming") == StoryStatus.READY_FOR_GROOMING
    assert StoryStatus.from_raw("ready for dev") == StoryStatus.READY_FOR_DEV
    assert StoryStatus.from_raw("in analyze") == StoryStatus.IN_ANALYZE
    assert StoryStatus.from_raw("in dev") == StoryStatus.IN_DEV
    assert StoryStatus.from_raw("in qa") == StoryStatus.IN_QA


def test_from_raw_hyphens_normalized():
    assert StoryStatus.from_raw("IN-ANALYZE") == StoryStatus.IN_ANALYZE
    assert StoryStatus.from_raw("READY-FOR-GROOMING") == StoryStatus.READY_FOR_GROOMING
    assert StoryStatus.from_raw("IN-DEV") == StoryStatus.IN_DEV


def test_from_raw_unknown_returns_open():
    """Valeur inconnue → OPEN (fail-open, pas d'exception)."""
    assert StoryStatus.from_raw("WHATEVER") == StoryStatus.OPEN
    assert StoryStatus.from_raw("") == StoryStatus.OPEN
    assert StoryStatus.from_raw("123") == StoryStatus.OPEN


def test_all_statuses_parseable():
    """Chaque valeur de l'enum doit être parseable par from_raw()."""
    for s in StoryStatus:
        assert StoryStatus.from_raw(s.value) == s


# ─── Tests SprintBacklogItem ──────────────────────────────────────────────────

def _make_item(status: StoryStatus, story_type: StoryType = StoryType.FEATURE) -> SprintBacklogItem:
    return SprintBacklogItem(
        id="TEST-001",
        title="Test",
        description="test.md",
        type=story_type,
        status=status,
    )


def test_sprint_item_default_status_and_type():
    item = SprintBacklogItem(id="X", title="T", description="d")
    assert item.status == StoryStatus.OPEN
    assert item.type == StoryType.FEATURE


@pytest.mark.parametrize("status", [
    StoryStatus.READY_FOR_GROOMING, StoryStatus.READY_FOR_DEV,
    StoryStatus.IN_DEV, StoryStatus.IN_QA, StoryStatus.DONE, StoryStatus.ACCEPTED
])
def test_grilled_true_for_human_and_downstream_statuses(status):
    """grilled == True pour les statuts validés par mLoop et en cours de livraison."""
    assert _make_item(status).grilled is True


@pytest.mark.parametrize("status", [
    StoryStatus.OPEN, StoryStatus.IN_ANALYZE, StoryStatus.IN_PLAN,
    StoryStatus.IN_BUILD, StoryStatus.IN_VALIDATE, StoryStatus.SHIPPED, StoryStatus.ERROR,
])
def test_grilled_false_for_in_progress_statuses(status):
    assert _make_item(status).grilled is False


# ─── Tests Transitions FSM ────────────────────────────────────────────────────

def test_full_client_lifecycle_transitions():
    """Vérifie le cycle complet de transitions client."""
    assert StoryStatus.READY_FOR_DEV in ALLOWED_TRANSITIONS[StoryStatus.READY_FOR_GROOMING]
    assert StoryStatus.IN_DEV in ALLOWED_TRANSITIONS[StoryStatus.READY_FOR_DEV]
    assert StoryStatus.IN_QA in ALLOWED_TRANSITIONS[StoryStatus.IN_DEV]
    assert StoryStatus.ACCEPTED in ALLOWED_TRANSITIONS[StoryStatus.IN_QA]

