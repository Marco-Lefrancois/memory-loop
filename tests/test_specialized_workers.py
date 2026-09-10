"""
test_specialized_workers.py - Unit tests for the 5 Specialized Worker Pipelines (ADR-0346)
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.pipelines.delegation import (
    run_handoff_simulator,
    run_legacy_miner,
    run_shadow_estimator,
    run_visual_dissector,
    run_semantic_janitor,
    SemanticJanitorWatcher,
)


@pytest.fixture
def dummy_project(tmp_path):
    proj = tmp_path / "Projects" / "TestSpecial"
    proj.mkdir(parents=True)
    stories_dir = proj / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    story_file = stories_dir / "US-01.md"
    story_file.write_text(
        "---\n"
        "id: US-01\n"
        "jira_key: US-01\n"
        "title: Authentification Utilisateur\n"
        "layer: backend\n"
        "type: feature\n"
        "status: IN_ANALYZE\n"
        "---\n\n"
        "# Authentification Utilisateur\n\n"
        "## Description du besoin métier\n"
        "Permettre la connexion sécurisée.\n\n"
        "## Critères d'acceptation\n"
        "- Token JWT retourné\n\n"
        "## Scénarios de test\n"
        "### 1. Nominal\n"
        "Étant donné des identifiants valides...\n",
        encoding="utf-8"
    )

    # Legacy mock
    legacy_dir = tmp_path / "legacy_code"
    legacy_dir.mkdir()
    (legacy_dir / "tax_calculator.py").write_text("def calc_tax(amount): return amount * 0.15", encoding="utf-8")

    # Mock asset
    asset_dir = proj / "docs" / "05-assets"
    asset_dir.mkdir(parents=True)
    (asset_dir / "login_screen.svg").write_text("<svg><text>Connexion</text></svg>", encoding="utf-8")

    return {
        "root": tmp_path,
        "project": proj,
        "story_file": story_file,
        "legacy_dir": legacy_dir,
        "asset_file": asset_dir / "login_screen.svg"
    }


def test_handoff_simulator_dry_run(dummy_project):
    with patch("src.pipelines.delegation.handoff_simulator.resolve_story_file", return_value=dummy_project["story_file"]):
        res = run_handoff_simulator(
            project_name="TestSpecial",
            story_id="US-01",
            dry_run=True
        )
        assert res["success"] is True
        assert res["status"] == "HANDOFF_APPROVED"
        assert res["dry_run"] is True


def test_legacy_miner_dry_run(dummy_project):
    res = run_legacy_miner(
        project_name="TestSpecial",
        source_path=str(dummy_project["legacy_dir"]),
        dry_run=True
    )
    assert res["success"] is True
    assert res["status"] == "MINED_SUCCESS"
    assert res["rules_count"] == 5


def test_shadow_estimator_dry_run(dummy_project):
    with patch("pathlib.Path.cwd", return_value=dummy_project["root"]):
        res = run_shadow_estimator(
            project_name="TestSpecial",
            target_id="EPIC-AUTH",
            dry_run=True
        )
        assert res["success"] is True
        assert res["status"] == "ESTIMATION_COMPLETED"
        assert res["data"]["baseline_estimate_days"] == 5
        assert res["data"]["shadow_estimate_days"] == 9


def test_visual_dissector_dry_run(dummy_project):
    res = run_visual_dissector(
        project_name="TestSpecial",
        asset_path=str(dummy_project["asset_file"]),
        dry_run=True
    )
    assert res["success"] is True
    assert res["status"] == "DISSECTED_SUCCESS"
    assert "components" in res["matrix"]
    assert len(res["matrix"]["states_checklist"]) == 8


def test_semantic_janitor_watcher(dummy_project):
    watcher = SemanticJanitorWatcher(str(dummy_project["project"]))
    report = watcher.scan_project()
    assert report["total_scanned"] >= 1
    assert report["total_issues"] == 0

    # Test broken link detection
    broken_story = dummy_project["project"] / "backlog" / "stories" / "US-02.md"
    broken_story.write_text(
        "# Bad Story\n"
        "[Lien Brisé](file:///C:/non_existent_folder_xyz/file.md)\n",
        encoding="utf-8"
    )

    watcher2 = SemanticJanitorWatcher(str(dummy_project["project"]))
    report2 = watcher2.scan_project()
    assert report2["total_issues"] >= 1


def test_specialized_mcp_routing(dummy_project):
    from src.bridges.mcp_herdr import handle_tool_call

    with patch("src.pipelines.delegation.run_handoff_simulator", return_value={"success": True, "status": "HANDOFF_APPROVED"}):
        res = handle_tool_call("herdr_handoff_test", {"project_name": "TestSpecial", "story_id": "US-01", "dry_run": True})
        assert res["success"] is True

    with patch("src.pipelines.delegation.run_semantic_janitor", return_value={"success": True, "status": "JANITOR_COMPLETED"}):
        res = handle_tool_call("herdr_janitor_watch", {"project_name": "TestSpecial", "dry_run": True})
        assert res["success"] is True

