"""
Moteur de backfill retroactif des EvidencePacks EPIC-10→17 (MLOOP-182-BE).

Injecte dans les packs existants : implementation_decisions (fact_dossier,
plans, sections Règles d'affaires), verbatim_extracts (granularité hybride D :
1/fichier source + 1/décision), declarative_contracts (plans) et
epistemic_audit.what_it_does_not_prove (Admission of Limits) — puis recalcule
richness_penalty (Déc.5) et horodatage.

Garanties : zéro invention (CA-2), idempotence stricte (CA-3 — delta nul =
zéro écriture), legacy EPIC 1-9 intouché (CA-4), écriture atomique tmp+replace
(Pilier 3), poursuite sur erreur avec log exc_info (ADR-0369).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.pipelines.backfill_merger import atomic_write_json, merge_and_maybe_write
from src.pipelines.backfill_parsers import parse_dossier, parse_plan, parse_story_rules
from src.utils.logger import get_logger

logger = get_logger("pipelines.evidence_backfill")

# Bornes d'éligibilité (CA-4) : <100 legacy EPIC 1-9, 100..179 cible EPIC 10-17,
# >=180 génération native (parité native MLOOP-180+).
_LEGACY_MAX = 99
_MODERN_MIN = 180


def _classify(story_number: int) -> str:
    if story_number <= _LEGACY_MAX:
        return "legacy"
    if story_number >= _MODERN_MIN:
        return "modern"
    return "eligible"


class EvidenceBackfillEngine:
    """Orchestrateur du backfill : classification, extraction, fusion, rapport."""

    def __init__(self, project_path: Path) -> None:
        self.project_path = Path(project_path)
        self.evidence_dir = self.project_path / "memory" / "evidence"
        self.plan_dir = self.project_path / "memory" / "plan"
        self.stories_dir = self.project_path / "backlog" / "stories"
        self.last_report: Optional[Dict[str, Any]] = None

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """Exécute le backfill sur tous les packs éligibles (CA-1 à CA-6)."""
        report: Dict[str, Any] = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "processed": [],
            "unchanged": [],
            "legacy_skipped": [],
            "skipped_modern": [],
            "no_source": [],
            "errors": [],
            "avg_delta_citations": 0.0,
        }
        deltas: List[int] = []

        for pack_path in sorted(self.evidence_dir.glob("*_evidence.json")):
            sid = pack_path.name[: -len("_evidence.json")]
            m = re.match(r"MLOOP-(\d+)", sid)
            if not m:
                continue
            classification = _classify(int(m.group(1)))
            if classification == "legacy":
                logger.info(
                    "legacy_skipped: %s (EPIC 1-9 strictement exclu, Déc. 6)",
                    sid,
                    extra={"component": "pipelines.evidence_backfill",
                           "operation": "run", "story_id": sid},
                )
                report["legacy_skipped"].append(sid)
                continue
            if classification == "modern":
                report["skipped_modern"].append(sid)
                continue

            try:
                delta = self._process_pack(sid, pack_path, report, dry_run=dry_run)
            except Exception as exc:
                logger.debug(
                    "Backfill du pack échoué, poursuite sur les autres packs",
                    exc_info=True,
                    extra={"component": "pipelines.evidence_backfill",
                           "operation": "run", "story_id": sid, "error": str(exc)},
                )
                report["errors"].append({"story_id": sid, "error": str(exc)})
                continue

            if delta is None:
                report["unchanged"].append(sid)
            else:
                report["processed"].append(sid)
                deltas.append(delta)

        report["avg_delta_citations"] = (
            round(sum(deltas) / len(deltas), 2) if deltas else 0.0
        )
        if not dry_run:
            atomic_write_json(self.evidence_dir / "backfill_report.json", report)
        self.last_report = report
        return report

    def _resolve_plan(self, sid: str) -> Optional[Path]:
        """Résolution déterministe du plan : nom canonique, puis contenance du sid."""
        exact = self.plan_dir / f"implementation_plan_{sid}.md"
        if exact.exists():
            return exact
        if self.plan_dir.exists():
            needle = sid.lower()
            for candidate in sorted(self.plan_dir.glob("implementation_plan_*.md")):
                if needle in candidate.name.lower():
                    return candidate
        return None

    def _process_pack(
        self, sid: str, pack_path: Path, report: Dict[str, Any], dry_run: bool
    ) -> Optional[int]:
        """
        Traite un pack éligible : parse TOUTES les sources d'abord (Pilier 3 —
        pack intact si une source est corrompue), puis fusion, puis écriture.

        Returns:
            Delta de citations injectées, ou None si inchangé (idempotence CA-3).
        """
        pack = json.loads(pack_path.read_text(encoding="utf-8"))

        sources_found = 0
        cand_decisions: List[Dict[str, Any]] = []
        cand_citations: List[Dict[str, Any]] = []
        cand_contracts: List[Dict[str, Any]] = []
        admissions: List[str] = []

        dossier_path = self.evidence_dir / f"{sid}_fact_dossier.md"
        if dossier_path.exists():
            rel = str(dossier_path.relative_to(self.project_path)).replace("\\", "/")
            parsed = parse_dossier(dossier_path.read_text(encoding="utf-8"), rel)
            if parsed["story_id"] in (None, sid):
                sources_found += 1
                cand_citations.extend(parsed["citations"])
                cand_decisions.extend(parsed["decisions"])
                admissions.extend(parsed["admissions"])
            else:
                logger.warning(
                    "fact_dossier ignoré (story_id %s ≠ %s)",
                    parsed["story_id"], sid,
                    extra={"component": "pipelines.evidence_backfill",
                           "operation": "_process_pack", "story_id": sid},
                )

        plan_path = self._resolve_plan(sid)
        if plan_path is not None:
            rel = str(plan_path.relative_to(self.project_path)).replace("\\", "/")
            parsed_plan = parse_plan(plan_path.read_text(encoding="utf-8"), rel)
            sources_found += 1
            cand_decisions.extend(parsed_plan["decisions"])
            cand_contracts.extend(parsed_plan["contracts"])

        story_path = self.stories_dir / f"{sid}.md"
        if story_path.exists():
            rel = str(story_path.relative_to(self.project_path)).replace("\\", "/")
            parsed_story = parse_story_rules(story_path.read_text(encoding="utf-8"), rel)
            if parsed_story["decisions"]:
                sources_found += 1
                cand_decisions.extend(parsed_story["decisions"])

        if sources_found == 0:
            report["no_source"].append(sid)
            admissions.append(
                "NO_SOURCE_AVAILABLE : aucun fact_dossier, plan ni section "
                "Règles d'affaires exploitable pour ce récit (backfill MLOOP-182-BE)."
            )

        return merge_and_maybe_write(
            self.project_path, sid, pack, pack_path, cand_decisions, cand_citations,
            cand_contracts, admissions, dry_run,
        )
