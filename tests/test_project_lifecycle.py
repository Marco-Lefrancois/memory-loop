"""
Tests unitaires pour le moteur de cycle de vie projet (ProjectLifecycleManager).
Conformité : ADR-0375 (Cycle de vie en 5 phases) et ADR-0369 (Standards de Robustesse Senior).
"""

from __future__ import annotations

import shutil
from pathlib import Path
import pytest

from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
    GATE_DEFINITIONS,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Crée un répertoire de test simulant un projet sous Projects/<nom>."""
    proj = tmp_path / "Projects" / "TestProject"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj / "memory" / "evidence").mkdir(parents=True, exist_ok=True)
    yield proj
    if proj.exists():
        shutil.rmtree(proj.parent.parent, ignore_errors=True)


def test_init_lifecycle_defaults(temp_project: Path) -> None:
    """Vérifie l'amorçage nominal en Phase 1 (INGEST) ou Phase 2 (PLAN) si SOW/specs déjà présents."""
    state = ProjectLifecycleManager.get_state(temp_project)
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_INGEST
    assert len(state.gates) == 0

    # Présence du SOW -> amorçage direct en STAGE_2_PLAN_ANALYSE (Fast-Track)
    sow_file = temp_project / "docs" / "01-architecture" / "SOW_TestProject.md"
    sow_file.write_text("# SOW Document", encoding="utf-8")
    
    # Supprimer l'état persistant pour forcer le ré-amorçage
    state_file = temp_project / "memory" / "lifecycle_state.json"
    state_file.unlink()
    
    new_state = ProjectLifecycleManager.get_state(temp_project)
    assert new_state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE


@pytest.mark.parametrize(
    "command,stage,expected_allowed",
    [
        # Commandes universelles toujours autorisées
        ("resume", ProjectLifecycleStage.STAGE_1_INGEST, True),
        ("vibe-check", ProjectLifecycleStage.STAGE_1_INGEST, True),
        ("guide", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("sync", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("lifecycle-status", ProjectLifecycleStage.STAGE_1_INGEST, True),
        
        # Commandes Phase 1 (INGEST)
        ("ingest", ProjectLifecycleStage.STAGE_1_INGEST, True),
        ("research", ProjectLifecycleStage.STAGE_1_INGEST, True),
        
        # Commandes Phase 2 (PLAN & ANALYSE) interdites en Phase 1
        ("to-tshirt", ProjectLifecycleStage.STAGE_1_INGEST, False),
        ("to-tshirt", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("to-sow", ProjectLifecycleStage.STAGE_1_INGEST, False),
        ("to-sow", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("grill-project", ProjectLifecycleStage.STAGE_1_INGEST, False),
        ("grill-project", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("grill", ProjectLifecycleStage.STAGE_1_INGEST, False),
        ("grill", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("to-tickets", ProjectLifecycleStage.STAGE_1_INGEST, False),
        ("to-tickets", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        ("focus", ProjectLifecycleStage.STAGE_1_INGEST, False),
        ("focus", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, True),
        
        # Commandes de Phase 3 (BUILD) interdites avant Phase 3
        ("self-dev", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, False),
        ("self-dev", ProjectLifecycleStage.STAGE_3_BUILD, True),
        ("worker-spawn", ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE, False),
        ("worker-spawn", ProjectLifecycleStage.STAGE_3_BUILD, True),
        
        # Commandes de Phase 5 (SHIP) interdites avant Phase 5
        ("jira_sync", ProjectLifecycleStage.STAGE_3_BUILD, False),
        ("jira_sync", ProjectLifecycleStage.STAGE_5_SHIP, True),
    ],
)
def test_can_execute_command_gating(
    temp_project: Path,
    command: str,
    stage: ProjectLifecycleStage,
    expected_allowed: bool,
) -> None:
    """Contrat de vérification des permissions de commandes par étape."""
    state = ProjectLifecycleManager.get_state(temp_project)
    state.current_stage = stage
    ProjectLifecycleManager.save_state(temp_project, state)

    allowed, reason = ProjectLifecycleManager.can_execute_command(temp_project, command)
    assert allowed == expected_allowed, f"Échec sur {command} en {stage}: {reason}"


def test_approve_gate_nominal_progression(temp_project: Path) -> None:
    """Vérifie la progression séquentielle Gate 1 -> Gate 2."""
    state = ProjectLifecycleManager.get_state(temp_project)
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_INGEST

    # Valider Gate 1 (Ingestion & Cadrage Initial Prêt) -> Passage en STAGE_2_PLAN_ANALYSE
    state = ProjectLifecycleManager.approve_gate(
        project_path=temp_project,
        gate_number=1,
        approver="Architecte Lead",
        notes="Ingestion et cadrage validés",
    )
    assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    assert state.is_gate_approved(1)
    assert state.gates["1"].approver == "Architecte Lead"

    # Valider Gate 2 (Definition of Ready - DoR) -> Passage en STAGE_3_BUILD
    state = ProjectLifecycleManager.approve_gate(
        project_path=temp_project,
        gate_number=2,
        approver="PO Lead",
        notes="Stories DoR 6/6 validées",
    )
    assert state.current_stage == ProjectLifecycleStage.STAGE_3_BUILD
    assert state.is_gate_approved(2)


def test_approve_gate_out_of_order_raises(temp_project: Path) -> None:
    """Vérifie qu'on ne peut pas valider une porte hors de séquence (ex: Gate 2 alors qu'on est en Phase 1)."""
    with pytest.raises(ValueError, match="Impossible de valider la Gate 2"):
        ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=2,
            approver="Hacker",
            notes="Saut de phase illicite",
        )


def test_clean_premature_stories(temp_project: Path) -> None:
    """Vérifie la suppression radicale des stories sauvages et EvidencePacks en Phase 1 INGEST."""
    state = ProjectLifecycleManager.get_state(temp_project)
    state.current_stage = ProjectLifecycleStage.STAGE_1_INGEST
    ProjectLifecycleManager.save_state(temp_project, state)

    # Créer des fichiers orphelins prématurés
    s1 = temp_project / "backlog" / "stories" / "SHOP-101.md"
    s1.write_text("# Premature Story 101", encoding="utf-8")
    s2 = temp_project / "backlog" / "stories" / "SHOP-102.md"
    s2.write_text("# Premature Story 102", encoding="utf-8")
    readme = temp_project / "backlog" / "stories" / "README.md"
    readme.write_text("# Keep README", encoding="utf-8")

    e1 = temp_project / "memory" / "evidence" / "SHOP-101_evidence.json"
    e1.write_text("{}", encoding="utf-8")

    # Exécuter le nettoyage avec confirmation explicite
    result = ProjectLifecycleManager.clean_premature_stories(temp_project, confirm=True)
    assert len(result["deleted_stories"]) == 2
    assert "SHOP-101.md" in result["deleted_stories"]
    assert "SHOP-102.md" in result["deleted_stories"]
    assert len(result["deleted_evidence"]) == 1

    # Vérifier l'état du disque
    assert not s1.exists()
    assert not s2.exists()
    assert readme.exists()  # Le README n'est pas touché
    assert not e1.exists()
