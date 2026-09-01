import pytest
import shutil
from pathlib import Path
from src.state import StoryStatus, SprintBacklogItem
from src.pipelines.state_machine import (
    StateMachineEngine,
    StateTransitionError,
    ContentTamperingError,
    ALLOWED_TRANSITIONS,
)


@pytest.fixture
def temp_project_dir(tmp_path):
    """Crée un répertoire temporaire simulant un projet sous Projects/<nom>."""
    proj_dir = tmp_path / "Projects" / "TestInReviewProject"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj_dir / "backlog" / "reviews").mkdir(parents=True, exist_ok=True)
    yield proj_dir
    if proj_dir.exists():
        shutil.rmtree(proj_dir.parent.parent, ignore_errors=True)


def test_in_review_enum_parsing():
    """Vérifie le parsing tolérant de IN_REVIEW."""
    assert StoryStatus.from_raw("IN_REVIEW") == StoryStatus.IN_REVIEW
    assert StoryStatus.from_raw("in review") == StoryStatus.IN_REVIEW
    assert StoryStatus.from_raw("in-review") == StoryStatus.IN_REVIEW
    assert StoryStatus.from_raw("IN_review") == StoryStatus.IN_REVIEW


def test_in_review_sprint_backlog_item_properties():
    """Vérifie que IN_REVIEW est éligible à la synchro Jira et est considéré comme grilled."""
    item = SprintBacklogItem(
        id="US-01",
        title="Test Story",
        description="backlog/stories/US-01.md",
        status=StoryStatus.IN_REVIEW
    )
    assert item.grilled is True
    assert item.jira_sync_eligible is True


def test_in_review_transitions(temp_project_dir):
    """Vérifie les transitions bidirectionnelles entre READY_* et IN_REVIEW."""
    engine = StateMachineEngine(str(temp_project_dir))

    # READY_FOR_DEV -> IN_REVIEW -> READY_FOR_DEV
    assert engine.validate_transition(StoryStatus.READY_FOR_DEV, StoryStatus.IN_REVIEW) is True
    assert engine.validate_transition(StoryStatus.IN_REVIEW, StoryStatus.READY_FOR_DEV) is True

    # READY_FOR_GROOMING -> IN_REVIEW -> READY_FOR_GROOMING
    assert engine.validate_transition(StoryStatus.READY_FOR_GROOMING, StoryStatus.IN_REVIEW) is True
    assert engine.validate_transition(StoryStatus.IN_REVIEW, StoryStatus.READY_FOR_GROOMING) is True

    # OPEN / IN_ANALYZE -> IN_REVIEW
    assert engine.validate_transition(StoryStatus.OPEN, StoryStatus.IN_REVIEW) is True
    assert engine.validate_transition(StoryStatus.IN_ANALYZE, StoryStatus.IN_REVIEW) is True


def test_anti_tampering_bypassed_in_review(temp_project_dir):
    """Vérifie que l'édition de contenu en statut IN_REVIEW ne déclenche pas d'erreur Anti-Tampering."""
    engine = StateMachineEngine(str(temp_project_dir))
    story_file = temp_project_dir / "backlog" / "stories" / "US-01.md"

    # Initialement validé avec hash
    story_content = (
        "---\n"
        "id: US-01\n"
        "status: IN_REVIEW\n"
        "content_hash: initialhash123\n"
        "---\n"
        "# Titre Initial\n\n"
        "Contenu modifié avec nouvelles informations métier.\n"
    )
    story_file.write_text(story_content, encoding="utf-8")

    # En mode IN_REVIEW, validate_content_integrity doit retourner True sans exception
    assert engine.validate_content_integrity(story_file) is True


def test_multi_story_in_review_allowed(temp_project_dir):
    """Vérifie que plusieurs stories peuvent être simultanément en IN_REVIEW sans violer la règle mono-IN_ANALYZE."""
    engine = StateMachineEngine(str(temp_project_dir))
    
    story1 = temp_project_dir / "backlog" / "stories" / "US-01.md"
    story1.write_text("---\nid: US-01\nstatus: IN_REVIEW\n---\n# Story 1", encoding="utf-8")

    story2 = temp_project_dir / "backlog" / "stories" / "US-02.md"
    story2.write_text("---\nid: US-02\nstatus: IN_REVIEW\n---\n# Story 2", encoding="utf-8")

    # Ne doit pas lever d'erreur (contrairement à 2 stories en IN_ANALYZE)
    in_analyze = engine.validate_single_in_analyze()
    assert len(in_analyze) == 0


def test_restamp_hash_on_ready(temp_project_dir):
    """Vérifie que le hash est recalculé et injecté lors du passage en READY_FOR_DEV."""
    engine = StateMachineEngine(str(temp_project_dir))
    story_file = temp_project_dir / "backlog" / "stories" / "US-01.md"

    story_content = (
        "---\n"
        "id: US-01\n"
        "status: READY_FOR_DEV\n"
        "---\n"
        "# Titre Mis à Jour\n\n"
        "Nouvelles exigences 4 piliers Gherkin.\n"
    )
    story_file.write_text(story_content, encoding="utf-8")

    new_hash = engine.stamp_content_hash(story_file)
    assert new_hash is not None
    assert len(new_hash) == 16

    # Relire et valider l'intégrité
    assert engine.validate_content_integrity(story_file) is True
