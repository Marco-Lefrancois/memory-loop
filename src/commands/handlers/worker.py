"""
worker.py - CLI Command Handlers for Herdr Worker Lifecycle in mLoop
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_worker_spawn(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Instancie un volet Herdr isolé pour un récit spécifique."""
    from src.pipelines.worker_pipeline import run_worker_spawn
    story_id = getattr(args, "story", "")
    kind = getattr(args, "kind", "opencode")
    model = getattr(args, "model", None)
    task_type = getattr(args, "task_type", None)
    res = run_worker_spawn(args.project, story_id, kind=kind, model=model, task_type=task_type)
    return 0 if res.get("success") else 1


def handle_worker_status(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Affiche le statut de tous les workers Herdr actifs."""
    from src.pipelines.worker_pipeline import run_worker_status
    res = run_worker_status(getattr(args, "project", None))
    return 0 if res.get("success") else 1


def handle_worker_harvest(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Moissonne les preuves d'exécution PTY du worker et met à jour l'EvidencePack."""
    from src.pipelines.worker_pipeline import run_worker_harvest
    story_id = getattr(args, "story", "")
    lines = getattr(args, "lines", 150)
    res = run_worker_harvest(args.project, story_id, lines=lines)
    return 0 if res.get("success") else 1


def handle_worker_close(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Ferme un volet Herdr et libère ses ressources."""
    from src.pipelines.worker_pipeline import run_worker_close
    story_id = getattr(args, "story", "")
    res = run_worker_close(args.project, story_id)
    return 0 if res.get("success") else 1
