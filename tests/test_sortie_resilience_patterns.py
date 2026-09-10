"""
test_sortie_resilience_patterns.py - Tests unitaires pour les patterns de résilience inspirés de Sortie (ADR-0355).

Couvre :
1. Protocole de signalisation sidecar (WorkerSignal, JSON & Key-Value parsing, lecture/écriture).
2. Stall detection et watchdog de purge zombie dans HerdrAdapter.
3. Handoff Evidence Policy et détection de non-dégénérescence dans CompletionGate.
4. Intégration dans le pipeline worker (run_worker_reap et run_worker_harvest).
"""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.core.worker_signal import (
    WorkerSignal,
    WorkerSignalType,
    parse_worker_signal,
    read_worker_signal,
    write_worker_signal,
    resolve_signal_path,
)
from src.core.herdr_adapter import HerdrAdapter
from src.pipelines.completion_gate import (
    CompletionGate,
    GateStatus,
    HandoffEvidencePolicy,
)
from src.pipelines.worker_pipeline import (
    run_worker_reap,
    run_worker_reap_zombies,
    run_worker_harvest,
)


# ==============================================================================
# 1. Tests WorkerSignal & Sidecar Protocol
# ==============================================================================

def test_worker_signal_json_parsing():
    json_data = json.dumps({
        "status": "COMPLETED",
        "reason": "Tous les tests sont passés et le code est commité",
        "story_id": "US-TEST-01",
        "details": {"files_modified": 3}
    })
    sig = parse_worker_signal(json_data)
    assert sig is not None
    assert sig.signal_type == WorkerSignalType.COMPLETED
    assert sig.reason == "Tous les tests sont passés et le code est commité"
    assert sig.details.get("files_modified") == 3


def test_worker_signal_key_value_parsing():
    raw_kv = """
    # Rapport d'état du worker
    STATUS = NO_CHANGE_NEEDED
    REASON = Le bug était déjà corrigé dans la version amont
    STORY_ID = MMA-4651
    """
    sig = parse_worker_signal(raw_kv)
    assert sig is not None
    assert sig.signal_type == WorkerSignalType.NO_CHANGE_NEEDED
    assert "déjà corrigé" in sig.reason


def test_worker_signal_blocked_and_case_insensitive():
    raw_kv = "status=blocked\nreason=Manque de credentials pour la base"
    sig = parse_worker_signal(raw_kv)
    assert sig is not None
    assert sig.signal_type == WorkerSignalType.BLOCKED
    assert sig.reason == "Manque de credentials pour la base"


def test_worker_signal_write_and_read(tmp_path):
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()

    # Écriture dans .mloop/status
    sig_out = WorkerSignal(
        signal_type=WorkerSignalType.NEEDS_REVIEW,
        reason="Refactoring terminé mais nécessite confirmation d'API",
        story_id="US-API-09"
    )
    written_path = write_worker_signal(project_dir, sig_out)
    assert written_path.exists()

    # Lecture via read_worker_signal
    sig_in = read_worker_signal(project_dir, story_id="US-API-09")
    assert sig_in is not None
    assert sig_in.signal_type == WorkerSignalType.NEEDS_REVIEW
    assert "confirmation d'API" in sig_in.reason


def test_worker_signal_fallback_worker_specific(tmp_path):
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()
    memory_dir = project_dir / "memory"
    memory_dir.mkdir()

    # Écriture spécifique worker_<story_id>.status
    target_file = memory_dir / "worker_US_99.status"
    target_file.write_text("STATUS=COMPLETED\nREASON=Done in worker file\n", encoding="utf-8")

    sig = read_worker_signal(project_dir, story_id="US-99")
    assert sig is not None
    assert sig.signal_type == WorkerSignalType.COMPLETED
    assert sig.reason == "Done in worker file"


# ==============================================================================
# 2. Tests Stall Detection & Zombie Reaping (HerdrAdapter)
# ==============================================================================

def test_detect_stalled_agents():
    adapter = HerdrAdapter()
    mock_agents = [
        {"name": "worker_active", "agent_status": "running", "pane_id": "pane_1"},
        {"name": "worker_idle", "agent_status": "idle", "pane_id": "pane_2"},
        {"name": "worker_stopped", "agent_status": "stopped", "pane_id": "pane_3"},
        {"name": "worker_untracked", "agent_status": "", "pane_id": "pane_4"},
    ]

    with patch.object(adapter, "list_agents", return_value={"success": True, "result": {"agents": mock_agents}}):
        stalled = adapter.detect_stalled_agents(timeout_sec=300)
        assert len(stalled) == 3
        stalled_panes = [s["pane_id"] for s in stalled]
        assert "pane_2" in stalled_panes
        assert "pane_3" in stalled_panes
        assert "pane_4" in stalled_panes
        assert "pane_1" not in stalled_panes


def test_reap_zombie_workers():
    adapter = HerdrAdapter()
    mock_agents = [
        {"name": "worker_done", "agent_status": "done", "pane_id": "pane_10"},
        {"name": "worker_running", "agent_status": "busy", "pane_id": "pane_11"},
    ]

    with patch.object(adapter, "list_agents", return_value={"success": True, "result": {"agents": mock_agents}}):
        with patch.object(adapter, "close_pane", return_value={"success": True, "closed_pane": "pane_10"}) as mock_close:
            res = adapter.reap_zombie_workers(timeout_sec=300)
            assert res["success"] is True
            assert res["total_detected"] == 1
            assert res["reaped_count"] == 1
            mock_close.assert_called_once_with("pane_10")


# ==============================================================================
# 3. Tests Handoff Evidence Policy (CompletionGate)
# ==============================================================================

def test_handoff_evidence_policy_off(tmp_path):
    res = CompletionGate.validate_workspace_evidence(
        project_path=tmp_path,
        story_id="US-DUMMY",
        policy=HandoffEvidencePolicy.OFF
    )
    assert res.status == GateStatus.PASS
    assert res.requires_hitl is False


def test_handoff_evidence_no_change_needed_signal(tmp_path):
    sig = WorkerSignal(
        signal_type=WorkerSignalType.NO_CHANGE_NEEDED,
        reason="Analyse concluante : aucun changement requis"
    )
    res = CompletionGate.validate_workspace_evidence(
        project_path=tmp_path,
        story_id="US-NOOP",
        signal=sig,
        policy=HandoffEvidencePolicy.OBSERVED
    )
    assert res.status == GateStatus.PASS
    assert res.requires_hitl is False
    assert any("NO_CHANGE_NEEDED" in w for w in res.warnings)


def test_handoff_evidence_blocked_signal(tmp_path):
    sig = WorkerSignal(
        signal_type=WorkerSignalType.BLOCKED,
        reason="Dépendance externe indisponible"
    )
    res = CompletionGate.validate_workspace_evidence(
        project_path=tmp_path,
        story_id="US-BLOCKED",
        signal=sig,
        policy=HandoffEvidencePolicy.OBSERVED
    )
    assert res.status == GateStatus.FAIL
    assert res.requires_hitl is True
    assert any("Worker bloqué" in r for r in res.reasons)


def test_handoff_evidence_observed_with_modified_file(tmp_path):
    # Création de l'arborescence
    stories_dir = tmp_path / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    story_file = stories_dir / "US-01.md"
    story_file.write_text("# US-01 Updated Content\n", encoding="utf-8")

    spawn_time = time.time() - 10.0

    res = CompletionGate.validate_workspace_evidence(
        project_path=tmp_path,
        story_id="US-01",
        spawn_timestamp=spawn_time,
        policy=HandoffEvidencePolicy.OBSERVED
    )
    assert res.status == GateStatus.PASS
    assert res.requires_hitl is False
    assert res.patch_stats.get("modified_candidates_count") == 1


def test_handoff_evidence_observed_no_file_triggers_hitl(tmp_path):
    # Aucun fichier créé
    res = CompletionGate.validate_workspace_evidence(
        project_path=tmp_path,
        story_id="US-GHOST",
        policy=HandoffEvidencePolicy.OBSERVED
    )
    assert res.status == GateStatus.DEGENERATE_CANDIDATE
    assert res.is_degenerate is True
    assert res.requires_hitl is True
    assert any("Aucune preuve d'effort physique" in r for r in res.reasons)


# ==============================================================================
# 4. Tests Worker Pipeline (run_worker_reap & run_worker_harvest integration)
# ==============================================================================

@patch("src.core.herdr_adapter.herdr.reap_zombie_workers")
def test_pipeline_run_worker_reap(mock_reap):
    mock_reap.return_value = {
        "success": True,
        "total_detected": 2,
        "reaped_count": 2,
        "reaped": [{"name": "worker_1", "pane_id": "p1", "reason": "idle"}],
        "errors": []
    }

    res = run_worker_reap(timeout_sec=120, force=True)
    assert res["success"] is True
    assert res["reaped_count"] == 2
    mock_reap.assert_called_once_with(timeout_sec=120, force=True)

    # Vérification alias rétrocompatible
    mock_reap.reset_mock()
    res_alias = run_worker_reap_zombies()
    assert res_alias["success"] is True
    mock_reap.assert_called_once_with(timeout_sec=300, force=False)


@patch("src.core.herdr_adapter.herdr.harvest_story_evidence")
def test_pipeline_run_worker_harvest_with_sidecar_signal(mock_harvest, tmp_path):
    # Setup projet et sidecar .mloop/status
    proj_dir = tmp_path / "DemoProject"
    proj_dir.mkdir()
    dot_mloop = proj_dir / ".mloop"
    dot_mloop.mkdir()
    (dot_mloop / "status").write_text(json.dumps({
        "status": "NO_CHANGE_NEEDED",
        "reason": "Inspection terminée sans code à modifier",
        "story_id": "US-HARVEST-01"
    }), encoding="utf-8")

    mock_harvest.return_value = {
        "success": True,
        "cleaned_lines": 50,
        "evidence_file": str(proj_dir / "evidence.json"),
        "summary_preview": "Execution summary...",
    }

    with patch("src.pipelines.worker_pipeline.resolve_project_path", return_value=proj_dir):
        res = run_worker_harvest(
            project_name="DemoProject",
            story_id="US-HARVEST-01",
            lines=50
        )

    assert res["success"] is True
    assert "evidence_gate" in res
    assert res["evidence_gate"]["status"] == "PASS"
    assert res["evidence_gate"]["requires_hitl"] is False
