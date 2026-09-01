"""
Agent Plugins 1.0 Validation Pipeline (ADR-0309)

Validates plugin.json and mcp.json against the Agent Plugins 1.0 specification schemas.
Performs structural checks: manifest presence, skills discovery, path containment, naming rules.
"""

import json
import re
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────

PLUGIN_MANIFEST = "plugin.json"
MCP_CONFIG = "mcp.json"
SKILLS_DIR = "skills"
SKILL_ENTRY = "SKILL.md"

# Agent Plugins 1.0 schema constants
AP_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

# Name pattern from spec: lowercase alphanumeric, hyphens, dots; no -- or ..; start/end alphanumeric
NAME_PATTERN = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.\-]*[a-z0-9])?$")
NAME_MAX_LEN = 64

# Allowed MCP server types
MCP_SERVER_TYPES = {"stdio", "streamable-http", "sse"}

# Fields allowed per server type (closed schema)
STDIO_FIELDS = {"type", "command", "args", "env", "cwd"}
STREAMABLE_HTTP_FIELDS = {"type", "url", "headers"}
SSE_FIELDS = {"type", "url", "headers"}

# Reserved env vars that plugins MUST NOT override
RESERVED_ENV_VARS = {"PLUGIN_ROOT", "PLUGIN_DATA"}

# CWD must start with one of these
CWD_PATTERN = re.compile(r"^(?:\./|\$\{PLUGIN_ROOT\}(?:/|$)|\$\{PLUGIN_DATA\}(?:/|$))")

# Plugin manifest allowed top-level keys (closed schema)
PLUGIN_ALLOWED_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
                       "repository", "license", "keywords", "extensions"}

# Author allowed keys
AUTHOR_ALLOWED_KEYS = {"name", "email", "url"}


# ── Result Builder ─────────────────────────────────────────────────

class ValidationResult:
    """Accumulates validation findings (errors = fatal, warnings = non-fatal)."""

    def __init__(self, plugin_root: Path):
        self.plugin_root = plugin_root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.skills_found: list[str] = []
        self.mcp_servers_found: list[str] = []
        self.mcp_servers_invalid: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "PASS" if self.passed else "FAIL",
            "plugin_root": str(self.plugin_root),
            "errors": self.errors,
            "warnings": self.warnings,
            "skills_discovered": self.skills_found,
            "mcp_servers_valid": self.mcp_servers_found,
            "mcp_servers_invalid": self.mcp_servers_invalid,
            "summary": {
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "skill_count": len(self.skills_found),
                "mcp_server_count": len(self.mcp_servers_found),
            }
        }


# ── Validators ─────────────────────────────────────────────────────

def _validate_plugin_manifest(manifest_path: Path, result: ValidationResult) -> dict | None:
    """Validate plugin.json against AP 1.0 spec. Returns parsed manifest or None if fatal."""
    if not manifest_path.exists():
        result.error(f"plugin.json not found at {manifest_path}")
        return None

    try:
        raw = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(raw)
    except json.JSONDecodeError as e:
        result.error(f"plugin.json is not valid JSON: {e}")
        return None

    if not isinstance(manifest, dict):
        result.error("plugin.json root must be a JSON object")
        return None

    # Required: $schema
    schema_val = manifest.get("$schema")
    if schema_val != AP_SCHEMA_URL:
        result.error(f"plugin.json.$schema must be exactly '{AP_SCHEMA_URL}', got: {schema_val!r}")

    # Required: name
    name = manifest.get("name")
    if not name:
        result.error("plugin.json.name is required")
    elif not isinstance(name, str):
        result.error(f"plugin.json.name must be a string, got: {type(name).__name__}")
    else:
        if len(name) > NAME_MAX_LEN:
            result.error(f"plugin.json.name exceeds {NAME_MAX_LEN} chars: {len(name)}")
        if not NAME_PATTERN.match(name):
            result.error(f"plugin.json.name does not match required pattern: {name!r}")

    # Closed schema: unknown top-level keys are non-fatal
    unknown_keys = set(manifest.keys()) - PLUGIN_ALLOWED_KEYS
    if unknown_keys:
        result.warn(f"plugin.json contains unknown top-level keys (non-fatal, ignored): {sorted(unknown_keys)}")

    # Optional: author (closed object)
    author = manifest.get("author")
    if author is not None:
        if not isinstance(author, dict):
            result.error("plugin.json.author must be an object")
        else:
            unknown_author = set(author.keys()) - AUTHOR_ALLOWED_KEYS
            if unknown_author:
                result.error(f"plugin.json.author contains unknown keys: {sorted(unknown_author)}")
            for k in AUTHOR_ALLOWED_KEYS:
                v = author.get(k)
                if v is not None and not isinstance(v, str):
                    result.error(f"plugin.json.author.{k} must be a string, got: {type(v).__name__}")

    # Optional: extensions (non-object is non-fatal)
    extensions = manifest.get("extensions")
    if extensions is not None and not isinstance(extensions, dict):
        result.warn("plugin.json.extensions is not an object (non-fatal, ignored)")

    # Optional: keywords (array of strings)
    keywords = manifest.get("keywords")
    if keywords is not None:
        if not isinstance(keywords, list):
            result.error("plugin.json.keywords must be an array")
        elif not all(isinstance(k, str) for k in keywords):
            result.error("plugin.json.keywords must contain only strings")

    # String-typed optional fields
    for field in ("version", "description", "homepage", "repository", "license"):
        val = manifest.get(field)
        if val is not None and not isinstance(val, str):
            result.error(f"plugin.json.{field} must be a string, got: {type(val).__name__}")

    return manifest


def _validate_mcp_config(mcp_path: Path, manifest: dict | None, result: ValidationResult) -> dict | None:
    """Validate mcp.json against AP 1.0 spec. Returns parsed config or None."""
    if not mcp_path.exists():
        result.warn("mcp.json not found — MCP component is absent (valid: plugin can be skills-only)")
        return None

    try:
        raw = mcp_path.read_text(encoding="utf-8")
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        result.error(f"mcp.json is not valid JSON: {e}")
        return None

    if not isinstance(config, dict):
        result.error("mcp.json root must be a JSON object")
        return None

    # Required: $schema
    schema_val = config.get("$schema")
    if schema_val != MCP_SCHEMA_URL:
        result.error(f"mcp.json.$schema must be exactly '{MCP_SCHEMA_URL}', got: {schema_val!r}")

    # Required: mcpServers
    servers = config.get("mcpServers")
    if servers is None:
        result.error("mcp.json.mcpServers is required")
        return config
    if not isinstance(servers, dict):
        result.error("mcp.json.mcpServers must be an object")
        return config

    # Closed top-level: only $schema and mcpServers
    unknown_top = set(config.keys()) - {"$schema", "mcpServers"}
    if unknown_top:
        result.error(f"mcp.json contains unknown top-level keys: {sorted(unknown_top)}")

    # Validate each server entry independently
    for name, server in servers.items():
        _validate_mcp_server(name, server, result)

    return config


def _validate_mcp_server(name: str, server: Any, result: ValidationResult):
    """Validate a single MCP server entry. Invalid entries are skipped (non-fatal per server)."""
    if not isinstance(server, dict):
        result.mcp_servers_invalid.append(name)
        result.warn(f"mcp.json.mcpServers.{name}: not an object, skipping")
        return

    server_type = server.get("type")
    if server_type not in MCP_SERVER_TYPES:
        result.mcp_servers_invalid.append(name)
        result.warn(f"mcp.json.mcpServers.{name}: unknown type '{server_type}', skipping")
        return

    # Determine allowed fields based on type
    if server_type == "stdio":
        allowed = STDIO_FIELDS
    elif server_type == "streamable-http":
        allowed = STREAMABLE_HTTP_FIELDS
    else:  # sse
        allowed = SSE_FIELDS

    # Check for unknown fields (closed schema → invalid entry)
    unknown = set(server.keys()) - allowed
    if unknown:
        result.mcp_servers_invalid.append(name)
        result.warn(f"mcp.json.mcpServers.{name}: unknown fields {sorted(unknown)}, skipping")
        return

    if server_type == "stdio":
        _validate_stdio_server(name, server, result)
    else:
        _validate_http_server(name, server, server_type, result)


def _validate_stdio_server(name: str, server: dict, result: ValidationResult):
    """Validate a stdio MCP server."""
    # Required: command
    command = server.get("command")
    if not command or not isinstance(command, str):
        result.mcp_servers_invalid.append(name)
        result.warn(f"mcp.json.mcpServers.{name}: 'command' is required and must be a non-empty string")
        return

    # Optional: args (array of strings)
    args = server.get("args")
    if args is not None:
        if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
            result.mcp_servers_invalid.append(name)
            result.warn(f"mcp.json.mcpServers.{name}: 'args' must be an array of strings")
            return

    # Optional: env (object of strings, no PLUGIN_ROOT/PLUGIN_DATA keys)
    env = server.get("env")
    if env is not None:
        if not isinstance(env, dict):
            result.mcp_servers_invalid.append(name)
            result.warn(f"mcp.json.mcpServers.{name}: 'env' must be an object")
            return
        reserved = set(env.keys()) & RESERVED_ENV_VARS
        if reserved:
            result.mcp_servers_invalid.append(name)
            result.warn(f"mcp.json.mcpServers.{name}: 'env' must not contain reserved keys: {sorted(reserved)}")
            return
        if not all(isinstance(v, str) for v in env.values()):
            result.mcp_servers_invalid.append(name)
            result.warn(f"mcp.json.mcpServers.{name}: all 'env' values must be strings")
            return

    # Optional: cwd (must match pattern)
    cwd = server.get("cwd")
    if cwd is not None:
        if not isinstance(cwd, str) or not CWD_PATTERN.match(cwd):
            result.mcp_servers_invalid.append(name)
            result.warn(f"mcp.json.mcpServers.{name}: 'cwd' must start with './', '${{PLUGIN_ROOT}}', or '${{PLUGIN_DATA}}', got: {cwd!r}")
            return

    result.mcp_servers_found.append(name)


def _validate_http_server(name: str, server: dict, server_type: str, result: ValidationResult):
    """Validate a streamable-http or sse MCP server."""
    url = server.get("url")
    if not url or not isinstance(url, str):
        result.mcp_servers_invalid.append(name)
        result.warn(f"mcp.json.mcpServers.{name}: 'url' is required and must be a non-empty string")
        return

    headers = server.get("headers")
    if headers is not None:
        if not isinstance(headers, dict) or not all(isinstance(v, str) for v in headers.values()):
            result.mcp_servers_invalid.append(name)
            result.warn(f"mcp.json.mcpServers.{name}: 'headers' must be an object of strings")
            return

    result.mcp_servers_found.append(name)


def _discover_skills(plugin_root: Path, result: ValidationResult):
    """Discover Agent Skills under skills/ directory (no recursive search per spec)."""
    skills_dir = plugin_root / SKILLS_DIR
    if not skills_dir.exists():
        result.warn(f"skills/ directory not found — plugin has no skills component")
        return

    if not skills_dir.is_dir():
        result.error(f"skills/ exists but is not a directory")
        return

    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir():
            skill_md = entry / SKILL_ENTRY
            if skill_md.exists() and skill_md.is_file():
                result.skills_found.append(entry.name)
            else:
                result.warn(f"skills/{entry.name}/ exists but has no SKILL.md — not discoverable as a skill")


def _check_extension_namespaces(plugin_root: Path, manifest: dict | None, result: ValidationResult):
    """Check extension namespaces for consistency."""
    if manifest is None:
        return

    extensions = manifest.get("extensions", {})
    if not isinstance(extensions, dict):
        return

    for ns_name, ns_data in extensions.items():
        # Check if the namespace directory exists
        ns_dir = plugin_root / ns_name
        if ns_dir.exists() and not ns_dir.is_dir():
            result.warn(f"Extension namespace '{ns_name}' exists as a file, not a directory")
        # Verify namespace data is an object
        if not isinstance(ns_data, dict):
            result.warn(f"Extension namespace '{ns_name}' value should be an object")


# ── Public API ─────────────────────────────────────────────────────

def run_plugin_validate(project_name: str = None,
                        plugin_root: str | Path = None,
                        strict: bool = False) -> dict[str, Any]:
    """
    Validate an Agent Plugin at the given root directory.

    Args:
        project_name: Optional project name (used for logging context only)
        plugin_root: Path to the plugin root. Defaults to '.agents/'
        strict: If True, treat warnings as errors

    Returns:
        Dictionary with validation results (status, errors, warnings, discoveries)
    """
    if plugin_root is None:
        plugin_root = Path(".agents")
    else:
        plugin_root = Path(plugin_root)

    result = ValidationResult(plugin_root)

    # Step 1: Validate plugin.json
    manifest_path = plugin_root / PLUGIN_MANIFEST
    manifest = _validate_plugin_manifest(manifest_path, result)

    # Step 2: Validate mcp.json
    mcp_path = plugin_root / MCP_CONFIG
    _validate_mcp_config(mcp_path, manifest, result)

    # Step 3: Discover skills
    _discover_skills(plugin_root, result)

    # Step 4: Check extension namespaces
    _check_extension_namespaces(plugin_root, manifest, result)

    # Strict mode: promote warnings to errors
    if strict and result.warnings:
        result.errors.extend([f"[strict] {w}" for w in result.warnings])

    output = result.to_dict()
    output["project"] = project_name or "default"
    output["spec_version"] = "1.0.0"

    return output
