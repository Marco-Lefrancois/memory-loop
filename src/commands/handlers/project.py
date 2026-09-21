"""Handlers Projet — Facade de réexportation (découpage ADR-0202)."""

from __future__ import annotations

# Core (init, resume, focus, vibe-check, install-hooks + private helpers)
from src.commands.handlers.project_core import (  # noqa: F401
    handle_init,
    handle_resume,
    handle_focus,
    handle_vibe_check,
    handle_install_hooks,
    _FRAMEWORK_ROOT,
    _HOOK_MANAGED_MARKER,
    _resolve_git_root,
    _uninstall_hook,
)

# Management (guide, sync-antigravity, gate-approve, lifecycle)
from src.commands.handlers.project_management import (  # noqa: F401
    handle_guide,
    handle_sync_antigravity,
    handle_gate_approve,
    handle_lifecycle_status,
    handle_lifecycle_clean,
)

__all__ = [
    # Core
    "handle_init",
    "handle_resume",
    "handle_focus",
    "handle_vibe_check",
    "handle_install_hooks",
    # Management
    "handle_guide",
    "handle_sync_antigravity",
    "handle_gate_approve",
    "handle_lifecycle_status",
    "handle_lifecycle_clean",
]
