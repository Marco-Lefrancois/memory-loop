"""
Tests d'instrumentation logging pour src/pipelines/focus.py (MLOOP-141-BE / ADR-0369).
Valide que les erreurs de lecture/normalisation du frontmatter des stories
sont capturées avec stack trace et contexte métier (story_id, lock_type).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.pipelines import focus


def test_logger_bound_via_get_logger():
    """Vérifie que focus.logger est bien issu de get_logger (persistance mloop.log)."""
    assert focus.logger.name == "mloop.pipelines.focus"


def test_set_focus_normalize_read_error_logs(tmp_path):
    """
    Une story avec un frontmatter YAML corrompu doit produire un logger.error
    contextualisé (lock_type=frontmatter) sans interrompre la normalisation globale.
    """
    project_dir = tmp_path / "TestProjectFocus"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    target_story = stories_dir / "MLOOP-141-BE.md"
    target_story.write_text(
        "---\nid: MLOOP-141-BE\nstatus: OPEN\n---\n\n# Story cible\n",
        encoding="utf-8",
    )

    corrupt_story = stories_dir / "CORRUPT-001.md"
    corrupt_story.write_text(
        "---\nid: CORRUPT-001\nstatus: [unclosed\n---\n\n# Story corrompue\n",
        encoding="utf-8",
    )

    with patch.object(focus, "logger") as mock_logger:
        focus_changed = focus.set_focus(
            "TestProjectFocus", "MLOOP-141-BE.md", base_projects_dir=str(tmp_path)
        )

    assert focus_changed is True
    matching = [
        c
        for c in mock_logger.error.call_args_list
        if c.kwargs.get("extra", {}).get("lock_type") == "frontmatter"
    ]
    assert len(matching) == 1
    kwargs = matching[0].kwargs
    assert kwargs.get("exc_info") is True
    assert kwargs.get("extra", {}).get("story_id") == "MLOOP-141-BE.md"


def test_set_focus_emits_info_start_and_end(tmp_path):
    """set_focus doit émettre un log INFO de début et un log INFO de fin avec duration_ms."""
    project_dir = tmp_path / "TestProjectFocus"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    target_story = stories_dir / "MLOOP-141-BE.md"
    target_story.write_text(
        "---\nid: MLOOP-141-BE\nstatus: OPEN\n---\n\n# Story cible\n",
        encoding="utf-8",
    )

    with patch.object(focus, "logger") as mock_logger:
        focus.set_focus("TestProjectFocus", "MLOOP-141-BE.md", base_projects_dir=str(tmp_path))

    assert mock_logger.info.call_count >= 2
    last_call_kwargs = mock_logger.info.call_args_list[-1].kwargs
    assert "duration_ms" in last_call_kwargs.get("extra", {})
