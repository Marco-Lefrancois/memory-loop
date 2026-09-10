"""Handlers Skill : skill-list, skill-invoke (SEP-2640)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState


def handle_skill_list(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Affiche le catalogue des compétences enregistrées dans le registre `skill://`."""
    from src.core.skill_registry import list_skills

    catalogue = list_skills()
    if not catalogue:
        ZeroFluffConsole.warning("[SEP-2640] Registre vide — aucune compétence enregistrée.")
        return 0

    ZeroFluffConsole.info(f"[SEP-2640] {len(catalogue)} compétence(s) disponible(s) :")
    print(json.dumps(catalogue, indent=2, ensure_ascii=False))
    return 0


def handle_skill_invoke(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Invoque une compétence via son URI `skill://`."""
    from src.core.skill_registry import (
        InvalidSkillURIError,
        SkillNotFoundError,
        invoke_skill,
    )

    uri: str = args.uri
    ZeroFluffConsole.info(f"[SEP-2640] Résolution de : {uri}")

    try:
        result = invoke_skill(uri)
        if result is not None:
            output = json.dumps(result, indent=2, ensure_ascii=False) if not isinstance(result, str) else result
            print(output)
        ZeroFluffConsole.success(f"[SEP-2640] Compétence '{uri}' exécutée avec succès.")
        return 0
    except InvalidSkillURIError as exc:
        ZeroFluffConsole.error(str(exc))
        return 1
    except SkillNotFoundError as exc:
        ZeroFluffConsole.error(str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001
        ZeroFluffConsole.error(f"[SEP-2640] Erreur inattendue lors de l'invocation : {exc}")
        return 1


def handle_skill_doctor(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Audite l'hygiène du catalogue de compétences mLoop (tokens, context rot, tombstones)."""
    from src.pipelines.skill_doctor import run_skill_doctor

    workspace_root = Path.cwd()
    threshold = getattr(args, "threshold", 2000)
    output_json = getattr(args, "json", False)
    suggest_tombstone = not getattr(args, "no_tombstone", False)

    report = run_skill_doctor(
        workspace_root=workspace_root,
        threshold=threshold,
        suggest_tombstone=suggest_tombstone,
        output_json=output_json,
    )
    return 0 if report.get("success") else 1
