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


def handle_rollover_archive(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Archivage des épopées scellées vers backlog/archive/ (ADR-0391)."""
    from src.pipelines.sync._sync_archive import auto_archive_completed_epics

    dry_run = getattr(args, "dry_run", False)
    res = auto_archive_completed_epics(project_path, dry_run=dry_run)
    status = res.get("status", "")
    if status == "no_completed_epics":
        ZeroFluffConsole.info("Aucune épopée 100% complétée à archiver dans sprint_backlog.md.")
    elif res.get("archived_epics", 0) > 0:
        prefix = "[DRY-RUN] " if dry_run else ""
        ZeroFluffConsole.success(
            f"{prefix}Archivage achevé : {res['archived_epics']} épopée(s) et "
            f"{res['archived_stories']} récit(s) archivés vers backlog/archive/."
        )
    return 0

