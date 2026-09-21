"""
Tests d'instrumentation logging pour src/core/lifecycle.py (MLOOP-141-BE / ADR-0369).
Valide la migration vers get_logger (persistance mloop.log) et l'enrichissement
contextuel des transitions de Gate (gate, from_status, to_status, phase, duration_ms).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core import lifecycle
from src.core.lifecycle import ProjectLifecycleManager, ProjectLifecycleStage


def test_logger_bound_via_get_logger():
    """Vérifie que lifecycle.logger est bien issu de get_logger (persistance mloop.log + errors.log)."""
    assert lifecycle.logger.name == "mloop.core.lifecycle"


def test_get_state_corrupt_json_logs_warning_with_context(tmp_path):
    """Un lifecycle_state.json corrompu doit produire un logger.warning avec exc_info et contexte projet."""
    project_path = tmp_path / "Projects" / "TestProj"
    memory_dir = project_path / "memory"
    memory_dir.mkdir(parents=True)
    state_file = memory_dir / "lifecycle_state.json"
    state_file.write_text("{not valid json at all", encoding="utf-8")

    with patch.object(lifecycle, "logger") as mock_logger:
        state = ProjectLifecycleManager.get_state(project_path)

    # Ré-amorçage déterministe malgré la corruption
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_INGEST

    matching = [
        c
        for c in mock_logger.warning.call_args_list
        if c.kwargs.get("extra", {}).get("project") == "TestProj"
    ]
    assert len(matching) >= 1
    assert any(c.kwargs.get("exc_info") is True for c in matching)


def test_approve_gate_emits_info_with_from_to_status_and_duration(tmp_path):
    """approve_gate() doit émettre des logs INFO début/fin avec from_status, to_status, gate, duration_ms."""
    project_path = tmp_path / "Projects" / "TestProj"
    project_path.mkdir(parents=True)

    state = ProjectLifecycleManager.init_lifecycle(project_path)
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_INGEST

    with patch.object(lifecycle, "logger") as mock_logger:
        result_state = ProjectLifecycleManager.approve_gate(
            project_path=project_path,
            gate_number=1,
            approver="Test Approver",
            notes="Test",
        )

    assert result_state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE

    info_calls = mock_logger.info.call_args_list
    start_calls = [
        c
        for c in info_calls
        if c.kwargs.get("extra", {}).get("from_status") == "STAGE_1_INGEST"
        and "to_status" not in c.kwargs.get("extra", {})
    ]
    end_calls = [
        c
        for c in info_calls
        if c.kwargs.get("extra", {}).get("to_status") == "STAGE_2_PLAN_ANALYSE"
    ]

    assert len(start_calls) == 1
    assert len(end_calls) == 1
    assert end_calls[0].kwargs.get("extra", {}).get("gate") == 1
    assert "duration_ms" in end_calls[0].kwargs.get("extra", {})
