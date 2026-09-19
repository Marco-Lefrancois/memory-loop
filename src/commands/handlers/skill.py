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
    from src.core.skill_registry import get_skill_catalog, list_skills

    # Récupérer les compétences dynamiques du StandardsGraph (catalogue SSOT)
    catalog = get_skill_catalog()
    if catalog:
        ZeroFluffConsole.section(f"CATALOGUE DES COMPÉTENCES STANDARDSGRAPH ({len(catalog)} compétences indexées)")
        by_category: dict[str, list[dict]] = {}
        for name, meta in catalog.items():
            cat = meta.get("category", "général").capitalize()
            by_category.setdefault(cat, []).append(meta)

        for cat, items in sorted(by_category.items()):
            ZeroFluffConsole.info(f"\n📁 Catégorie : {cat} ({len(items)})")
            for item in items:
                h_status = "⚡ Actif" if item.get("runtime_handler") else "📦 Déclaratif"
                desc = item.get("description", "Aucune description")
                print(f"  • {item['name']:<32} [{h_status}] : {desc}")
        return 0

    # Fallback sur les handlers en mémoire si le catalogue est vide
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
    """Audite l'hygiène du catalogue de compétences mLoop et/ou des runtimes d'agents locaux (ADR-0377)."""
    check_skills = getattr(args, "skills", False)
    check_agents = getattr(args, "agents", False)

    # Si aucun drapeau explicite n'est fourni, exécuter les deux volets de diagnostic
    if not check_skills and not check_agents:
        check_skills = True
        check_agents = True

    status_code = 0

    if check_skills:
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
        if not report.get("success"):
            status_code = 1

    if check_agents:
        agent_code = handle_agent_probe(args, state, project_path)
        if agent_code != 0:
            status_code = agent_code

    return status_code


def handle_agent_probe(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Sonde la disponibilité et les versions des agents CLI locaux (ADR-0377)."""
    from src.core.agent_probe import AgentProbe, render_agent_report

    probe = AgentProbe()
    target_agent = getattr(args, "agent", None)
    output_json = getattr(args, "json", False)

    if target_agent:
        statuses = [probe.probe(target_agent)]
    else:
        statuses = probe.probe_all()

    report_str = render_agent_report(statuses, json_format=output_json)
    if not output_json:
        ZeroFluffConsole.section("SONDE DÉTERMINISTE DES RUNTIMES D'AGENTS AVAL (ADR-0377)")
    print(report_str)
    return 0

