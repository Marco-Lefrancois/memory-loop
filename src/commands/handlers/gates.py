"""Handlers Gates : gates, tree (ADR-0341)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_gates(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Exécute ou audite les portails d'acceptation (Runnable Gates)."""
    from src.pipelines.gatekeeper import GatekeeperPipeline

    pipeline = GatekeeperPipeline(project_path=project_path)
    file_target = getattr(args, "file", None)
    scope = getattr(args, "scope", None)
    reverify = getattr(args, "reverify", False)
    lint = getattr(args, "lint", False)

    mode = "verify"
    if getattr(args, "status", False):
        mode = "status"
    elif reverify:
        mode = "reverify"

    return pipeline.execute(
        file_path=file_target,
        mode=mode,
        reverify=reverify,
        lint=lint,
        scope=scope,
    )


def handle_tree(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Affiche l'arbre complet Depth Tree et le statut des gates."""
    from src.pipelines.gatekeeper import GatekeeperPipeline

    pipeline = GatekeeperPipeline(project_path=project_path)
    file_target = getattr(args, "file", None)
    scope = getattr(args, "scope", None)

    return pipeline.execute(
        file_path=file_target,
        mode="status",
        reverify=False,
        lint=False,
        scope=scope,
    )
