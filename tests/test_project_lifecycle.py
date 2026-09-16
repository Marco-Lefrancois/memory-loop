"""
Tests unitaires pour le moteur de cycle de vie projet (ProjectLifecycleManager).
Conformité : ADR-0339 (Quality Gates) et ADR-0369 (Standards de Robustesse Senior).
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
    """Vérifie l'amorçage nominal en Phase 0 ou Phase 1 si SOW déjà présent."""
    state = ProjectLifecycleManager.get_state(temp_project)
    assert state.current_stage == ProjectLifecycleStage.STAGE_0_TSHIRT
    assert len(state.gates) == 0

    # Présence du SOW -> amorçage en STAGE_1_SOW
    sow_file = temp_project / "docs" / "01-architecture" / "SOW_TestProject.md"
    sow_file.write_text("# SOW Document", encoding="utf-8")
    
    # Supprimer l'état persistant pour forcer le ré-amorçage
    state_file = temp_project / "memory" / "lifecycle_state.json"
    state_file.unlink()
    
    new_state = ProjectLifecycleManager.get_state(temp_project)
    assert new_state.current_stage == ProjectLifecycleStage.STAGE_1_SOW


@pytest.mark.parametrize(
    "command,stage,expected_allowed",
    [
        # Commandes universelles toujours autorisées
        ("resume", ProjectLifecycleStage.STAGE_0_TSHIRT, True),
        ("vibe-check", ProjectLifecycleStage.STAGE_0_TSHIRT, True),
        ("guide", ProjectLifecycleStage.STAGE_1_SOW, True),
        ("sync", ProjectLifecycleStage.STAGE_1_SOW, True),
        ("lifecycle-status", ProjectLifecycleStage.STAGE_0_TSHIRT, True),
        
        # Commandes de cadrage SOW (autorisées dès Phase 0/1)
        ("to-sow", ProjectLifecycleStage.STAGE_0_TSHIRT, True),
        ("to-sow", ProjectLifecycleStage.STAGE_1_SOW, True),
        ("ingest", ProjectLifecycleStage.STAGE_0_TSHIRT, True),
        
        # Commandes de Phase 2 (PLAN / GRILL) interdites en Phase 0 et 1
        ("grill", ProjectLifecycleStage.STAGE_0_TSHIRT, False),
        ("grill", ProjectLifecycleStage.STAGE_1_SOW, False),
        ("grill", ProjectLifecycleStage.STAGE_2_PLAN_GRILL, True),
        ("to-tickets", ProjectLifecycleStage.STAGE_1_SOW, False),
        ("to-tickets", ProjectLifecycleStage.STAGE_2_PLAN_GRILL, True),
        ("focus", ProjectLifecycleStage.STAGE_1_SOW, False),
        ("focus", ProjectLifecycleStage.STAGE_2_PLAN_GRILL, True),
        
        # Commandes de Phase 3 (BUILD) interdites avant Phase 3
        ("self-dev", ProjectLifecycleStage.STAGE_2_PLAN_GRILL, False),
        ("self-dev", ProjectLifecycleStage.STAGE_3_BUILD, True),
        ("worker-spawn", ProjectLifecycleStage.STAGE_2_PLAN_GRILL, False),
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
    # Définir l'étape du projet
    state = ProjectLifecycleManager.get_state(temp_project)
    state.current_stage = stage
    ProjectLifecycleManager.save_state(temp_project, state)

    allowed, reason = ProjectLifecycleManager.can_execute_command(temp_project, command)
    assert allowed == expected_allowed, f"Échec sur {command} en {stage}: {reason}"


def test_approve_gate_nominal_progression(temp_project: Path) -> None:
    """Vérifie la progression séquentielle Gate 0 -> Gate 1 -> Gate 2."""
    state = ProjectLifecycleManager.get_state(temp_project)
    assert state.current_stage == ProjectLifecycleStage.STAGE_0_TSHIRT

    # Valider Gate 0 (Accord Enveloppe) -> Passage en STAGE_1_SOW
    state = ProjectLifecycleManager.approve_gate(
        project_path=temp_project,
        gate_number=0,
        approver="PO Lead",
        notes="Budget T-Shirt validé",
    )
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_SOW
    assert state.is_gate_approved(0)
    assert state.gates["0"].approver == "PO Lead"

    # Valider Gate 1 (Signature SOW) -> Passage en STAGE_2_PLAN_GRILL
    state = ProjectLifecycleManager.approve_gate(
        project_path=temp_project,
        gate_number=1,
        approver="Client Direct",
        notes="SOW signé le 16 septembre",
    )
    assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_GRILL
    assert state.is_gate_approved(1)


def test_approve_gate_out_of_order_raises(temp_project: Path) -> None:
    """Vérifie qu'on ne peut pas valider une porte hors de séquence (ex: Gate 2 alors qu'on est en Phase 0)."""
    with pytest.raises(ValueError, match="Impossible de valider la Gate 2"):
        ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=2,
            approver="Hacker",
            notes="Saut de phase illicite",
        )


def test_clean_premature_stories(temp_project: Path) -> None:
    """Vérifie la suppression radicale des stories sauvages et EvidencePacks en Phase SOW."""
    # Créer l'état en STAGE_1_SOW
    state = ProjectLifecycleManager.get_state(temp_project)
    state.current_stage = ProjectLifecycleStage.STAGE_1_SOW
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

    # Exécuter le nettoyage
    result = ProjectLifecycleManager.clean_premature_stories(temp_project)
    assert len(result["deleted_stories"]) == 2
    assert "SHOP-101.md" in result["deleted_stories"]
    assert "SHOP-102.md" in result["deleted_stories"]
    assert len(result["deleted_evidence"]) == 1

    # Vérifier l'état du disque
    assert not s1.exists()
    assert not s2.exists()
    assert readme.exists()  # Le README n'est pas touché
    assert not e1.exists()
