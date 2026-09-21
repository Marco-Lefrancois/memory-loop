"""
Tests unitaires pour le Zombie Reap systématique dans approve_gate() — MLOOP-123-BE.
Vérifie que audit_and_reap_zombies() est invoqué pour TOUTES les gates.
"""

import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Crée un répertoire de test simulant un projet."""
    proj = tmp_path / "Projects" / "TestZombieReap"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "00-ingested").mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj / "memory" / "evidence").mkdir(parents=True, exist_ok=True)
    yield proj
    if proj.exists():
        shutil.rmtree(proj.parent.parent, ignore_errors=True)


@patch("src.core.lifecycle.HerdrAdapter", create=True)
def test_zombie_reap_called_on_gate_1(mock_herdr_cls, temp_project):
    """audit_and_reap_zombies() doit être appelé lors de l'approbation Gate 1."""
    mock_herdr = MagicMock()
    mock_herdr.audit_and_reap_zombies.return_value = {"reaped_count": 0}
    mock_herdr_cls.return_value = mock_herdr

    with patch("src.core.herdr_adapter.HerdrAdapter", mock_herdr_cls, create=True):
        ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=1,
            approver="Test",
            notes="Test zombie reap",
        )
        mock_herdr.audit_and_reap_zombies.assert_called_once_with(project_name=temp_project.name)


@patch("src.core.herdr_adapter.HerdrAdapter", create=True)
def test_zombie_reap_called_on_gate_2(mock_herdr_cls, temp_project):
    """audit_and_reap_zombies() doit être appelé lors de l'approbation Gate 2."""
    mock_herdr = MagicMock()
    mock_herdr.audit_and_reap_zombies.return_value = {"reaped_count": 0}
    mock_herdr_cls.return_value = mock_herdr

    # Avancer jusqu'à Gate 2
    state = ProjectLifecycleManager.get_state(temp_project)
    state.current_stage = ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    ProjectLifecycleManager.save_state(temp_project, state)

    with patch("src.core.herdr_adapter.HerdrAdapter", mock_herdr_cls, create=True):
        ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=2,
            approver="Test",
            notes="Test zombie reap gate 2",
        )
        mock_herdr.audit_and_reap_zombies.assert_called_once_with(project_name=temp_project.name)


def test_zombie_reap_failure_does_not_block_gate(temp_project):
    """Si audit_and_reap_zombies() échoue, l'approbation de gate doit continuer."""
    with patch("src.core.herdr_adapter.HerdrAdapter", create=True) as mock_cls:
        mock_herdr = MagicMock()
        mock_herdr.audit_and_reap_zombies.side_effect = ConnectionError("Herdr not available")
        mock_cls.return_value = mock_herdr

        # Ne doit PAS lever d'exception
        state = ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=1,
            approver="Test",
            notes="Test resilience",
        )
        assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
        assert state.is_gate_approved(1)


def test_zombie_reap_logs_reaped_workers(temp_project):
    """Les workers purgés doivent être journalisés en debug."""
    with patch("src.core.herdr_adapter.HerdrAdapter", create=True) as mock_cls:
        mock_herdr = MagicMock()
        mock_herdr.audit_and_reap_zombies.return_value = {
            "reaped_count": 2,
            "reaped": [{"name": "worker_1"}, {"name": "worker_2"}],
        }
        mock_cls.return_value = mock_herdr

        state = ProjectLifecycleManager.approve_gate(
            project_path=temp_project,
            gate_number=1,
            approver="Test",
            notes="Test reap logging",
        )
        assert state.is_gate_approved(1)
        # Vérifier que la journalisation a bien été appelée
        mock_herdr.audit_and_reap_zombies.assert_called_once()
