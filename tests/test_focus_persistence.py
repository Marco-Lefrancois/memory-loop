"""
Tests TDD pour la persistance du focus (MLOOP-107-BE).
Vérifie que la transition IN_ANALYZE est correctement persistée dans le frontmatter
et que le verdict de succès n'est émis que si la transition est effectivement effectuée.
"""

import pytest
import yaml
from pathlib import Path

from src.pipelines.focus import set_focus
from src.state import StoryStatus


def _create_project_with_story(
    tmp_path: Path, story_id: str = "MLOOP-107-BE", status: str = "OPEN"
) -> Path:
    """Crée un projet test avec une story au statut donné."""
    project_dir = tmp_path / "TestProjectFocus"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    story_file = stories_dir / f"{story_id}.md"
    story_content = f"""---
id: {story_id}
jira_key: ""
status: {status}
---

# Story de Test {story_id}

## Scénarios de test
"""
    story_file.write_text(story_content, encoding="utf-8")
    return project_dir


def _read_story_status(project_dir: Path, story_id: str) -> str:
    """Lit le statut actuel d'une story depuis son frontmatter."""
    story_file = project_dir / "backlog" / "stories" / f"{story_id}.md"
    text = story_file.read_text(encoding="utf-8")
    assert text.startswith("---"), "Le fichier ne commence pas par un frontmatter YAML"
    parts = text.split("---", 2)
    assert len(parts) >= 3, "Frontmatter YAML invalide"
    data = yaml.safe_load(parts[1])
    return data.get("status", "")


def test_focus_persists_in_analyze_status(tmp_path):
    """Vérifie que focus --story MLOOP-107-BE persiste le statut IN_ANALYZE."""
    project_dir = _create_project_with_story(tmp_path, status="OPEN")

    # Exécuter le focus
    set_focus(project_dir.name, "MLOOP-107-BE", base_projects_dir=str(tmp_path))

    # Vérifier que le statut est bien IN_ANALYZE
    status = _read_story_status(project_dir, "MLOOP-107-BE")
    assert status == StoryStatus.IN_ANALYZE.value


def test_focus_without_md_extension(tmp_path):
    """Vérifie que focus fonctionne même sans l'extension .md."""
    project_dir = _create_project_with_story(tmp_path, status="OPEN")

    # Exécuter le focus sans .md
    set_focus(project_dir.name, "MLOOP-107-BE", base_projects_dir=str(tmp_path))

    # Vérifier que le statut est bien IN_ANALYZE
    status = _read_story_status(project_dir, "MLOOP-107-BE")
    assert status == StoryStatus.IN_ANALYZE.value


def test_focus_idempotent_when_already_in_analyze(tmp_path):
    """Vérifie que focus est idempotent quand la story est déjà IN_ANALYZE."""
    project_dir = _create_project_with_story(tmp_path, status="IN_ANALYZE")

    # Exécuter le focus (devrait fonctionner sans erreur)
    result = set_focus(project_dir.name, "MLOOP-107-BE", base_projects_dir=str(tmp_path))

    # Vérifier que le statut est toujours IN_ANALYZE
    status = _read_story_status(project_dir, "MLOOP-107-BE")
    assert status == StoryStatus.IN_ANALYZE.value


def test_focus_releases_other_stories(tmp_path):
    """Vérifie que focus relâche les autres stories IN_ANALYZE."""
    # Créer deux stories
    project_dir = tmp_path / "TestProjectFocus"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    # Story 1 déjà IN_ANALYZE
    story1_file = stories_dir / "STORY-001.md"
    story1_content = """---
id: STORY-001
status: IN_ANALYZE
---

# Story 1
"""
    story1_file.write_text(story1_content, encoding="utf-8")

    # Story 2 en OPEN
    story2_file = stories_dir / "STORY-002.md"
    story2_content = """---
id: STORY-002
status: OPEN
---

# Story 2
"""
    story2_file.write_text(story2_content, encoding="utf-8")

    # Focus sur Story 2
    set_focus(project_dir.name, "STORY-002", base_projects_dir=str(tmp_path))

    # Vérifier que Story 1 est relâchée en OPEN
    status1 = _read_story_status(project_dir, "STORY-001")
    assert status1 == StoryStatus.OPEN.value, f"Story 1 devrait être OPEN, est {status1}"

    # Vérifier que Story 2 est IN_ANALYZE
    status2 = _read_story_status(project_dir, "STORY-002")
    assert status2 == StoryStatus.IN_ANALYZE.value


def test_focus_nonexistent_story_raises_error(tmp_path):
    """Vérifie que focus sur une story inexistante lève une erreur quand aucune story n'existe."""
    project_dir = tmp_path / "TestProjectEmpty"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(FileNotFoundError):
        set_focus(project_dir.name, "TOTALLY-INVALID-STORY", base_projects_dir=str(tmp_path))


def test_focus_preserves_frontmatter_structure(tmp_path):
    """Vérifie que focus préserve la structure du frontmatter YAML."""
    project_dir = _create_project_with_story(tmp_path, status="OPEN")
    story_file = project_dir / "backlog" / "stories" / "MLOOP-107-BE.md"

    # Lire le contenu original
    original_content = story_file.read_text(encoding="utf-8")

    # Exécuter le focus
    set_focus(project_dir.name, "MLOOP-107-BE", base_projects_dir=str(tmp_path))

    # Lire le contenu modifié
    modified_content = story_file.read_text(encoding="utf-8")

    # Vérifier que le YAML est valide
    assert modified_content.startswith("---")
    parts = modified_content.split("---", 2)
    assert len(parts) >= 3
    data = yaml.safe_load(parts[1])
    assert isinstance(data, dict)

    # Vérifier que le corps Markdown est préservé
    assert parts[2].strip() == original_content.split("---", 2)[2].strip()


def test_focus_verdict_shows_transition_when_new(tmp_path, capsys):
    """Vérifie que le verdict affiche 'positionné' quand la transition est nouvelle."""
    project_dir = _create_project_with_story(tmp_path, status="OPEN")

    set_focus(project_dir.name, "MLOOP-107-BE", base_projects_dir=str(tmp_path))

    captured = capsys.readouterr()
    assert "positionné au statut IN_ANALYZE" in captured.out


def test_focus_verdict_shows_idempotent_when_already_focused(tmp_path, capsys):
    """Vérifie que le verdict affiche 'idempotent' quand la story est déjà IN_ANALYZE."""
    project_dir = _create_project_with_story(tmp_path, status="IN_ANALYZE")

    set_focus(project_dir.name, "MLOOP-107-BE", base_projects_dir=str(tmp_path))

    captured = capsys.readouterr()
    assert "déjà au statut IN_ANALYZE (idempotent)" in captured.out
