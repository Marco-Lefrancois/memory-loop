"""Handlers Export — Plugin, Cycle Status, Self-Dev, Unlearn, Canvas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

def handle_plugin_export(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Exporte un package Agent Plugin 1.0 portable."""
    from src.pipelines.plugin_export import run_plugin_export

    result = run_plugin_export(
        project_name=args.project,
        output_path=getattr(args, "output", None),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


def handle_cycle_status(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Affiche le statut du cycle courant."""
    from src.pipelines.cycle_runner import run_cycle_status

    res = run_cycle_status(args.project)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def handle_self_dev(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Auto-développement du framework mLoop."""
    from src.pipelines.self_dev_pipeline import run_self_dev

    run_self_dev(args.project, state, project_path)
    return 0


def handle_unlearn(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Désapprentissage d'un concept."""
    from src.pipelines.unlearn import run_unlearn

    res = run_unlearn(args.project, args.concept)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


def handle_canvas(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Génération et synchronisation des toiles Obsidian Canvas (ADR-0337)."""
    from src.pipelines.canvas_generator import CanvasGenerator

    generator = CanvasGenerator(project_path)
    res = generator.sync_all_canvases()
    ZeroFluffConsole.success(
        f"Synchronisation Canvas terminée pour '{project_path.name}' ({len(res)} toiles générées)."
    )
    return 0


def handle_jira_read(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """
    Lecture Read-Only d'un ticket Jira Cloud (API v3) et restitution de sa
    description ADF convertie en Markdown lisible. Utile pour diff Jira <-> récit local.
    Aucune écriture ; les identifiants proviennent du .env (jamais affichés).
    """
    from src.pipelines.jira.jira_reader import read_jira_issue

    issue_key = getattr(args, "issue", None)
    if not issue_key:
        ZeroFluffConsole.error(
            "jira-read nécessite --issue <CLE_JIRA> (ex: --issue COUVBOIRE-1062)."
        )
        return 1

    result = read_jira_issue(issue_key.strip())
    if result is None:
        return 1

    out_path = getattr(args, "out", None)
    if out_path:
        Path(out_path).write_text(result["description_md"], encoding="utf-8")
        ZeroFluffConsole.success(
            f"{result['key']} — « {result['summary']} » [{result['status']}] "
            f"→ description Markdown écrite sous {out_path}"
        )
    else:
        print(f"# {result['key']} — {result['summary']}  [{result['status']}]\n")
        print(result["description_md"])
    return 0

