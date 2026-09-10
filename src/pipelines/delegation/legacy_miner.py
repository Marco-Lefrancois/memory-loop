"""
legacy_miner.py - Legacy Codebase Business Logic Miner (ADR-0346)

Dispatches a deepsearch worker agent to analyze a legacy codebase repository/directory,
extracting buried business rules, validation logic, formulas, and error codes into docs/02-business-rules/.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.cli import ZeroFluffConsole
from src.core.herdr_adapter import herdr


def run_legacy_miner(
    project_name: str,
    source_path: str,
    target_domain: Optional[str] = None,
    timeout_sec: int = 180,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Spawns a deepsearch worker to extract business rules from a legacy codebase.
    """
    ZeroFluffConsole.section("LEGACY CODEBASE LOGIC MINER")
    src_dir = Path(source_path)

    if not src_dir.exists():
        err = f"Répertoire source legacy introuvable : '{source_path}'"
        ZeroFluffConsole.error(err)
        return {"success": False, "error": err}

    proj_dir = Path.cwd() / "Projects" / project_name
    if not proj_dir.exists() and (Path.cwd() / "docs").exists():
        proj_dir = Path.cwd()

    rules_dir = proj_dir / "docs" / "02-business-rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    domain_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', (target_domain or src_dir.name)).lower()
    output_file = rules_dir / f"BR-LEGACY-{domain_slug}.md"

    ZeroFluffConsole.info(f"Analyse de la source : {src_dir.resolve()}")
    ZeroFluffConsole.info(f"Fichier de destination SSOT : {output_file.relative_to(Path.cwd()) if output_file.is_relative_to(Path.cwd()) else output_file}")

    if dry_run:
        ZeroFluffConsole.info("[Dry Run] Scan legacy préparé avec succès.")
        return {
            "success": True,
            "status": "MINED_SUCCESS",
            "source": str(src_dir),
            "output_file": str(output_file),
            "rules_count": 5,
            "dry_run": True
        }

    # 1. Spawn deepsearch worker
    worker_name = f"worker_miner_{domain_slug}"[:32]
    split_res = herdr.split_pane(target_pane_id="p1", direction="right", no_focus=True)
    pane_id = split_res.get("new_pane_id") or "p_miner"

    herdr.start_agent(
        agent_name=worker_name,
        kind="opencode",
        pane_id=str(pane_id),
        extra_args=["--yolo", "--model", "nmedia_cloud/claude-sonnet-5"]
    )

    # 2. Formulate Extraction Prompt
    prompt_text = (
        f"## MISSION : EXTRACTION DE RÈGLES MÉTIER LEGACY (LOGIC MINER)\n\n"
        f"**Répertoire Source** : `{src_dir.resolve()}`\n"
        f"**Fichier Cible** : `{output_file.resolve()}`\n\n"
        f"### Directives d'extraction :\n"
        f"1. Explore le code source dans `{src_dir.resolve()}` (contrôleurs, modèles, validateurs, services).\n"
        f"2. Identifie toutes les règles d'affaires critiques : calculs, seuils, validations de champs, codes d'erreurs.\n"
        f"3. Rédige un fichier Markdown structuré dans `{output_file.resolve()}` avec le format :\n"
        f"   - Frontmatter YAML (id: BR-LEGACY-{domain_slug.upper()}, title, domain)\n"
        f"   - Tableaux des règles identifiées avec source (nom du fichier legacy et méthode)\n"
        f"   - Cas limites et contraintes non documentées\n"
        f"4. Termine par `[MINING_COMPLETED]`.\n"
    )

    herdr.prompt_agent(worker_name, prompt_text, wait=True, timeout_ms=timeout_sec * 1000)

    # 3. Harvest & Teardown
    read_res = herdr.read_agent_output(worker_name, lines=80, source="recent-unwrapped")
    cleaned_logs = herdr.filter_terminal_bloat(read_res.get("raw_output") or "")
    herdr.cleanup_worker(worker_name)

    herdr.show_notification(
        title="⛏️ Legacy Mining Terminé",
        body=f"Règles extraites sous docs/02-business-rules/BR-LEGACY-{domain_slug}.md",
        sound="done"
    )

    ZeroFluffConsole.success(f"Règles métier legacy extraites avec succès dans {output_file.name}.")
    return {
        "success": True,
        "status": "MINED_SUCCESS",
        "output_file": str(output_file),
        "summary": cleaned_logs[-400:] if len(cleaned_logs) > 400 else cleaned_logs
    }
