# -*- coding: utf-8 -*-
"""
Tests unitaires pour MLOOP-252-BE : Session Forking OpenCode pour Grill-Me & Doubt-Driven.
Conforme ADR-0202 (<=300L) et 4 Piliers Gherkin.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from src.bridges.opencode.session_forker import (
    OpenCodeSessionForker,
    SessionForkError,
    SessionNotFoundError,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Espace temporaire pour tester le gestionnaire de forks."""
    (tmp_path / "memory" / "sessions").mkdir(parents=True)
    return tmp_path


def test_fork_session_nominal(temp_workspace: Path):
    """Pilier 1 - Nominal : bifurcation d'une session avec inscription au registre."""
    forker = OpenCodeSessionForker(workspace_root=temp_workspace)

    # Mock runner retournant un code 0 et le nouvel ID
    def mock_runner(cmd, **kwargs):
        return {"returncode": 0, "child_id": "sess-child-101", "stdout": "Forked successfully"}

    res = forker.fork_session(
        parent_session_id="sess-parent-001",
        reason="GRILL_EXPLORATION",
        story_id="MLOOP-252-BE",
        runner=mock_runner,
    )

    assert res["child_session_id"] == "sess-child-101"
    assert res["parent_session_id"] == "sess-parent-001"
    assert res["status"] == "ACTIVE"

    forks = forker.list_forks(story_id="MLOOP-252-BE")
    assert len(forks) == 1
    assert forks[0]["child_session_id"] == "sess-child-101"
    assert forks[0]["reason"] == "GRILL_EXPLORATION"


def test_fork_session_runner_failure(temp_workspace: Path):
    """Pilier 2 - Exception : échec du runner CLI OpenCode."""
    forker = OpenCodeSessionForker(workspace_root=temp_workspace)

    def failing_runner(cmd, **kwargs):
        return {"returncode": 1, "stderr": "Session not found in store"}

    with pytest.raises(SessionNotFoundError):
        forker.fork_session(
            parent_session_id="sess-invalide",
            reason="GRILL_EXPLORATION",
            runner=failing_runner,
        )


def test_reconcile_fork(temp_workspace: Path):
    """Pilier 1 - Nominal : réconciliation d'une session forked."""
    forker = OpenCodeSessionForker(workspace_root=temp_workspace)
    forker.fork_session(
        parent_session_id="sess-p1",
        reason="DOUBT_REVIEW",
        story_id="MLOOP-252-BE",
        runner=lambda cmd, **kw: {"returncode": 0, "child_id": "sess-c1"},
    )

    rec = forker.reconcile_fork("sess-c1", summary="Arbitrage validé en faveur de l'option B")
    assert rec["reconciled"] is True
    assert rec["summary"] == "Arbitrage validé en faveur de l'option B"

    # Vérification dans la liste
    forks = forker.list_forks()
    assert forks[0]["reconciled"] is True


def test_purge_expired_forks(temp_workspace: Path):
    """Pilier 3 - Résilience & Rétention : purge des sessions > 7 jours."""
    forker = OpenCodeSessionForker(workspace_root=temp_workspace)

    # Création d'une session récente
    forker.fork_session(
        parent_session_id="sess-recent",
        reason="GRILL",
        runner=lambda cmd, **kw: {"returncode": 0, "child_id": "child-recent"},
    )

    # Injection directe d'une session ancienne (> 8 jours)
    registry_file = temp_workspace / "memory" / "sessions" / "forks_registry.json"
    data = forker._read_registry()
    old_time = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat()
    data.append({
        "child_session_id": "child-old",
        "parent_session_id": "sess-old",
        "story_id": "ANCIENNE-001",
        "reason": "EXPIRED",
        "created_at": old_time,
        "ttl_days": 7,
        "reconciled": False,
        "summary": None,
    })
    forker._write_registry(data)

    assert len(forker.list_forks()) == 2
    purged_count = forker.purge_expired_forks(max_age_days=7)
    assert purged_count == 1

    remaining = forker.list_forks()
    assert len(remaining) == 1
    assert remaining[0]["child_session_id"] == "child-recent"


def test_get_session_tree(temp_workspace: Path):
    """Pilier 4 - UX : représentation arborescente des sessions."""
    forker = OpenCodeSessionForker(workspace_root=temp_workspace)
    forker.fork_session(
        parent_session_id="root-sess",
        reason="BRANCH_1",
        story_id="S1",
        runner=lambda cmd, **kw: {"returncode": 0, "child_id": "branch-1"},
    )
    forker.fork_session(
        parent_session_id="root-sess",
        reason="BRANCH_2",
        story_id="S1",
        runner=lambda cmd, **kw: {"returncode": 0, "child_id": "branch-2"},
    )

    tree = forker.get_session_tree(story_id="S1")
    assert "root-sess" in tree
    assert len(tree["root-sess"]) == 2
    assert "branch-1" in tree["root-sess"]
    assert "branch-2" in tree["root-sess"]
