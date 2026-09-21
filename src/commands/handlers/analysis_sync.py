"""Handlers Analyse — Sync (sync/wikifix, supersession-sync)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_sync(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """WikiFix + Synchronisation d'état du projet."""
    from src.pipelines.sync import run_sync

    run_sync(
        args.project,
        state,
        project_path,
        verbose=getattr(args, "verbose", False),
        incremental=getattr(args, "incremental", False),
        fast_mode=getattr(args, "fast", False),
        story_filter=getattr(args, "story", None),
    )
    return 0


def handle_supersession_sync(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Synchronisation du registre de supersession des règles et décisions (ADR-0326)."""
    from src.loop_mem.supersession import MemorySupersessionEngine

    engine = MemorySupersessionEngine(project_path)
    ledger = engine.sync_ledger()

    ZeroFluffConsole.success(
        f"Registre de supersession synchronisé : {ledger['total_superseded']} élément(s) archivé(s)."
    )
    for item_id, details in ledger.get("superseded_items", {}).items():
        print(f"  [SUPERSEDED] {item_id} ➔ {details['superseded_by']} ({details['reason']})")

    return 0
