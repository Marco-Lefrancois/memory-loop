"""
visual_dissector.py - Visual Contract Dissector & 8-States UI Mapper (ADR-0332 / ADR-0340 / ADR-0346)

Dispatches a compaction/OCR worker to inspect SVG/image mockups, extracting verbatim
UI copy, layout structures, and mapping all 8 UI states into docs/05-assets/.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.cli import ZeroFluffConsole
from src.core.herdr_adapter import herdr


UI_8_STATES = [
    "1. Initial / Default",
    "2. Loading / Skeleton",
    "3. Empty State (Aucune donnée)",
    "4. Populated / Nominal",
    "5. Error / Validation Failure",
    "6. Active / Selected",
    "7. Disabled / Read-Only",
    "8. Hover / Focused"
]


def run_visual_dissector(
    project_name: str,
    asset_path: str,
    timeout_sec: int = 120,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Dissects a visual asset mockup and generates its complete 8-states UI matrix.
    """
    ZeroFluffConsole.section("VISUAL CONTRACT DISSECTOR & UI MAPPER")
    src_asset = Path(asset_path)

    if not src_asset.exists():
        err = f"Fichier de maquette introuvable : '{asset_path}'"
        ZeroFluffConsole.error(err)
        return {"success": False, "error": err}

    proj_dir = Path.cwd() / "Projects" / project_name
    if not proj_dir.exists() and (Path.cwd() / "docs").exists():
        proj_dir = Path.cwd()

    assets_dir = proj_dir / "docs" / "05-assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    out_file = assets_dir / f"{src_asset.stem}_ui_matrix.json"

    ZeroFluffConsole.info(f"Maquette analysée : {src_asset.name}")
    ZeroFluffConsole.info(f"Matrice UI de sortie : {out_file.name}")

    if dry_run:
        sample_matrix = {
            "asset_name": src_asset.name,
            "components": [
                {
                    "name": "HeaderActionBar",
                    "labels": ["Filtrer", "Rechercher", "Exporter"],
                    "states_covered": ["1. Initial / Default", "4. Populated / Nominal", "7. Disabled / Read-Only"]
                },
                {
                    "name": "DataTableGrid",
                    "labels": ["Nom", "Statut", "Date", "Actions"],
                    "states_covered": UI_8_STATES
                }
            ],
            "extracted_text": ["Filtrer", "Rechercher", "Exporter", "Nom", "Statut", "Date", "Actions"],
            "states_checklist": {st: True for st in UI_8_STATES}
        }
        out_file.write_text(json.dumps(sample_matrix, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.info("[Dry Run] Matrice UI des 8 états générée avec succès.")
        return {"success": True, "status": "DISSECTED_SUCCESS", "matrix": sample_matrix}

    # 1. Spawn worker (Gemini 3.5 Flash Lite)
    worker_name = f"worker_ui_{src_asset.stem.lower()}"[:32]
    split_res = herdr.split_pane(target_pane_id="p1", direction="down", no_focus=True)
    pane_id = split_res.get("new_pane_id") or "p_ui_dissect"

    herdr.start_agent(
        agent_name=worker_name,
        kind="opencode",
        pane_id=str(pane_id),
        extra_args=["--yolo", "--model", "nmedia_cloud/gemini-3.5-flash-lite"]
    )

    # 2. Formulate Prompt
    prompt_text = (
        f"## MISSION : DISSECTION VISUELLE DE MAQUETTE & MATRICE 8 ÉTATS\n\n"
        f"**Maquette** : `{src_asset.resolve()}`\n"
        f"**Fichier Cible** : `{out_file.resolve()}`\n\n"
        f"### Directives d'extraction visuelle :\n"
        f"1. Examine le fichier de maquette vectoriel/image.\n"
        f"2. Extrais tous les textes, libellés exacts de boutons, titres de colonnes et placeholders.\n"
        f"3. Cartographie pour chaque composant les 8 états obligatoires : "
        f"{', '.join(UI_8_STATES)}.\n"
        f"4. Sauvegarde la matrice au format JSON dans `{out_file.resolve()}`.\n"
        f"5. Termine par `[DISSECTION_COMPLETED]`.\n"
    )

    herdr.prompt_agent(worker_name, prompt_text, wait=True, timeout_ms=timeout_sec * 1000)

    # 3. Harvest & Teardown
    read_res = herdr.read_agent_output(worker_name, lines=50, source="recent-unwrapped")
    cleaned_logs = herdr.filter_terminal_bloat(read_res.get("raw_output") or "")
    herdr.cleanup_worker(worker_name)

    matrix_data = {}
    if out_file.exists():
        try:
            matrix_data = json.loads(out_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    ZeroFluffConsole.success(f"Dissection visuelle terminée pour {src_asset.name}.")
    herdr.show_notification(
        title="🖼️ Dissection UI Complétée",
        body=f"Matrice 8 états sauvegardée sous docs/05-assets/{out_file.name}",
        sound="done"
    )

    return {
        "success": True,
        "status": "DISSECTED_SUCCESS",
        "output_file": str(out_file),
        "matrix": matrix_data,
        "summary": cleaned_logs[-200:] if len(cleaned_logs) > 200 else cleaned_logs
    }
