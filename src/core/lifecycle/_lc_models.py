"""
_lc_models.py — Modèles de données du cycle de vie mLoop (ADR-0339/PROJECT_LIFECYCLE_STAGES.md).
Contient : ProjectLifecycleStage, STAGE_ORDER, STAGE_NAMES, GATE_DEFINITIONS,
           COMMAND_MIN_STAGE, WORKER_TASK_TYPE_MIN_STAGE, GateApprovalRecord,
           ProjectLifecycleState, et les helpers statiques SHA-256/QA.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectLifecycleStage(str, Enum):
    """Les 5 phases séquentielles officielles du cycle de vie mLoop (ADR-0375)."""

    STAGE_1_INGEST = "STAGE_1_INGEST"  # Phase 1 : INGEST & EXPLORE
    STAGE_2_PLAN_ANALYSE = "STAGE_2_PLAN_ANALYSE"  # Phase 2 : PLAN & ANALYSE
    STAGE_3_BUILD = "STAGE_3_BUILD"  # Phase 3 : BUILD & DEV
    STAGE_4_VALIDATE = "STAGE_4_VALIDATE"  # Phase 4 : VALIDATE & QA
    STAGE_5_SHIP = "STAGE_5_SHIP"  # Phase 5 : SHIP & SYNC

    # Rétro-compatibilité legacy ADR-0339
    STAGE_0_TSHIRT = "STAGE_0_TSHIRT"
    STAGE_1_SOW = "STAGE_1_SOW"
    STAGE_2_PLAN_GRILL = "STAGE_2_PLAN_GRILL"


# Ordre strict des 5 phases canoniques (ADR-0375)
STAGE_ORDER: List[ProjectLifecycleStage] = [
    ProjectLifecycleStage.STAGE_1_INGEST,
    ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    ProjectLifecycleStage.STAGE_3_BUILD,
    ProjectLifecycleStage.STAGE_4_VALIDATE,
    ProjectLifecycleStage.STAGE_5_SHIP,
]

STAGE_NAMES: Dict[ProjectLifecycleStage, str] = {
    ProjectLifecycleStage.STAGE_1_INGEST: "Phase 1 : INGEST & EXPLORE (Amorçage & Ingestion)",
    ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE: "Phase 2 : PLAN & ANALYSE (Planification & Spécifications)",
    ProjectLifecycleStage.STAGE_3_BUILD: "Phase 3 : BUILD (Développement Physique)",
    ProjectLifecycleStage.STAGE_4_VALIDATE: "Phase 4 : VALIDATE (Assurance Qualité & Evals)",
    ProjectLifecycleStage.STAGE_5_SHIP: "Phase 5 : SHIP & SYNC (Distribution & Clôture)",
    # Aliases legacy
    ProjectLifecycleStage.STAGE_0_TSHIRT: "Phase 1 : INGEST & EXPLORE (Amorçage & Ingestion)",
    ProjectLifecycleStage.STAGE_1_SOW: "Phase 2 : PLAN & ANALYSE (Planification & Spécifications)",
    ProjectLifecycleStage.STAGE_2_PLAN_GRILL: "Phase 2 : PLAN & ANALYSE (Planification & Spécifications)",
}

GATE_DEFINITIONS: Dict[int, Dict[str, Any]] = {
    0: {
        "name": "Gate 0 : Cadrage Initial (Alias Gate 1)",
        "from_stage": ProjectLifecycleStage.STAGE_1_INGEST,
        "to_stage": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        "description": "Validation d'amorçage (alias rétro-compatible de Gate 1).",
        "requires_human": False,
    },
    1: {
        "name": "Gate 1 : Ingestion & Cadrage Initial Prêt",
        "from_stage": ProjectLifecycleStage.STAGE_1_INGEST,
        "to_stage": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        "description": "Validation que les sources brutes sont ingérées et que le projet peut être planifié et analysé.",
        "requires_human": False,
    },
    2: {
        "name": "Gate 2 : Definition of Ready (DoR)",
        "from_stage": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        "to_stage": ProjectLifecycleStage.STAGE_3_BUILD,
        "description": "Validation DoR sans ambiguïté par WikiFix & Sentinel (4 Piliers Gherkin + EvidencePacks).",
        "requires_human": False,
    },
    3: {
        "name": "Gate 3 : Definition of Done (DoD)",
        "from_stage": ProjectLifecycleStage.STAGE_3_BUILD,
        "to_stage": ProjectLifecycleStage.STAGE_4_VALIDATE,
        "description": "Tests unitaires et d'intégration 100% au vert.",
        "requires_human": False,
    },
    4: {
        "name": "Gate 4 : Conformité Métier & Recette QA",
        "from_stage": ProjectLifecycleStage.STAGE_4_VALIDATE,
        "to_stage": ProjectLifecycleStage.STAGE_5_SHIP,
        "description": "Audit contradictoire Sentinel / QA Lead approuvé.",
        "requires_human": True,
    },
    5: {
        "name": "Gate 5 : Clôture de Cycle & Synchronisation",
        "from_stage": ProjectLifecycleStage.STAGE_5_SHIP,
        "to_stage": None,
        "description": "Synchronisation Jira et Git réussie, archivage mémoire scellé.",
        "requires_human": True,
    },
}

# Matrice des restrictions de commandes par phase minimale requise (ADR-0375)
COMMAND_MIN_STAGE: Dict[str, ProjectLifecycleStage] = {
    # Phase 1 : INGEST & EXPLORE
    "ingest": ProjectLifecycleStage.STAGE_1_INGEST,
    "research": ProjectLifecycleStage.STAGE_1_INGEST,
    "markitdown_convert": ProjectLifecycleStage.STAGE_1_INGEST,
    "crawl": ProjectLifecycleStage.STAGE_1_INGEST,
    "extract": ProjectLifecycleStage.STAGE_1_INGEST,
    "agentic-extract": ProjectLifecycleStage.STAGE_1_INGEST,
    "notebooklm": ProjectLifecycleStage.STAGE_1_INGEST,
    "svg-optimize": ProjectLifecycleStage.STAGE_1_INGEST,
    "svg-ocr": ProjectLifecycleStage.STAGE_1_INGEST,
    "csv-normalize": ProjectLifecycleStage.STAGE_1_INGEST,
    "csv-validate": ProjectLifecycleStage.STAGE_1_INGEST,
    "lifecycle-status": ProjectLifecycleStage.STAGE_1_INGEST,
    "lifecycle-clean": ProjectLifecycleStage.STAGE_1_INGEST,
    "gate-approve": ProjectLifecycleStage.STAGE_1_INGEST,
    # Phase 2 : PLAN & ANALYSE
    "to-tshirt": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "to-sow": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "grill-project": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "focus": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "grill": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "to-spec": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "to-tickets": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "archify": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "chunk": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "hyper-query": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "wayfinder": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "struct-check": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "rubber-duck": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "multi-draft": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "worker-status": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "worker-close": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "worker-harvest": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    # Phase 3 : BUILD & DEV
    "self-dev": ProjectLifecycleStage.STAGE_3_BUILD,
    "confidence": ProjectLifecycleStage.STAGE_3_BUILD,
    "worker-spawn": ProjectLifecycleStage.STAGE_3_BUILD,
    "code-impact": ProjectLifecycleStage.STAGE_3_BUILD,
    "code-affected": ProjectLifecycleStage.STAGE_3_BUILD,
    # Phase 4 : VALIDATE & QA
    "aoep": ProjectLifecycleStage.STAGE_4_VALIDATE,
    "eval": ProjectLifecycleStage.STAGE_4_VALIDATE,
    "audit-loop": ProjectLifecycleStage.STAGE_4_VALIDATE,
    "validate-sprint": ProjectLifecycleStage.STAGE_4_VALIDATE,
    # Phase 5 : SHIP & SYNC
    "jira-sync": ProjectLifecycleStage.STAGE_5_SHIP,
    "jira_sync": ProjectLifecycleStage.STAGE_5_SHIP,
    "cycle-status": ProjectLifecycleStage.STAGE_5_SHIP,
}

# Matrice des restrictions par type de tâche pour les workers Herdr (ADR-0375)
WORKER_TASK_TYPE_MIN_STAGE: Dict[str, ProjectLifecycleStage] = {
    "deepening": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "deepsearch": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "validation": ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
    "build": ProjectLifecycleStage.STAGE_3_BUILD,
    "compaction": ProjectLifecycleStage.STAGE_3_BUILD,
}


class GateApprovalRecord(BaseModel):
    """Enregistrement infalsifiable d'approbation d'une Porte de Gouvernance."""

    gate_number: int
    gate_name: str
    approved_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    approver: str
    notes: str = ""
    checksum: str = ""
    qa_certification_hash: Optional[str] = None


class ProjectLifecycleState(BaseModel):
    """État persistant et canonique du cycle de vie d'un projet client (SSOT)."""

    project_name: str
    current_stage: ProjectLifecycleStage = ProjectLifecycleStage.STAGE_1_INGEST
    gates: Dict[str, GateApprovalRecord] = Field(default_factory=dict)
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def canonical_stage(self) -> ProjectLifecycleStage:
        if self.current_stage in (
            ProjectLifecycleStage.STAGE_0_TSHIRT,
            ProjectLifecycleStage.STAGE_1_INGEST,
        ):
            return ProjectLifecycleStage.STAGE_1_INGEST
        if self.current_stage in (
            ProjectLifecycleStage.STAGE_1_SOW,
            ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
            ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        ):
            return ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
        return self.current_stage

    @property
    def stage_index(self) -> int:
        return STAGE_ORDER.index(self.canonical_stage)

    def is_gate_approved(self, gate_number: int) -> bool:
        return str(gate_number) in self.gates


# ---------------------------------------------------------------------------
# Helpers statiques partagés (SHA-256, QA report, livrables)
# ---------------------------------------------------------------------------


def compute_file_sha256(file_path: Path) -> str:
    """Calcule le hash SHA-256 d'un fichier (ADR-0369)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def find_qa_certification_report(project_path: Path) -> Optional[Path]:
    """Recherche qa_certification_report.json dans les emplacements canoniques."""
    for candidate in [
        project_path / "memory" / "evidence" / "qa_certification_report.json",
        project_path / "qa_certification_report.json",
    ]:
        if candidate.exists():
            return candidate
    return None


def compute_stage_deliverables_hash(project_path: Path, stage: "ProjectLifecycleStage") -> str:
    """Calcule un SHA-256 déterministe sur les livrables clés de la phase courante."""
    h = hashlib.sha256()
    files_to_hash: List[Path] = []
    canonical = (
        ProjectLifecycleStage.STAGE_1_INGEST
        if stage in (ProjectLifecycleStage.STAGE_0_TSHIRT, ProjectLifecycleStage.STAGE_1_INGEST)
        else ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
        if stage
        in (
            ProjectLifecycleStage.STAGE_1_SOW,
            ProjectLifecycleStage.STAGE_2_PLAN_GRILL,
            ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE,
        )
        else stage
    )
    if canonical == ProjectLifecycleStage.STAGE_1_INGEST:
        ingested_dir = project_path / "docs" / "00-ingested"
        if ingested_dir.exists():
            manifest = ingested_dir / "source_manifest.json"
            if manifest.exists():
                files_to_hash.append(manifest)
            files_to_hash.extend(sorted(ingested_dir.glob("*.md")))
        assets_dir = project_path / "docs" / "05-assets"
        if assets_dir.exists():
            files_to_hash.extend(sorted(f for f in assets_dir.rglob("*.svg") if f.is_file()))
        lexicon = project_path / "docs" / "04-transverse" / "lexique_domaine.md"
        if lexicon.exists():
            files_to_hash.append(lexicon)
    elif canonical == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE:
        arch_dir = project_path / "docs" / "01-architecture"
        if arch_dir.exists():
            files_to_hash.extend(sorted(arch_dir.glob("TSHIRT_SIZE_*.md")))
            files_to_hash.extend(sorted(arch_dir.glob("SOW_*.md")))
        backlog = project_path / "backlog" / "sprint_backlog.md"
        if backlog.exists():
            files_to_hash.append(backlog)
        stories_dir = project_path / "backlog" / "stories"
        if stories_dir.exists():
            files_to_hash.extend(sorted(stories_dir.glob("*.md")))
    for f in files_to_hash:
        h.update(f.read_bytes())
    return h.hexdigest()[:16] if files_to_hash else "empty_phase_deliverable"
