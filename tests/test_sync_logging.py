"""
Tests d'instrumentation logging pour src/pipelines/sync/ (MLOOP-141-BE / ADR-0369).
Valide que les erreurs des sous-systèmes (wikifix, graphify, fts5, hypergraph, cache,
struct, audit) sont capturées avec stack trace et contexte métier.
Le pipeline sync est désormais un package (src/pipelines/sync/) dont le point
d'entrée est run_sync dans _sync_run.py (migration MLOOP-179-BE).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.pipelines import sync
from src.state import LoopState


def test_logger_bound_via_get_logger():
    """Vérifie que sync.logger est bien issu de get_logger (persistance mloop.log)."""
    assert sync.logger.name == "mloop.pipelines.sync"


def test_load_sync_cache_corrupt_json_logs_error(tmp_path):
    """Un cache JSON corrompu doit produire un logger.error contextualisé subsystem=cache."""
    project_path = tmp_path / "Projects" / "TestProj"
    cache_dir = project_path / "memory" / "cache"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "sync_state.json"
    cache_file.write_text("{not valid json", encoding="utf-8")

    with patch.object(sync, "logger") as mock_logger:
        result = sync.load_sync_cache(project_path)

    assert result == {"stories": {}, "questions": {}}
    mock_logger.error.assert_called_once()
    _, kwargs = mock_logger.error.call_args
    assert kwargs.get("exc_info") is True
    extra = kwargs.get("extra", {})
    assert extra.get("subsystem") == "cache"


def test_run_sync_wikifix_failure_logs_error_with_subsystem(tmp_path):
    """Une panne WikiFix pendant run_sync doit logger.error avec subsystem=wikifix."""
    proj_dir = tmp_path / "Projects" / "TestProj"
    proj_dir.mkdir(parents=True)
    state = LoopState(project_name="TestProj")

    with (
        patch("src.pipelines.sync._sync_run.sync_live_reference_wikis"),
        patch("src.pipelines.sync._sync_run.sync_project_directives"),
        patch("src.pipelines.sync._sync_run.sync_sprint_backlog"),
        patch("src.pipelines.sync._sync_run.sync_open_questions"),
        patch("src.pipelines.sync._sync_run.sync_hypergraph"),
        patch(
            "src.pipelines.sync.WikiFixAgent.execute", side_effect=RuntimeError("WikiFix crashed!")
        ),
        patch("src.pipelines.sync.GraphifyAgent.execute", return_value=state),
        patch("src.state.LoopState.save_to_audit"),
        patch.object(sync, "logger") as mock_logger,
    ):
        result_state = sync.run_sync("TestProj", state, proj_dir, fast_mode=False)

    assert result_state == state
    matching = [
        c
        for c in mock_logger.error.call_args_list
        if c.kwargs.get("extra", {}).get("subsystem") == "wikifix"
    ]
    assert len(matching) == 1
    assert matching[0].kwargs.get("exc_info") is True


def test_run_sync_graphify_failure_logs_error_with_subsystem(tmp_path):
    """Une panne Graphify pendant run_sync doit logger.error avec subsystem=graphify."""
    proj_dir = tmp_path / "Projects" / "TestProj"
    proj_dir.mkdir(parents=True)
    state = LoopState(project_name="TestProj")

    with (
        patch("src.pipelines.sync._sync_run.sync_live_reference_wikis"),
        patch("src.pipelines.sync._sync_run.sync_project_directives"),
        patch("src.pipelines.sync._sync_run.sync_sprint_backlog"),
        patch("src.pipelines.sync._sync_run.sync_open_questions"),
        patch("src.pipelines.sync._sync_run.sync_hypergraph"),
        patch("src.pipelines.sync.WikiFixAgent.execute", return_value=state),
        patch(
            "src.pipelines.sync.GraphifyAgent.execute",
            side_effect=RuntimeError("Graphify crashed!"),
        ),
        patch("src.state.LoopState.save_to_audit"),
        patch.object(sync, "logger") as mock_logger,
    ):
        result_state = sync.run_sync("TestProj", state, proj_dir, fast_mode=False)

    assert result_state == state
    matching = [
        c
        for c in mock_logger.error.call_args_list
        if c.kwargs.get("extra", {}).get("subsystem") == "graphify"
    ]
    assert len(matching) == 1
    assert matching[0].kwargs.get("exc_info") is True

    # INFO début/fin du pipeline avec duration_ms doit également être émis
    info_calls = [
        c
        for c in mock_logger.info.call_args_list
        if c.kwargs.get("extra", {}).get("subsystem") == "orchestrator"
    ]
    assert len(info_calls) == 2  # début + fin
    assert "duration_ms" in info_calls[-1].kwargs.get("extra", {})
