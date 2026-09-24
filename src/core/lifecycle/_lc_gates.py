"""
_lc_gates.py — GatesMixin : approbation des portes de gouvernance (ADR-0339/ADR-0375/ADR-0378/ADR-0383).
Méthodes : approve_gate, clean_premature_stories, _compute_file_sha256,
           _find_qa_certification_report, _compute_stage_deliverables_hash.
"""

from __future__ import annotations

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ._lc_logger import logger
from ._lc_models import (
    GATE_DEFINITIONS,
    STAGE_ORDER,
    GateApprovalRecord,
    ProjectLifecycleStage,
    ProjectLifecycleState,
    compute_file_sha256,
    compute_stage_deliverables_hash,
    find_qa_certification_report,
)


class GatesMixin:
    """Mixin : approbation des gates de gouvernance et nettoyage de backlog."""

    @classmethod
    def approve_gate(
        cls,
        project_path: Path,
        gate_number: int,
        approver: str,
        notes: str = "",
    ) -> ProjectLifecycleState:
        """Valide une Porte de Gouvernance et fait progresser le projet vers la phase suivante."""
        if gate_number not in GATE_DEFINITIONS:
            raise ValueError(f"Porte inconnue : Gate {gate_number}. Portes valides : 1 à 5.")
        t0 = time.perf_counter()
        state = cls.get_state(project_path)
        gate_def = GATE_DEFINITIONS[gate_number]
        from_status_start = state.current_stage.value
        logger.info(
            f"[LIFECYCLE] Début approbation Gate {gate_number} par '{approver}'.",
            extra={
                "project": project_path.name,
                "gate": gate_number,
                "from_status": from_status_start,
                "phase": state.canonical_stage.value,
            },
        )
        # Vérification d'alignement de phase (support canonique)
        expected_stage = gate_def["from_stage"]
        current_canonical = state.canonical_stage
        expected_canonical = (
            ProjectLifecycleStage.STAGE_1_INGEST
            if expected_stage
            in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
            else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
            if expected_stage
            in (
                ProjectLifecycleStage.STAGE_1_SOW,
                ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
                ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
            )
            else expected_stage
        )
        if current_canonical != expected_canonical:
            raise ValueError(
                f"Impossible de valider la Gate {gate_number} : le projet est en étape '{state.current_stage.value}', "
                f"alors que cette porte requiert d'être en étape '{expected_stage.value}'."
            )
        # Validations Gate 0/1 : Anti-Ghost-Bias (ADR-0378 / Check 13)
        if gate_number in (0, 1):
            stories_dir = project_path / "backlog" / "stories"
            if stories_dir.exists():
                premature = [
                    sf.name for sf in stories_dir.glob("*.md") if sf.name.lower() != "readme.md"
                ]
                if premature:
                    raise ValueError(
                        f"Approbation de Gate {gate_number} refusée (Check 13 / Anti-Ghost-Bias) : "
                        f"des récits physiques ({len(premature)}) existent déjà sous backlog/stories/ : {premature[:3]}. "
                        f"En Phase 1 (INGEST & EXPLORE), la création de stories est formellement interdite. "
                        f"Lancez 'python src/swarm.py lifecycle-clean --confirm' pour assainir le backlog avant de valider la Gate 1."
                    )
            ref_dir = project_path / "reference"
            raw_files = [f for f in ref_dir.rglob("*") if f.is_file()] if ref_dir.exists() else []
            ingested_dir = project_path / "docs" / "00-ingested"
            ingested_files = list(ingested_dir.glob("*.md")) if ingested_dir.exists() else []
            manifest_file = ingested_dir / "source_manifest.json" if ingested_dir.exists() else None
            has_ingested = bool(ingested_files or (manifest_file and manifest_file.exists()))
            if raw_files and not has_ingested:
                raise ValueError(
                    f"Approbation de Gate {gate_number} refusée : des fichiers bruts sont présents dans reference/ "
                    f"mais aucun document normalisé n'a été trouvé sous docs/00-ingested/ pour '{project_path.name}'. "
                    f"Lancez 'python src/swarm.py ingest --project {project_path.name}' avant d'approuver la Gate 1."
                )
        # Validation Gate 4 (ADR-0383 / MLOOP-092-BE)
        if gate_number == 4:
            from src.core.gate4_validator import validate_gate4_approval

            validate_gate4_approval(project_path, approver)
        # Nettoyage workers zombies (Zero Zombie Policy - ADR-0306 / ADR-0345)
        try:
            from src.core.herdr_adapter import HerdrAdapter

            herdr = HerdrAdapter()
            reap_result = herdr.audit_and_reap_zombies(project_name=project_path.name)
            reaped_count = reap_result.get("reaped_count", 0)
            if reaped_count > 0:
                logger.debug(
                    f"[LIFECYCLE] {reaped_count} worker(s) zombie(s) purgé(s) avant Gate {gate_number}.",
                    extra={"project": project_path.name, "reaped_count": reaped_count},
                )
        except Exception as reap_err:
            logger.debug(
                f"[LIFECYCLE] Zombie reap non critique ignoré avant Gate {gate_number} : {reap_err}",
                exc_info=True,
                extra={"project": project_path.name, "gate": gate_number},
            )
        checksum = compute_stage_deliverables_hash(project_path, state.current_stage)
        qa_cert_hash: Optional[str] = None
        if gate_number == 4:
            qa_report_path = find_qa_certification_report(project_path)
            if qa_report_path is not None:
                qa_cert_hash = compute_file_sha256(qa_report_path)
                logger.info(
                    f"[LIFECYCLE] Hash SHA-256 du rapport QA calculé : {qa_cert_hash[:16]}...",
                    extra={"project": project_path.name, "qa_report": str(qa_report_path)},
                )
            else:
                logger.warning(
                    "[LIFECYCLE] Aucun rapport qa_certification_report.json trouvé pour le calcul du hash.",
                    extra={"project": project_path.name},
                )
        record = GateApprovalRecord(
            gate_number=gate_number,
            gate_name=gate_def["name"],
            approver=approver,
            notes=notes,
            checksum=checksum,
            qa_certification_hash=qa_cert_hash,
        )
        state.gates[str(gate_number)] = record
        next_stage = gate_def["to_stage"]
        if next_stage:
            state.current_stage = next_stage
        cls.save_state(project_path, state)
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.info(
            f"[LIFECYCLE] Gate {gate_number} approuvée par '{approver}'. "
            f"Projet '{project_path.name}' transite vers '{state.current_stage.value}'.",
            extra={
                "project": project_path.name,
                "gate": gate_number,
                "from_status": from_status_start,
                "to_status": state.current_stage.value,
                "duration_ms": duration_ms,
                "phase": state.canonical_stage.value,
            },
        )
        return state

    @classmethod
    def clean_premature_stories(cls, project_path: Path, confirm: bool = False) -> Dict[str, Any]:
        """Archive de manière réversible les stories prématurées et leurs EvidencePacks (ADR-0339/L-08)."""
        _e: Dict[str, Any] = {
            "deleted_stories": [],
            "deleted_evidence": [],
            "archived_stories": [],
            "archived_evidence": [],
            "archive_dir": None,
        }
        if not confirm:
            logger.warning(
                f"[LIFECYCLE-CLEAN] Nettoyage refusé pour '{project_path.name}'.",
                extra={"project": project_path.name},
            )
            return {
                **_e,
                "status": "refused",
                "message": "Nettoyage refusé : confirmation explicite requise (passez --confirm).",
            }
        state = cls.get_state(project_path)
        if state.canonical_stage != ProjectLifecycleStage.STAGE_1_INGEST:
            return {
                **_e,
                "status": "noop",
                "message": "Le projet est en Phase 2 ou supérieure. Aucune suppression de story requise.",
            }
        deleted_stories: list = []
        deleted_evidence: list = []
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_dir = project_path / "memory" / "archive" / "premature_stories" / timestamp_str
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            for sf in list(stories_dir.glob("*.md")):
                if sf.name.lower() != "readme.md":
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    target_dest = archive_dir / sf.name
                    shutil.move(str(sf), str(target_dest))
                    deleted_stories.append(sf.name)
                    logger.warning(
                        f"[LIFECYCLE-CLEAN] Story archivée : {sf.name} -> {target_dest}",
                        extra={
                            "project": project_path.name,
                            "file": sf.name,
                            "archive": str(target_dest),
                        },
                    )
        evidence_dir = project_path / "memory" / "evidence"
        if evidence_dir.exists():
            ev_glob = list(evidence_dir.glob("*_evidence.json")) + list(
                evidence_dir.glob("*_fact_dossier.md")
            )
            for ef in ev_glob:
                archive_dir.mkdir(parents=True, exist_ok=True)
                target_dest = archive_dir / ef.name
                shutil.move(str(ef), str(target_dest))
                deleted_evidence.append(ef.name)
                logger.warning(
                    f"[LIFECYCLE-CLEAN] Preuve archivée : {ef.name} -> {target_dest}",
                    extra={
                        "project": project_path.name,
                        "file": ef.name,
                        "archive": str(target_dest),
                    },
                )
        backlog_file = project_path / "backlog" / "sprint_backlog.md"
        if backlog_file.exists():
            try:
                with open(backlog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                for kw in ["IN_ANALYZE", "READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV"]:
                    content = content.replace(kw, "OPEN")
                with open(backlog_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.debug(
                    f"Erreur mise à jour sprint_backlog.md : {e}",
                    exc_info=True,
                    extra={"project": project_path.name, "phase": "STAGE_1_INGEST"},
                )
        has_items = bool(deleted_stories or deleted_evidence)
        return {
            "status": "completed",
            "deleted_stories": deleted_stories,
            "deleted_evidence": deleted_evidence,
            "archived_stories": deleted_stories,
            "archived_evidence": deleted_evidence,
            "archive_dir": str(archive_dir) if has_items else None,
            "message": (
                f"Nettoyage sécurisé effectué : {len(deleted_stories)} story(ies) et "
                f"{len(deleted_evidence)} preuve(s) archivée(s) vers {archive_dir}."
                if has_items
                else "Aucune story prématurée à nettoyer."
            ),
        }

    # Aliases de rétrocompatibilité (méthodes statiques proxyfiant les helpers module-level)
    _compute_file_sha256 = staticmethod(compute_file_sha256)
    _find_qa_certification_report = staticmethod(find_qa_certification_report)

    @classmethod
    def _compute_stage_deliverables_hash(
        cls, project_path: Path, stage: ProjectLifecycleStage
    ) -> str:
        return compute_stage_deliverables_hash(project_path, stage)
