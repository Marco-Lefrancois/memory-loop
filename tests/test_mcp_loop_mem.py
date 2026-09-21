import json
from pathlib import Path
import pytest
from src.bridges.mcp_loop_mem import (
    handle_initialize,
    handle_server_discover,
    process_message,
)
from src.bridges.mcp_resources import (
    discover_skills,
    handle_resources_list,
    handle_resources_read,
)
from src.bridges.mcp_tools import (
    handle_tools_list,
    handle_tools_call,
    execute_story_compliance,
)


def test_mcp_initialize():
    res = handle_initialize(1)
    assert res["jsonrpc"] == "2.0"
    assert res["id"] == 1
    assert "tools" in res["result"]["capabilities"]
    assert res["result"]["serverInfo"]["name"] == "memory-loop-session-memory-mcp"


def test_mcp_tools_list():
    res = handle_tools_list(2)
    tools = res["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "loop_mem_search" in names
    assert "loop_mem_code_rag" in names
    assert "read_skill" in names


def test_mcp_story_compliance():
    content_ok = """# Titre
## Règles d'affaires
- **RM-001 Règle Métier** : Spécification claire.
## Scénarios de test
```gherkin
Scénario: Nominal
Scénario: Exception
Scénario: Résilience
Scénario: UX
```"""
    res_ok = execute_story_compliance({"content": content_ok})
    assert "CONFORME" in res_ok

    content_bad = "# Titre\n## Scénarios de test\nScénario: Unique"
    res_bad = execute_story_compliance({"content": content_bad})
    assert "NON CONFORME" in res_bad


def test_mcp_resources_list_and_read_skill():
    skills = discover_skills()
    assert len(skills) > 0

    res_list = handle_resources_list(3)
    resources = res_list["result"]["resources"]
    skill_uris = [r["uri"] for r in resources if r["uri"].startswith("skill://")]
    assert len(skill_uris) > 0

    target_skill = skills[0]["name"]
    res_read = handle_resources_read(4, {"uri": f"skill://{target_skill}"})
    assert res_read["result"].get("isError") is not True
    assert "contents" in res_read["result"]
    assert res_read["result"]["contents"][0]["mimeType"] == "text/markdown"

    res_missing = handle_resources_read(5, {"uri": "skill://skill_fantome_inexistant"})
    assert res_missing["result"]["isError"] is True


def test_mcp_process_message_dispatch():
    req = json.dumps({"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}})
    raw_res = process_message(req)
    assert raw_res is not None
    data = json.loads(raw_res)
    assert data["id"] == 10
    assert "tools" in data["result"]
