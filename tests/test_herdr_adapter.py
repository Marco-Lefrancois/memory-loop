"""
test_herdr_adapter.py - Unit tests for HerdrAdapter, Bloat Filtering, and Worker Pipeline
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.core.herdr_adapter import HerdrAdapter, herdr
from src.pipelines.worker_pipeline import (
    run_worker_spawn,
    run_worker_status,
    run_worker_harvest,
    run_worker_close,
    resolve_project_path,
)


def test_filter_terminal_bloat():
    raw_terminal = (
        "\x1b[32m[INFO]\x1b[0m Starting build...\r\n"
        "⠋ Loading modules...\n"
        "⠙ Loading modules...\n"
        "\x1b[1;34mDone building component.\x1b[0m\n"
    )
    cleaned = HerdrAdapter.filter_terminal_bloat(raw_terminal)
    assert "[INFO] Starting build..." in cleaned
    assert "Done building component." in cleaned
    assert "⠋" not in cleaned
    assert "⠙" not in cleaned
    assert "\x1b" not in cleaned


def test_resolve_project_path(tmp_path):
    projects_dir = tmp_path / "Projects"
    projects_dir.mkdir()
    proj_a = projects_dir / "Metro_OneTrust"
    proj_a.mkdir()

    resolved = resolve_project_path("Metro_OneTrust", base_projects_dir=str(projects_dir))
    assert resolved == proj_a

    # Case-insensitive resolution
    resolved_ci = resolve_project_path("metro_onetrust", base_projects_dir=str(projects_dir))
    assert resolved_ci == proj_a


@patch.object(HerdrAdapter, "_exec")
def test_spawn_story_worker(mock_exec, tmp_path):
    mock_exec.return_value = {"success": True, "result": {"pane": {"pane_id": "p_test_1"}}}

    adapter = HerdrAdapter(herdr_bin="herdr")
    res = adapter.spawn_story_worker(
        project_name="TestProject",
        story_id="US-01-TEST",
        kind="opencode",
        root_dir=str(tmp_path)
    )

    assert res["success"] is True
    assert res["worker_name"] == "worker_us_01_test"
    assert res["pane_id"] == "p_test_1"


@patch.object(HerdrAdapter, "read_agent_output")
def test_harvest_story_evidence(mock_read, tmp_path):
    proj_dir = tmp_path / "Projects" / "TestProject"
    proj_dir.mkdir(parents=True)
    evidence_dir = proj_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)

    mock_read.return_value = {
        "success": True,
        "raw_output": "\x1b[32m[PASS]\x1b[0m Component validated 100%."
    }

    adapter = HerdrAdapter(herdr_bin="herdr")
    res = adapter.harvest_story_evidence(
        project_name="TestProject",
        story_id="US-01-TEST",
        project_path=str(proj_dir)
    )

    assert res["success"] is True
    assert Path(res["evidence_file"]).exists()

    data = json.loads(Path(res["evidence_file"]).read_text(encoding="utf-8"))
    assert data["story_id"] == "US-01-TEST"
    assert "Component validated 100%." in data["execution_summary"]
    assert data["harvest_status"] == "COMPLETED"


@patch.object(HerdrAdapter, "_exec")
def test_worker_pipeline_commands(mock_exec, tmp_path):
    # Test with Herdr v0.8 nested result structure
    mock_exec.return_value = {
        "success": True,
        "result": {
            "result": {
                "agents": [{"name": "worker_1", "agent_status": "idle", "pane_id": "p1"}]
            }
        }
    }

    status_res = run_worker_status("TestProject")
    assert status_res["success"] is True

    mock_exec.return_value = {"success": True, "result": {}}
    close_res = run_worker_close("TestProject", "US-01-TEST")
    assert close_res["success"] is True
