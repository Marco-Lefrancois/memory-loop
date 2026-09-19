"""
Tests unitaires pour la Phase 1 : INGEST & EXPLORE et la Gate 1 (ADR-0378).
Vérifie :
- Initialisation de projet (handle_init & init_lifecycle en STAGE_1_INGEST)
- Respect strict de reference/ sans sous-readme (ADR-0100)
- Ingestion propre avec gestion du dossier reference/ vide
- Blocage strict de Gate 1 en cas de stories prématurées (Check 13 / Anti-Ghost-Bias)
- Blocage de Gate 1 si des sources brutes ne sont pas ingérées
- Approbation nominale de Gate 1 et transition vers STAGE_2_PLAN_ANALYSE
- Calcul déterministe du hash des livrables de Phase 1
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
import pytest

from src.core.layout import ProjectLayout
from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
    GATE_DEFINITIONS,
)
from src.pipelines.ingest import run_ingest
from src.state import LoopState


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Crée un projet temporaire pour tester la Phase 1."""
    proj = tmp_path / "Projects" / "TestPhase1Project"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / ProjectLayout.REFERENCE).mkdir(parents=True, exist_ok=True)
    for subdir in ProjectLayout.DOCS_SUBDIRS:
        (proj / ProjectLayout.DOCS / subdir).mkdir(parents=True, exist_ok=True)
    (proj / ProjectLayout.BACKLOG / "stories").mkdir(parents=True, exist_ok=True)
    (proj / ProjectLayout.MEMORY).mkdir(parents=True, exist_ok=True)
    yield proj
    if proj.exists():
        shutil.rmtree(proj.parent.parent, ignore_errors=True)


def test_phase_1_initial_stage(temp_project: Path) -> None:
    """Vérifie que l'initialisation place le projet en STAGE_1_INGEST sans portes approuvées."""
    state = ProjectLifecycleManager.init_lifecycle(temp_project, initial_stage=ProjectLifecycleStage.STAGE_1_INGEST)
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_INGEST
    assert len(state.gates) == 0


def test_reference_dir_has_no_subreadme(temp_project: Path) -> None:
    """Vérifie l'absence de sous-readme dans reference/ (ADR-0100 forbidden_subreadmes)."""
    ref_dir = temp_project / ProjectLayout.REFERENCE
    readmes = list(ref_dir.glob("*.md"))
    assert len(readmes) == 0, f"reference/ ne doit contenir aucun fichier markdown : {readmes}"


def test_ingest_empty_reference_clean_exit(temp_project: Path) -> None:
    """Vérifie que run_ingest sur reference/ vide s'arrête proprement sans générer de faux manifeste."""
    state = LoopState(project_name=temp_project.name)
    result_state = run_ingest(temp_project.name, state, temp_project)
    ingested_dir = temp_project / ProjectLayout.DOCS / ProjectLayout.DOCS_INGESTED
    manifest = ingested_dir / ProjectLayout.SOURCE_MANIFEST
    assert not manifest.exists(), "source_manifest.json ne doit pas être généré si reference/ est vide."


def test_gate_1_blocks_on_premature_stories_check_13(temp_project: Path) -> None:
    """Vérifie que Gate 1 est rejetée si des User Stories existent sous backlog/stories/ (Check 13)."""
    ProjectLifecycleManager.init_lifecycle(temp_project, initial_stage=ProjectLifecycleStage.STAGE_1_INGEST)
    
    # Création d'une story prématurée sous backlog/stories/
    story_file = temp_project / ProjectLayout.BACKLOG / "stories" / "STORY-001.md"
    story_file.write_text("# Récit Prématuré", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=1,
            approver="QA Lead",
        )
    assert "Check 13" in str(excinfo.value)
    assert "backlog/stories" in str(excinfo.value)


def test_gate_1_blocks_when_raw_files_not_ingested(temp_project: Path) -> None:
    """Vérifie que Gate 1 bloque si des fichiers bruts sont dans reference/ mais rien n'a été ingéré."""
    ProjectLifecycleManager.init_lifecycle(temp_project, initial_stage=ProjectLifecycleStage.STAGE_1_INGEST)
    
    # Dépôt d'un fichier brut client dans reference/
    raw_file = temp_project / ProjectLayout.REFERENCE / "cahier_des_charges.docx"
    raw_file.write_text("Spécifications brutes du client", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=1,
            approver="PO Lead",
        )
    assert "fichiers bruts sont présents dans reference/" in str(excinfo.value)


def test_gate_1_nominal_approval(temp_project: Path) -> None:
    """Vérifie l'approbation nominale de Gate 1 quand les documents ingérés sont présents et 0 story."""
    ProjectLifecycleManager.init_lifecycle(temp_project, initial_stage=ProjectLifecycleStage.STAGE_1_INGEST)
    
    # Simulation de documents ingérés valides
    ingested_dir = temp_project / ProjectLayout.DOCS / ProjectLayout.DOCS_INGESTED
    ingested_doc = ingested_dir / "cahier_des_charges.md"
    ingested_doc.write_text("# Cahier des Charges Normalisé\n\nContenu extrait.", encoding="utf-8")

    manifest = ingested_dir / ProjectLayout.SOURCE_MANIFEST
    manifest.write_text(json.dumps({"manifest_version": "1.0.0", "sources": []}), encoding="utf-8")

    state = ProjectLifecycleManager.approve_gate(
        project_path=temp_project,
        gate_number=1,
        approver="Senior Architect",
        notes="Ingestion terminée et validée sans anomalie.",
    )

    assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    assert state.is_gate_approved(1)
    assert state.gates["1"].approver == "Senior Architect"
    assert state.gates["1"].checksum != "empty_phase_deliverable"


def test_phase_1_deliverables_hash(temp_project: Path) -> None:
    """Vérifie que le hash de Phase 1 capture les livrables d'ingestion et change lors d'un ajout."""
    ProjectLifecycleManager.init_lifecycle(temp_project, initial_stage=ProjectLifecycleStage.STAGE_1_INGEST)
    
    ingested_dir = temp_project / ProjectLayout.DOCS / ProjectLayout.DOCS_INGESTED
    doc = ingested_dir / "spec.md"
    doc.write_text("# Spec 1", encoding="utf-8")

    hash_1 = ProjectLifecycleManager._compute_stage_deliverables_hash(temp_project, ProjectLifecycleStage.STAGE_1_INGEST)
    assert hash_1 != "empty_phase_deliverable"

    # Modification d'un livrable -> le hash doit changer
    doc.write_text("# Spec 1 Modifiée avec de nouvelles exigences", encoding="utf-8")
    hash_2 = ProjectLifecycleManager._compute_stage_deliverables_hash(temp_project, ProjectLifecycleStage.STAGE_1_INGEST)
    assert hash_1 != hash_2
