"""Handlers Analyse — Facade de réexportation (découpage ADR-0202)."""

from __future__ import annotations

# ── Sync (sync, supersession-sync) ───────────────────────────────────────────
from src.commands.handlers.analysis_sync import (  # noqa: F401
    handle_sync,
    handle_supersession_sync,
)

# ── Audit (rubber-duck, struct-check, eval-harvest, dossier-init) ────────────
from src.commands.handlers.analysis_audit import (  # noqa: F401
    handle_struct_check,
    handle_rubber_duck,
    handle_eval_harvest,
    handle_dossier_init,
)

# ── Core (drill, confidence, blast, chunk, agentic-extract, etc.) ────────────
from src.commands.handlers.analysis_core import (  # noqa: F401
    handle_drill,
    handle_confidence,
    handle_blast,
    handle_chunk,
    handle_agentic_extract,
    handle_context_watch,
    handle_token_tracker,
    handle_distill_invest,
    handle_parent_resolve,
    handle_story_clean,
    handle_export_obsidian,
    handle_hyper_query,
)

__all__ = [
    # Sync
    "handle_sync",
    "handle_supersession_sync",
    # Audit
    "handle_struct_check",
    "handle_rubber_duck",
    "handle_eval_harvest",
    "handle_dossier_init",
    # Core
    "handle_drill",
    "handle_confidence",
    "handle_blast",
    "handle_chunk",
    "handle_agentic_extract",
    "handle_context_watch",
    "handle_token_tracker",
    "handle_distill_invest",
    "handle_parent_resolve",
    "handle_story_clean",
    "handle_export_obsidian",
    "handle_hyper_query",
]
