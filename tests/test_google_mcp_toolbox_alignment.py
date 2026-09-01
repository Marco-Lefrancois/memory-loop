import pytest
from pathlib import Path
import json

from src.bridges.mcp_loop_mem import handle_tools_list
from src.sdk.client import MLoopClient


def test_tools_yaml_manifest_exists():
    manifest_path = Path("tools.yaml")
    assert manifest_path.exists(), "Le manifeste tools.yaml déclaratif doit exister à la racine mLoop."


def test_dynamic_toolsets_phase_filtering():
    # 1. Sans filtre : tous les outils
    all_res = handle_tools_list(1)
    all_tools = all_res["result"]["tools"]
    assert len(all_tools) > 5

    # 2. Avec filtre phase="PLAN"
    plan_res = handle_tools_list(1, {"phase": "PLAN"})
    plan_tools = plan_res["result"]["tools"]
    assert len(plan_tools) > 0
    assert len(plan_tools) < len(all_tools)
    tool_names = [t["name"] for t in plan_tools]
    assert "loop_mem_search" in tool_names
    assert "check_story_compliance" not in tool_names


def test_mloop_client_sdk():
    client = MLoopClient(project_name="mLoop")
    plan_tools = client.list_tools(phase="PLAN")
    assert len(plan_tools) > 0
    assert any(t["name"] == "loop_mem_search" for t in plan_tools)
