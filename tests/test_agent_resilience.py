"""
Tests unitaires et d'intégration pour le moteur de résilience agentique (ADR-0371).
"""
import json
import pytest

from src.pipelines.agent_resilience import (
    AgentTopologyMapper,
    AgentStateRollbackEngine,
    ResilienceAudit,
    BlastRadiusLevel,
)
from src.state import LoopPhase, LoopState, SavepointManager


def test_topology_mapper_roles():
    """Vérifie que tous les rôles d'agents standards sont mappés avec leurs permissions."""
    topologies = AgentTopologyMapper.list_all_topologies()
    assert len(topologies) >= 6
    roles = [t.role for t in topologies]
    assert "orchestrator" in roles
    assert "worker" in roles
    assert "research" in roles
    assert "qa" in roles
    assert "crawler" in roles
    assert "sentinel" in roles


def test_topology_blast_radius_safe():
    """Vérifie le calcul de blast radius pour un worker sans violation."""
    calc = AgentTopologyMapper.compute_blast_radius(
        role="worker",
        proposed_writes=["docs/architecture/spec.md", "backlog/stories/STORY-001.md"]
    )
    assert calc["role"] == "worker"
    assert calc["level"] == BlastRadiusLevel.CONTROLLED.value
    assert calc["unattended_authorized"] is True
    assert len(calc["violations"]) == 0
    assert len(calc["in_scope_writes"]) == 2


def test_topology_blast_radius_violation():
    """Vérifie la détection de violation si un agent tente d'écrire hors périmètre."""
    calc = AgentTopologyMapper.compute_blast_radius(
        role="worker",
        proposed_writes=[".env", "standards/adr-system/secret.txt"]
    )
    assert len(calc["violations"]) == 2
    assert calc["unattended_authorized"] is False
    assert calc["blast_score"] > 35  # Pénalité de score appliquée


def test_unknown_role_confinement():
    """Vérifie qu'un rôle non répertorié est confiné par défaut."""
    top = AgentTopologyMapper.get_topology("untrusted_custom_agent")
    assert top.role == "untrusted_custom_agent"
    assert top.unattended_safe is False
    assert ".env" in top.forbidden_paths


def test_evidence_integrity_check(tmp_path):
    """Vérifie la validation des signatures d'EvidencePacks."""
    ev_dir = tmp_path / "memory" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)

    # Valid evidence file
    valid_file = ev_dir / "TEST-001_evidence.json"
    valid_file.write_text(json.dumps({
        "gate_execution_ledger": {
            "status": "ALL_MET",
            "gates": [{"id": "G1", "passed": True}]
        }
    }), encoding="utf-8")

    audit = AgentStateRollbackEngine.verify_evidence_integrity(tmp_path)
    assert audit["total"] == 1
    assert audit["valid"] == 1
    assert audit["corrupted"] == 0
    assert audit["details"][0]["has_ledger"] is True


def test_resilience_audit_scoring(tmp_path):
    """Vérifie le calcul global du Resilience Index."""
    # Créer arborescence minimale
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    health_file = mem_dir / "SESSION_MEMORY_HEALTH.md"
    health_file.write_text("# Session Health\nOK\n", encoding="utf-8")

    audit = ResilienceAudit.audit("TestProject", project_path=tmp_path)
    assert "resilience_index" in audit
    assert "status" in audit
    assert audit["memory_hygiene"]["ok"] is True
    assert audit["memory_hygiene"]["lines"] == 2


def test_rollback_engine_roundtrip(tmp_path):
    """Vérifie la sauvegarde et le rollback d'un checkpoint LoopState."""
    checkpoints_dir = tmp_path / "memory" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    state = LoopState(project_name="TestProject")
    state.current_phase = LoopPhase.SPEC

    # Sauvegarder checkpoint
    cp_file = SavepointManager.save_checkpoint(
        state.model_dump(exclude={"sprint_backlog", "knowledge_graph"}),
        project_path=tmp_path,
        reason="test_savepoint",
    )
    assert cp_file.exists()

    # Lister les points de restauration
    points = AgentStateRollbackEngine.list_restore_points(tmp_path)
    assert len(points) == 1
    assert points[0]["step"] == 1
    assert points[0]["phase"] == "spec"
    assert len(points[0]["sha256"]) == 64


@pytest.mark.parametrize(
    "role,expected_level,expected_unattended",
    [
        ("orchestrator", BlastRadiusLevel.ELEVATED, False),
        ("worker", BlastRadiusLevel.CONTROLLED, True),
        ("research", BlastRadiusLevel.MINIMAL, True),
        ("qa", BlastRadiusLevel.MINIMAL, True),
        ("crawler", BlastRadiusLevel.MINIMAL, True),
        ("sentinel", BlastRadiusLevel.MINIMAL, True),
    ],
)
def test_topology_roles_parametrized(role, expected_level, expected_unattended):
    """Standard 5 : Test paramétré de la matrice de conformité des rôles."""
    calc = AgentTopologyMapper.compute_blast_radius(role)
    assert calc["level"] == expected_level.value
    assert calc["unattended_authorized"] == expected_unattended


def test_rollback_failure_contracts(tmp_path):
    """Standard 5 : Test du contrat de rupture (Failure Contract) lors du rollback."""
    # Cas 1 : Aucun checkpoint existant
    res_empty = AgentStateRollbackEngine.rollback_to_step("TestProject", step=1, project_path=tmp_path)
    assert res_empty["success"] is False
    assert "Aucun point de restauration" in res_empty["error"]

    # Cas 2 : Checkpoint step hors bornes
    checkpoints_dir = tmp_path / "memory" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    state = LoopState(project_name="TestProject")
    SavepointManager.save_checkpoint(
        state.model_dump(exclude={"sprint_backlog", "knowledge_graph"}),
        project_path=tmp_path,
        reason="test_cp",
    )

    res_out_of_bounds = AgentStateRollbackEngine.rollback_to_step("TestProject", step=99, project_path=tmp_path)
    assert res_out_of_bounds["success"] is False
    assert "introuvable" in res_out_of_bounds["error"]


def test_corrupted_evidence_detected(tmp_path):
    """Standard 5 : Vérifie la détection d'EvidencePack corrompu (JSON invalide)."""
    ev_dir = tmp_path / "memory" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    bad_file = ev_dir / "CORRUPT-001_evidence.json"
    bad_file.write_text("{invalid_json_format: true", encoding="utf-8")

    audit = AgentStateRollbackEngine.verify_evidence_integrity(tmp_path)
    assert audit["total"] == 1
    assert audit["valid"] == 0
    assert audit["corrupted"] == 1
    assert audit["details"][0]["status"] == "CORRUPTED"

