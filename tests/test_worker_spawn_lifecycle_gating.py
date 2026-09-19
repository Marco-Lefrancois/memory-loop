"""
Tests TDD pour la gouvernance fine de worker-spawn selon le task-type (Option 1).
Conformité : ADR-0339 (Quality Gates) et ADR-0369 (Standards de Robustesse Senior).
Lacune : L-07 (worker-spawn bloqué en Phase 2 pour les tâches de cadrage/analyse).
"""

import shutil
from pathlib import Path
import pytest

from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
    WORKER_TASK_TYPE_MIN_STAGE,
)


@pytest.fixture
def phase2_project(tmp_path: Path) -> Path:
    """Crée un projet temporaire en STAGE_2_PLAN_ANALYSE."""
    proj = tmp_path / "Projects" / "Phase2Project"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj / "memory").mkdir(parents=True, exist_ok=True)

    state = ProjectLifecycleManager.init_lifecycle(proj)
    state = ProjectLifecycleManager.approve_gate(
        project_path=proj,
        gate_number=1,
        approver="PO Lead",
    )
    assert state.current_stage == ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE
    yield proj
    if proj.exists():
        shutil.rmtree(proj.parent.parent, ignore_errors=True)


@pytest.mark.parametrize(
    "task_type,expected_allowed",
    [
        ("deepening", True),
        ("deepsearch", True),
        ("validation", True),
        ("build", False),
        ("compaction", False),
        (None, False),
    ],
)
def test_worker_spawn_phase2_gating_by_task_type(
    phase2_project: Path, task_type: str, expected_allowed: bool
) -> None:
    """En Phase 2 (STAGE_2_PLAN_GRILL), seules les tâches d'analyse documentaire sont autorisées."""
    allowed, reason = ProjectLifecycleManager.can_execute_command(
        phase2_project, "worker-spawn", task_type=task_type
    )
    assert allowed == expected_allowed, f"Échec pour task_type='{task_type}': {reason}"


def test_worker_spawn_phase3_allows_build(phase2_project: Path) -> None:
    """En Phase 3 (STAGE_3_BUILD), build et sans task-type sont autorisés."""
    # Simuler passage en STAGE_3_BUILD
    state = ProjectLifecycleManager.get_state(phase2_project)
    state.current_stage = ProjectLifecycleStage.STAGE_3_BUILD
    ProjectLifecycleManager.save_state(phase2_project, state)

    allowed_build, _ = ProjectLifecycleManager.can_execute_command(
        phase2_project, "worker-spawn", task_type="build"
    )
    assert allowed_build is True

    allowed_none, _ = ProjectLifecycleManager.can_execute_command(
        phase2_project, "worker-spawn", task_type=None
    )
    assert allowed_none is True


def test_worker_status_and_harvest_allowed_in_phase2(phase2_project: Path) -> None:
    """Les commandes de cycle de vie worker (status, harvest, close) doivent être accessibles en Phase 2."""
    for cmd in ["worker-status", "worker-harvest", "worker-close"]:
        allowed, reason = ProjectLifecycleManager.can_execute_command(phase2_project, cmd)
        assert allowed is True, f"Commande {cmd} devrait être autorisée en Phase 2: {reason}"
