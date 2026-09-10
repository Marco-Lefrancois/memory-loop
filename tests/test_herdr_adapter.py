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

    resolved = resolve_project_path(
        "Metro_OneTrust", base_projects_dir=str(projects_dir)
    )
    assert resolved == proj_a

    # Case-insensitive resolution
    resolved_ci = resolve_project_path(
        "metro_onetrust", base_projects_dir=str(projects_dir)
    )
    assert resolved_ci == proj_a


@patch.object(HerdrAdapter, "ensure_server_running", return_value=True)
@patch.object(HerdrAdapter, "_exec")
def test_spawn_story_worker(mock_exec, mock_ensure, tmp_path):
    mock_exec.return_value = {
        "success": True,
        "result": {"pane": {"pane_id": "p_test_1"}},
    }

    adapter = HerdrAdapter(herdr_bin="herdr")
    res = adapter.spawn_story_worker(
        project_name="TestProject",
        story_id="US-01-TEST",
        kind="opencode",
        root_dir=str(tmp_path),
    )

    assert res["success"] is True
    assert res["worker_name"] == "worker_us_01_test"
    assert res["pane_id"] == "p_test_1"


def test_ensure_server_running_noop_when_already_up():
    """
    BUG worker-spawn auto-heal : si le serveur Herdr répond déjà 'running',
    ensure_server_running() ne doit PAS tenter de le relancer (idempotence).
    """
    adapter = HerdrAdapter(herdr_bin="herdr")
    with (
        patch.object(adapter, "_is_server_running", return_value=True) as mock_check,
        patch("subprocess.Popen") as mock_popen,
    ):
        result = adapter.ensure_server_running()
    assert result is True
    mock_check.assert_called_once()
    mock_popen.assert_not_called(), "Ne doit pas démarrer un serveur déjà en cours."


def test_ensure_server_running_starts_daemon_when_down():
    """
    BUG worker-spawn auto-heal : si le serveur Herdr est down (server_not_running),
    ensure_server_running() doit lancer 'herdr server' en arrière-plan puis re-vérifier.
    """
    adapter = HerdrAdapter(herdr_bin="herdr")
    # 1er check: down ; après démarrage: up
    check_results = [False, True]
    with (
        patch.object(
            adapter, "_is_server_running", side_effect=lambda: check_results.pop(0)
        ) as mock_check,
        patch("subprocess.Popen") as mock_popen,
        patch("time.sleep", return_value=None),
    ):
        result = adapter.ensure_server_running()
    assert result is True, "Le serveur doit être considéré running après auto-heal."
    mock_popen.assert_called_once()
    # La commande lancée doit être 'herdr server'
    launched_args = mock_popen.call_args[0][0]
    assert "server" in launched_args, (
        f"Doit lancer 'herdr server', reçu : {launched_args}"
    )


@patch.object(HerdrAdapter, "read_agent_output")
def test_harvest_story_evidence(mock_read, tmp_path):
    proj_dir = tmp_path / "Projects" / "TestProject"
    proj_dir.mkdir(parents=True)
    evidence_dir = proj_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)

    mock_read.return_value = {
        "success": True,
        "raw_output": "\x1b[32m[PASS]\x1b[0m Component validated 100%.",
    }

    adapter = HerdrAdapter(herdr_bin="herdr")
    res = adapter.harvest_story_evidence(
        project_name="TestProject", story_id="US-01-TEST", project_path=str(proj_dir)
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
                "agents": [
                    {"name": "worker_1", "agent_status": "idle", "pane_id": "p1"}
                ]
            }
        },
    }

    status_res = run_worker_status("TestProject")
    assert status_res["success"] is True

    mock_exec.return_value = {"success": True, "result": {}}
    close_res = run_worker_close("TestProject", "US-01-TEST")
    assert close_res["success"] is True


@patch.object(HerdrAdapter, "_exec")
def test_herdr_v082_primitives(mock_exec):
    adapter = HerdrAdapter(herdr_bin="herdr")

    # 1. Export Layout
    mock_exec.return_value = {"success": True, "result": {"root": {"type": "pane"}}}
    res_export = adapter.export_layout(tab_id="tab_1")
    assert res_export["success"] is True

    # 2. Apply Layout
    mock_exec.return_value = {"success": True, "result": {"type": "layout_applied"}}
    res_apply = adapter.apply_layout("ws_1", {"type": "pane"}, tab_label="dev")
    assert res_apply["success"] is True

    # 3. Report Metadata
    mock_exec.return_value = {"success": True, "result": {}}
    res_meta = adapter.report_metadata(
        pane_id="p1",
        title="Worker Story",
        tokens={"summary": "Building", "status": "INVEST_OK"},
    )
    assert res_meta["success"] is True

    # 4. Show Notification
    mock_exec.return_value = {"success": True, "result": {}}
    res_notif = adapter.show_notification(
        title="Alert", body="Test message", sound="done"
    )
    assert res_notif["success"] is True

    # 5. Explain Agent
    mock_exec.return_value = {
        "success": True,
        "result": {"matched_rule": "opencode_idle"},
    }
    res_explain = adapter.explain_agent(target="worker_1")
    assert res_explain["success"] is True

    # 6. Plugin Invoke
    mock_exec.return_value = {"success": True, "result": {}}
    res_plugin = adapter.plugin_invoke(
        "reap_zombies", plugin_id="org.mloop.orchestrator"
    )
    assert res_plugin["success"] is True


@patch.object(HerdrAdapter, "list_agents")
@patch.object(HerdrAdapter, "close_pane")
def test_audit_and_reap_zombies(mock_close, mock_list):
    adapter = HerdrAdapter(herdr_bin="herdr")
    mock_list.return_value = {
        "success": True,
        "result": {
            "agents": [
                {
                    "name": "worker_us_01",
                    "pane_id": "p_zombie_1",
                    "agent_status": "idle",
                },
                {
                    "name": "worker_us_02",
                    "pane_id": "p_zombie_2",
                    "agent_status": "done",
                },
                {
                    "name": "active_agent",
                    "pane_id": "p_active",
                    "agent_status": "working",
                },
            ]
        },
    }
    mock_close.return_value = {"success": True}

    reap_res = adapter.audit_and_reap_zombies()
    assert reap_res["success"] is True
    assert reap_res["reaped_count"] == 2
    assert mock_close.call_count == 2


@patch.object(HerdrAdapter, "_exec")
def test_read_agent_output_working_fallback(mock_exec):
    adapter = HerdrAdapter(herdr_bin="herdr")
    # First call with recent-unwrapped fails with agent_not_idle
    # Second call with visible succeeds
    mock_exec.side_effect = [
        {"success": False, "stderr": "agent_not_idle: cannot read while working"},
        {"success": True, "result": {"content": "Visible content on screen"}},
    ]

    res = adapter.read_agent_output("worker_1", source="recent-unwrapped")
    assert res["success"] is True
    assert res.get("source_fallback") == "visible"
    assert mock_exec.call_count == 2


def test_mcp_herdr_tool_dispatch():
    from src.bridges.mcp_herdr import handle_tool_call

    with patch.object(HerdrAdapter, "export_layout", return_value={"success": True}):
        res = handle_tool_call("herdr_layout_export", {"tab_id": "t1"})
        assert res["success"] is True

    with patch.object(
        HerdrAdapter, "show_notification", return_value={"success": True}
    ):
        res = handle_tool_call("herdr_notification_show", {"title": "Test Toast"})
        assert res["success"] is True

    with patch.object(
        HerdrAdapter,
        "audit_and_reap_zombies",
        return_value={"success": True, "reaped_count": 0},
    ):
        res = handle_tool_call("herdr_zombies_reap", {})
        assert res["success"] is True

    with patch.object(
        HerdrAdapter,
        "prompt_agent",
        return_value={"success": True, "delivery_status": "DELIVERED"},
    ):
        res = handle_tool_call(
            "herdr_agent_prompt",
            {"agent_name_or_pane": "worker_1", "prompt_text": "hello"},
        )
        assert res["success"] is True
        assert res["delivery_status"] == "DELIVERED"

    with patch.object(
        HerdrAdapter,
        "wait_agent",
        return_value={
            "success": True,
            "agent_status": "working",
            "completed": False,
            "timed_out": True,
        },
    ):
        res = handle_tool_call("herdr_agent_wait", {"agent_name_or_pane": "worker_1"})
        assert res["success"] is True
        assert res["agent_status"] == "working"
