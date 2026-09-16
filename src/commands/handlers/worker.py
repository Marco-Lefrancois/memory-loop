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
    """Affiche le statut de tous les workers Herdr actifs ou d'une story spécifique."""
    from src.pipelines.worker_pipeline import run_worker_status
    story_id = getattr(args, "story", None)
    res = run_worker_status(getattr(args, "project", None), story_id=story_id)
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


def handle_worker_handoff_test(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exécute une simulation Handoff Zero-Ask aveugle sur une story."""
    from src.pipelines.delegation import run_handoff_simulator
    story_id = getattr(args, "story", "")
    dry_run = getattr(args, "dry_run", False)
    res = run_handoff_simulator(args.project, story_id, dry_run=dry_run)
    return 0 if res.get("success") else 1


def handle_worker_legacy_mine(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Extrait la logique métier et les validations d'un code source legacy."""
    from src.pipelines.delegation import run_legacy_miner
    source = getattr(args, "source", "")
    domain = getattr(args, "domain", None)
    dry_run = getattr(args, "dry_run", False)
    res = run_legacy_miner(args.project, source, target_domain=domain, dry_run=dry_run)
    return 0 if res.get("success") else 1


def handle_worker_shadow_estimate(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exécute un chiffrage contradictoire pessimiste basé sur les risques."""
    from src.pipelines.delegation import run_shadow_estimator
    target_id = getattr(args, "epic", "") or getattr(args, "story", "") or "EPIC-GLOBAL"
    desc = getattr(args, "desc", None)
    dry_run = getattr(args, "dry_run", False)
    res = run_shadow_estimator(args.project, target_id, scope_description=desc, dry_run=dry_run)
    return 0 if res.get("success") else 1


def handle_worker_visual_dissect(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Dissecte une maquette et génère la matrice UI des 8 états."""
    from src.pipelines.delegation import run_visual_dissector
    asset = getattr(args, "asset", "")
    dry_run = getattr(args, "dry_run", False)
    res = run_visual_dissector(args.project, asset, dry_run=dry_run)
    return 0 if res.get("success") else 1


def handle_worker_janitor_watch(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Lance un audit de santé de la mémoire et des liens documentaires."""
    from src.pipelines.delegation import run_semantic_janitor
    dry_run = getattr(args, "dry_run", False)
    res = run_semantic_janitor(args.project, dry_run=dry_run)
    return 0 if res.get("success") else 1


def handle_worker_reap(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Purge les volets et agents orphelins ou inactifs (ADR-0355 Stall Detection)."""
    from src.pipelines.worker_pipeline import run_worker_reap
    timeout_sec = getattr(args, "timeout", 300)
    force = getattr(args, "force", False)
    project_name = getattr(args, "project", None)
    res = run_worker_reap(project_name=project_name, timeout_sec=timeout_sec, force=force)
    return 0 if res.get("success") else 1


