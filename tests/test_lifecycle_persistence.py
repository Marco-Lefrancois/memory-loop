"""
Tests TDD de persistance, idempotence et protection anti-régression du cycle de vie projet.
Conformité : ADR-0375 (Cycle de vie en 5 phases) et ADR-0369 (Standards de Robustesse Senior).
Lacune : L-05 (Corruption d'état lifecycle par worker/sync/init).
"""

import json
import shutil
from pathlib import Path
import pytest

from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
    GateApprovalRecord,
    ProjectLifecycleState,
)


@pytest.fixture
def active_phase2_project(tmp_path: Path) -> Path:
    """Crée un projet temporaire avec un état sain en STAGE_2_PLAN_ANALYSE et Gate 1 approuvée."""
    proj = tmp_path / "Projects" / "TestShopifyProject"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj / "memory" / "evidence").mkdir(parents=True, exist_ok=True)

    # Initialisation initiale en STAGE_1_INGEST (pas de SOW ni specs au départ)
    state = ProjectLifecycleManager.init_lifecycle(proj)
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_INGEST

    # Valider Gate 1 -> passage en STAGE_2_PLAN_ANALYSE
    state = ProjectLifecycleManager.approve_gate(
        project_path=proj,
        gate_number=1,
        approver="PO Lead",
        notes="Ingestion et cadrage initial approuvés",
    )
    assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    assert state.is_gate_approved(1)

    # Création d'un SOW pour simuler le cadrage amont achevé
    sow_file = proj / "docs" / "01-architecture" / "SOW_TestShopifyProject.md"
    sow_file.write_text("# SOW Validé", encoding="utf-8")

    yield proj

    if proj.exists():
        shutil.rmtree(proj.parent.parent, ignore_errors=True)


def test_init_lifecycle_preserves_existing_advanced_state(active_phase2_project: Path) -> None:
    """Vérifie que init_lifecycle ne réinitialise JAMAIS un état existant plus avancé."""
    # Simulation d'un appel init intempestif (par exemple exécuté par un worker)
    state_after_reinit = ProjectLifecycleManager.init_lifecycle(active_phase2_project, force=False)

    # L'état DOIT être préservé en STAGE_2_PLAN_ANALYSE avec Gate 1
    assert state_after_reinit.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    assert state_after_reinit.is_gate_approved(1)
    assert "1" in state_after_reinit.gates

    # Vérification sur disque
    state_file = ProjectLifecycleManager.get_state_file(active_phase2_project)
    disk_data = json.loads(state_file.read_text(encoding="utf-8"))
    assert disk_data["current_stage"] == "STAGE_2_PLAN_ANALYSE"
    assert "1" in disk_data["gates"]


def test_save_state_prevents_unauthorized_regression(active_phase2_project: Path) -> None:
    """Vérifie que save_state refuse d'écraser un état avancé avec un état régressé sans accord explicite."""
    # Création d'un état régressé (STAGE_1_INGEST sans gates)
    regressed_state = ProjectLifecycleState(
        project_name=active_phase2_project.name,
        current_stage=ProjectLifecycleStage.STAGE_1_INGEST,
        gates={},
    )

    # La tentative de sauvegarde d'une régression doit lever ValueError
    with pytest.raises(ValueError, match="Régression de cycle de vie interdite"):
        ProjectLifecycleManager.save_state(
            active_phase2_project, regressed_state, allow_regression=False
        )

    # L'état sur disque ne doit pas avoir bougé
    persisted = ProjectLifecycleManager.get_state(active_phase2_project)
    assert persisted.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    assert persisted.is_gate_approved(1)


def test_corrupted_state_backed_up_and_reinitialized(tmp_path: Path) -> None:
    """Vérifie qu'un fichier d'état corrompu est sauvegardé en .corrupt.<timestamp> et réamorcé proprement."""
    proj = tmp_path / "Projects" / "CorruptProj"
    proj.mkdir(parents=True, exist_ok=True)
    memory_dir = proj / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Fichier JSON corrompu
    state_file = memory_dir / "lifecycle_state.json"
    state_file.write_text('{ "corrupted_json": [incomplete', encoding="utf-8")

    # get_state doit rattraper l'erreur, archiver le fichier corrompu et réamorcer
    state = ProjectLifecycleManager.get_state(proj)
    assert state is not None
    assert state.project_name == "CorruptProj"

    # Vérifier la présence du fichier de sauvegarde .corrupt
    corrupt_backups = list(memory_dir.glob("lifecycle_state.json.corrupt.*"))
    assert len(corrupt_backups) == 1
    assert corrupt_backups[0].read_text(encoding="utf-8") == '{ "corrupted_json": [incomplete'


def test_resume_preserves_lifecycle_state(active_phase2_project: Path) -> None:
    """Vérifie que l'appel de run_session_resume ne modifie pas l'état lifecycle."""
    from src.pipelines.session_resume import run_session_resume

    # Exécution de resume
    run_session_resume(active_phase2_project.name)

    # L'état doit être strictement préservé
    state = ProjectLifecycleManager.get_state(active_phase2_project)
    assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    assert state.is_gate_approved(1)
