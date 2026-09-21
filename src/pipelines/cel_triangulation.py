"""
CEL Triangulation Helper (ADR-0383).
Logique de triangulation du Code Evidence Ledger extraite de qa_certifier.py.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.pipelines.qa_certifier_models import CelTriangulationResult

logger = logging.getLogger("pipelines.qa_certifier")

REQUIRED_GHERKIN_PILLARS: Set[str] = {
    "PILIER_1_CHEMIN_NOMINAL",
    "PILIER_2_EXCEPTIONS_REJETS",
    "PILIER_3_RESILIENCE_MODE_DEGRADE",
    "PILIER_4_UX_OBSERVABILITE",
}


def _classify_pillar(pillar_raw: str) -> Optional[str]:
    """Classifie un nom de pilier brut en constantes normalisées."""
    p = pillar_raw.upper()
    if any(k in p for k in ("PILIER_1", "PILIER 1", "NOMINAL")):
        return "PILIER_1_CHEMIN_NOMINAL"
    if any(k in p for k in ("PILIER_2", "PILIER 2", "EXCEPTION", "REJET")):
        return "PILIER_2_EXCEPTIONS_REJETS"
    if any(k in p for k in ("PILIER_3", "PILIER 3", "RESILIEN", "RÉSIL", "DEGRADE")):
        return "PILIER_3_RESILIENCE_MODE_DEGRADE"
    if any(k in p for k in ("PILIER_4", "PILIER 4", "UX", "OBSERVABIL")):
        return "PILIER_4_UX_OBSERVABILITE"
    return None


def _parse_ledger(data: Any) -> tuple[List[Dict[str, Any]], Set[str]]:
    """Parse le JSON du CEL et retourne (blocs, fichiers sprint)."""
    blocks: List[Dict[str, Any]] = []
    sprint_files: Set[str] = set()

    if not isinstance(data, dict):
        return blocks, sprint_files

    if "code_blocks" in data and isinstance(data["code_blocks"], list):
        blocks.extend(data["code_blocks"])
    elif "ledger" in data and isinstance(data["ledger"], list):
        for entry in data["ledger"]:
            if isinstance(entry, dict) and "blocks" in entry:
                blocks.extend(entry.get("blocks", []))

    for fp in data.get("source_files_sha256", {}).keys():
        sprint_files.add(str(fp))

    for b in blocks:
        if b.get("file_path"):
            sprint_files.add(str(b["file_path"]))
        tp = b.get("test_proof")
        if isinstance(tp, dict) and tp.get("test_file"):
            sprint_files.add(str(tp["test_file"]))

    return blocks, sprint_files


def triangulate_cel(
    project_path: Path,
    project_name: str,
    evidence_dir: Optional[Path] = None,
) -> CelTriangulationResult:
    """Vérifie la complétude du Code Evidence Ledger et extrait les fichiers du sprint."""
    target_dir = evidence_dir or (project_path / "memory" / "evidence")
    if (
        not target_dir.exists()
        and (Path("Projects") / project_name / "memory" / "evidence").exists()
    ):
        target_dir = Path("Projects") / project_name / "memory" / "evidence"

    if not target_dir.exists():
        return CelTriangulationResult(
            False, "", 0, [], sorted(list(REQUIRED_GHERKIN_PILLARS)), False, []
        )

    ledgers = sorted(
        list(target_dir.glob("*code_evidence_ledger.json")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not ledgers:
        return CelTriangulationResult(
            False, "", 0, [], sorted(list(REQUIRED_GHERKIN_PILLARS)), False, []
        )

    chosen = ledgers[0]
    try:
        with open(chosen, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.debug(
            "CEL ledger parse failed",
            extra={"ledger_path": str(chosen), "error": str(exc)},
            exc_info=True,
        )
        return CelTriangulationResult(
            True, str(chosen), 0, [], sorted(list(REQUIRED_GHERKIN_PILLARS)), False, []
        )

    blocks, sprint_files = _parse_ledger(data)

    covered: Set[str] = set()
    for b in blocks:
        pillar = _classify_pillar(str(b.get("gherkin_pillar", "")))
        if pillar:
            covered.add(pillar)

    missing = sorted(list(REQUIRED_GHERKIN_PILLARS - covered))
    return CelTriangulationResult(
        cel_found=True,
        ledger_path=str(chosen),
        total_blocks=len(blocks),
        covered_pillars=sorted(list(covered)),
        missing_pillars=missing,
        is_complete=len(missing) == 0 and len(blocks) > 0,
        sprint_files=sorted(list(sprint_files)),
    )
