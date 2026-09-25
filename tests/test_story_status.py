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
from src.pipelines.state_machine import (
    ALLOWED_TRANSITIONS,
    StateMachineEngine,
    StateTransitionError,
)


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


@pytest.mark.parametrize(
    "status",
    [
        StoryStatus.READY_FOR_GROOMING,
        StoryStatus.READY_FOR_DEV,
        StoryStatus.IN_DEV,
        StoryStatus.READY_FOR_QA,
        StoryStatus.IN_QA,
        StoryStatus.QA_CERTIFIED,
        StoryStatus.READY_TO_SHIP,
        StoryStatus.DONE,
        StoryStatus.ACCEPTED,
        StoryStatus.DONE_TESTED,
        StoryStatus.SHIPPED,
    ],
)
def test_grilled_true_for_human_and_downstream_statuses(status):
    """grilled == True pour les statuts validés par mLoop et en cours de livraison."""
    assert _make_item(status).grilled is True
    assert _make_item(status).jira_sync_eligible is True


@pytest.mark.parametrize(
    "status",
    [
        StoryStatus.DRAFT,
        StoryStatus.BACKLOG,
        StoryStatus.OPEN,
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_PLAN,
        StoryStatus.IN_BUILD,
        StoryStatus.IN_VALIDATE,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
)
def test_grilled_false_for_in_progress_statuses(status):
    assert _make_item(status).grilled is False
    assert _make_item(status).jira_sync_eligible is False


@pytest.mark.parametrize(
    "raw,expected_status",
    [
        ("READY_FOR_QA", "READY_FOR_QA"),
        ("ready_for_qa", "READY_FOR_QA"),
        ("ready for qa", "READY_FOR_QA"),
        ("READY-FOR-QA", "READY_FOR_QA"),
        ("QA_CERTIFIED", "QA_CERTIFIED"),
        ("qa_certified", "QA_CERTIFIED"),
        ("qa certified", "QA_CERTIFIED"),
        ("QA-CERTIFIED", "QA_CERTIFIED"),
        ("READY_TO_SHIP", "READY_TO_SHIP"),
        ("ready_to_ship", "READY_TO_SHIP"),
        ("ready to ship", "READY_TO_SHIP"),
        ("READY-TO-SHIP", "READY_TO_SHIP"),
    ],
)
def test_from_raw_new_5_phase_statuses_variants(raw, expected_status):
    """Les nouveaux statuts du cycle 5 phases doivent être reconnus avec tolérance."""
    assert StoryStatus.from_raw(raw).value == expected_status



# ─── Tests Transitions FSM ────────────────────────────────────────────────────


def test_full_client_lifecycle_transitions():
    """Vérifie le cycle complet de transitions client."""
    assert StoryStatus.READY_FOR_DEV in ALLOWED_TRANSITIONS[StoryStatus.READY_FOR_GROOMING]
    assert StoryStatus.IN_DEV in ALLOWED_TRANSITIONS[StoryStatus.READY_FOR_DEV]
    assert StoryStatus.IN_QA in ALLOWED_TRANSITIONS[StoryStatus.IN_DEV]
    assert StoryStatus.ACCEPTED in ALLOWED_TRANSITIONS[StoryStatus.IN_QA]


# ─── MLOOP-FIX-C1C2 (C1) — Statut DONE_TESTED ────────────────────────────────
# SSOT : standards/protocols/STORY_LIFECYCLE_PROTOCOL.md
#   L16 (chaîne unifiée), L35 (statut auto-positionnable IA),
#   L63-70 (§E IN_DEV→DONE_TESTED, §F DONE_TESTED→SHIPPED),
#   L90-95 (§3.2 rétrogradation via IN_REVIEW, re-progression par IN_DEV).


@pytest.mark.parametrize("raw", ["DONE_TESTED", "done_tested", "done tested", "DONE-TESTED"])
def test_from_raw_done_tested_variants(raw):
    """DONE_TESTED doit être reconnu par from_raw (toutes variantes normalisées)."""
    assert StoryStatus.from_raw(raw) == StoryStatus.DONE_TESTED


def test_done_tested_allowed_transitions_fsm():
    """FSM : entrée §E depuis IN_DEV ; sorties §F + §3.2 — aucune autre liste touchée."""
    assert StoryStatus.DONE_TESTED in ALLOWED_TRANSITIONS[StoryStatus.IN_DEV]
    assert ALLOWED_TRANSITIONS[StoryStatus.DONE_TESTED] == [
        StoryStatus.SHIPPED,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_DEV,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ]
    # Aucun accès direct illicite : DRAFT et IN_REVIEW ne mènent pas à DONE_TESTED.
    assert StoryStatus.DONE_TESTED not in ALLOWED_TRANSITIONS[StoryStatus.DRAFT]
    assert StoryStatus.DONE_TESTED not in ALLOWED_TRANSITIONS[StoryStatus.IN_REVIEW]


def test_done_tested_illicit_transition_raises():
    """Une transition DRAFT → DONE_TESTED doit lever StateTransitionError (FSM bloquante)."""
    engine = StateMachineEngine(".")
    with pytest.raises(StateTransitionError):
        engine.validate_transition(StoryStatus.DRAFT, StoryStatus.DONE_TESTED)


def test_done_tested_is_grilled_and_jira_sync_eligible():
    """Un récit DONE_TESTED est considéré grilled ET éligible à la sync Jira."""
    item = _make_item(StoryStatus.DONE_TESTED)
    assert item.grilled is True
    assert item.jira_sync_eligible is True
