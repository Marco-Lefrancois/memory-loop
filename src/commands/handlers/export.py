"""Handlers Export — Facade de réexportation (découpage ADR-0202)."""

from __future__ import annotations

# Jira Sync (+ private helpers/constants for tests & mocking)
from src.commands.handlers.export_story import (  # noqa: F401
    handle_jira_sync,
    _parse_target_keys,
    _verify_sha256_manifest,
    _TEMP_KEY_PREFIX,
    _BLOCKED_STATUSES_WITHOUT_FLAG,
)

# Re-export symbols from sub-imports used by test mocking
from src.pipelines.jira.sync_engine import (  # noqa: F401
    build_sync_preview,
    sync_targeted_to_jira,
    is_jira_status_closed,
)
from src.pipelines.sync import run_sync  # noqa: F401

# Plugin, Cycle, Self-Dev, Unlearn, Canvas, Jira Read
from src.commands.handlers.export_full import (  # noqa: F401
    handle_plugin_export,
    handle_cycle_status,
    handle_self_dev,
    handle_unlearn,
    handle_canvas,
    handle_jira_read,
)

__all__ = [
    "handle_jira_sync",
    "handle_jira_read",
    "handle_plugin_export",
    "handle_cycle_status",
    "handle_self_dev",
    "handle_unlearn",
    "handle_canvas",
]
