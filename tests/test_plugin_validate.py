"""
Tests for Agent Plugins 1.0 validation pipeline (ADR-0309).
Red-Green TDD: these tests define the expected behavior before implementation.
"""

import json
import pytest
from pathlib import Path

from src.pipelines.plugin_validate import (
    run_plugin_validate,
    NAME_PATTERN,
    AP_SCHEMA_URL,
    MCP_SCHEMA_URL,
)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def plugin_dir(tmp_path):
    """Create a minimal valid plugin directory."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create a valid skill
    skill = skills_dir / "analyze"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Analyze\nDescription here.", encoding="utf-8")

    # Create plugin.json
    manifest = {
        "$schema": AP_SCHEMA_URL,
        "name": "test-plugin",
    }
    (tmp_path / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

    return tmp_path


@pytest.fixture
def full_plugin_dir(plugin_dir):
    """Extend minimal plugin with mcp.json and extension namespace."""
    mcp = {
        "$schema": MCP_SCHEMA_URL,
        "mcpServers": {
            "my-server": {
                "type": "stdio",
                "command": "python",
                "args": ["${PLUGIN_ROOT}/server.py"],
                "cwd": "${PLUGIN_ROOT}"
            }
        }
    }
    (plugin_dir / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")

    # Extension namespace
    ns_dir = plugin_dir / "com.example.client"
    ns_dir.mkdir()
    (ns_dir / "config.json").write_text("{}", encoding="utf-8")

    # Update manifest with extensions
    manifest = json.loads((plugin_dir / "plugin.json").read_text())
    manifest["extensions"] = {"com.example.client": {"feature": True}}
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

    return plugin_dir


# ── Name Pattern Tests ─────────────────────────────────────────────

class TestNamePattern:
    """Verify name regex matches the Agent Plugins 1.0 spec."""

    def test_valid_simple(self):
        assert NAME_PATTERN.match("mloop-framework")

    def test_valid_with_dots(self):
        assert NAME_PATTERN.match("my.plugin.v2")

    def test_valid_single_char(self):
        assert NAME_PATTERN.match("a")

    def test_invalid_uppercase(self):
        assert not NAME_PATTERN.match("MyPlugin")

    def test_invalid_double_hyphen(self):
        assert not NAME_PATTERN.match("my--plugin")

    def test_invalid_double_dot(self):
        assert not NAME_PATTERN.match("my..plugin")

    def test_invalid_start_hyphen(self):
        assert not NAME_PATTERN.match("-plugin")

    def test_invalid_end_hyphen(self):
        assert not NAME_PATTERN.match("plugin-")

    def test_invalid_spaces(self):
        assert not NAME_PATTERN.match("my plugin")

    def test_invalid_empty(self):
        assert not NAME_PATTERN.match("")

    def test_max_length_boundary(self):
        name = "a" * 64
        assert NAME_PATTERN.match(name)

    def test_over_max_length(self):
        """Name pattern allows the string but length check is separate."""
        name = "a" * 65
        assert NAME_PATTERN.match(name)  # Pattern itself doesn't enforce length


# ── Plugin Manifest Validation ─────────────────────────────────────

class TestPluginManifest:

    def test_valid_minimal_manifest(self, plugin_dir):
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "PASS"
        assert res["summary"]["error_count"] == 0

    def test_missing_manifest_fails(self, tmp_path):
        res = run_plugin_validate(plugin_root=tmp_path)
        assert res["status"] == "FAIL"
        assert any("plugin.json not found" in e for e in res["errors"])

    def test_invalid_json_fails(self, tmp_path):
        (tmp_path / "plugin.json").write_text("{invalid json", encoding="utf-8")
        res = run_plugin_validate(plugin_root=tmp_path)
        assert res["status"] == "FAIL"
        assert any("not valid JSON" in e for e in res["errors"])

    def test_wrong_schema_fails(self, plugin_dir):
        manifest = json.loads((plugin_dir / "plugin.json").read_text())
        manifest["$schema"] = "https://wrong.url/schema.json"
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "FAIL"
        assert any("$schema" in e for e in res["errors"])

    def test_missing_name_fails(self, plugin_dir):
        manifest = {"$schema": AP_SCHEMA_URL}
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "FAIL"
        assert any("name is required" in e for e in res["errors"])

    def test_invalid_name_pattern_fails(self, plugin_dir):
        manifest = {"$schema": AP_SCHEMA_URL, "name": "Invalid-Name"}
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "FAIL"
        assert any("pattern" in e for e in res["errors"])

    def test_name_too_long_fails(self, plugin_dir):
        manifest = {"$schema": AP_SCHEMA_URL, "name": "a" * 65}
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "FAIL"
        assert any("exceeds" in e for e in res["errors"])

    def test_unknown_top_level_keys_warn(self, plugin_dir):
        manifest = json.loads((plugin_dir / "plugin.json").read_text())
        manifest["custom_field"] = "something"
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "PASS"  # Non-fatal
        assert any("unknown top-level" in w for w in res["warnings"])

    def test_unknown_author_keys_fail(self, plugin_dir):
        manifest = json.loads((plugin_dir / "plugin.json").read_text())
        manifest["author"] = {"name": "Test", "phone": "123"}
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "FAIL"
        assert any("author contains unknown" in e for e in res["errors"])


# ── MCP Config Validation ──────────────────────────────────────────

class TestMcpConfig:

    def test_no_mcp_is_valid(self, plugin_dir):
        """A skills-only plugin is valid without mcp.json."""
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "PASS"

    def test_valid_stdio_server(self, full_plugin_dir):
        res = run_plugin_validate(plugin_root=full_plugin_dir)
        assert res["status"] == "PASS"
        assert "my-server" in res["mcp_servers_valid"]

    def test_invalid_mcp_json(self, plugin_dir):
        (plugin_dir / "mcp.json").write_text("{bad}", encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert res["status"] == "FAIL"

    def test_reserved_env_var_warns(self, plugin_dir):
        mcp = {
            "$schema": MCP_SCHEMA_URL,
            "mcpServers": {
                "bad-server": {
                    "type": "stdio",
                    "command": "python",
                    "env": {"PLUGIN_ROOT": "/override"}
                }
            }
        }
        (plugin_dir / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert "bad-server" in res["mcp_servers_invalid"]

    def test_invalid_cwd_warns(self, plugin_dir):
        mcp = {
            "$schema": MCP_SCHEMA_URL,
            "mcpServers": {
                "bad-cwd": {
                    "type": "stdio",
                    "command": "python",
                    "cwd": "/absolute/path"
                }
            }
        }
        (plugin_dir / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert "bad-cwd" in res["mcp_servers_invalid"]

    def test_unknown_server_type_skipped(self, plugin_dir):
        mcp = {
            "$schema": MCP_SCHEMA_URL,
            "mcpServers": {
                "alien": {"type": "grpc", "endpoint": "localhost:50051"}
            }
        }
        (plugin_dir / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert "alien" in res["mcp_servers_invalid"]

    def test_streamable_http_valid(self, plugin_dir):
        mcp = {
            "$schema": MCP_SCHEMA_URL,
            "mcpServers": {
                "remote": {
                    "type": "streamable-http",
                    "url": "https://api.example.com/mcp"
                }
            }
        }
        (plugin_dir / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert "remote" in res["mcp_servers_valid"]


# ── Skills Discovery ───────────────────────────────────────────────

class TestSkillsDiscovery:

    def test_discovers_skills(self, plugin_dir):
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert "analyze" in res["skills_discovered"]

    def test_no_skills_dir_warns(self, tmp_path):
        manifest = {"$schema": AP_SCHEMA_URL, "name": "no-skills"}
        (tmp_path / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=tmp_path)
        assert res["status"] == "PASS"
        assert any("skills/ directory not found" in w for w in res["warnings"])

    def test_skill_without_skill_md_warns(self, plugin_dir):
        orphan = plugin_dir / "skills" / "broken-skill"
        orphan.mkdir()
        # No SKILL.md
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert "broken-skill" not in res["skills_discovered"]
        assert any("no SKILL.md" in w for w in res["warnings"])

    def test_multiple_skills_discovered(self, plugin_dir):
        for name in ["plan", "sentinel", "tdd"]:
            skill = plugin_dir / "skills" / name
            skill.mkdir()
            (skill / "SKILL.md").write_text(f"# {name}", encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir)
        assert len(res["skills_discovered"]) == 4  # analyze + 3 new


# ── Strict Mode ────────────────────────────────────────────────────

class TestStrictMode:

    def test_strict_promotes_warnings(self, plugin_dir):
        manifest = json.loads((plugin_dir / "plugin.json").read_text())
        manifest["unknown"] = "value"
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = run_plugin_validate(plugin_root=plugin_dir, strict=True)
        assert res["status"] == "FAIL"
        assert any("[strict]" in e for e in res["errors"])


# ── Integration: Real mLoop Plugin ─────────────────────────────────

class TestMloopPluginIntegration:
    """Validate the actual .agents/ plugin created by ADR-0309."""

    def test_real_plugin_validates(self):
        """The real .agents/ plugin.json + mcp.json should pass validation."""
        agents_dir = Path(".agents")
        if not agents_dir.exists():
            pytest.skip(".agents/ not found — not running from mLoop root")
        res = run_plugin_validate(plugin_root=agents_dir)
        assert res["status"] == "PASS", f"Validation failed: {res['errors']}"
        assert res["summary"]["skill_count"] >= 20  # We have 21 skills
        assert res["summary"]["mcp_server_count"] >= 1  # At least 1 MCP server
