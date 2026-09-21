"""
Tests d'instrumentation logging pour vibe_check.py (MLOOP-141-BE / ADR-0369).
Valide l'absence de NameError latent sur `logger` et la capture contextualisée
des erreurs des 15+ contrôles pré-vol.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.pipelines import vibe_check


def test_logger_bound_via_get_logger():
    """Vérifie que vibe_check.logger existe (corrige le NameError latent MLOOP-141-BE)."""
    assert vibe_check.logger.name == "mloop.pipelines.vibe_check"


def test_detect_lifecycle_stage_backlog_read_error_logs(tmp_path, monkeypatch):
    """Une erreur de lecture de sprint_backlog.md dans la détection de phase doit logger.error."""
    project_dir = tmp_path / "Projects" / "TestProj"
    (project_dir / "backlog").mkdir(parents=True)
    (project_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    backlog_file.write_text("| ID | Statut |\n| US-1 | OPEN |\n", encoding="utf-8")

    with (
        patch.object(vibe_check, "logger") as mock_logger,
        patch.object(Path, "read_text", side_effect=OSError("disque plein")),
    ):
        mode, stage = vibe_check.detect_project_lifecycle_stage(project_dir)

    mock_logger.error.assert_called_once()
    _, kwargs = mock_logger.error.call_args
    assert kwargs.get("exc_info") is True
    extra = kwargs.get("extra", {})
    assert extra.get("check_name") == "detect_project_lifecycle_stage"
    assert extra.get("violation_type") == "backlog_read_error"


def test_secret_leak_scan_read_error_logs_via_real_pipeline(tmp_path, monkeypatch):
    """
    Une erreur de lecture JSON lors du scan Zero-Leak (Check 7) au sein du run_vibe_check
    réel doit produire un logger.error contextualisé (check_name=secret_leak_scan).
    """
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / "Projects" / "TestProj"
    backlog_dir = project_dir / "backlog"
    backlog_dir.mkdir(parents=True)
    bad_json = backlog_dir / "leaky.json"
    bad_json.write_text("{}", encoding="utf-8")

    for rf in ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]:
        Path(rf).write_text("# Règles", encoding="utf-8")

    original_read_text = Path.read_text

    def scoped_read_text(self, *args, **kwargs):
        if self.name == "leaky.json":
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", scoped_read_text)

    with (
        patch.object(vibe_check, "logger") as mock_logger,
        patch("src.loop_mem.db.search_observations", return_value=[]),
    ):
        try:
            vibe_check.run_vibe_check("TestProj")
        except Exception:
            pass

    matching_calls = [
        call
        for call in mock_logger.error.call_args_list
        if call.kwargs.get("extra", {}).get("check_name") == "secret_leak_scan"
    ]
    assert len(matching_calls) == 1
    kwargs = matching_calls[0].kwargs
    assert kwargs.get("exc_info") is True
    assert kwargs.get("extra", {}).get("violation_type") == "file_read_error"
