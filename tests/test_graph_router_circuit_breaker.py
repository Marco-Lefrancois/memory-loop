import pytest
import os
import json
from pathlib import Path

from src.pipelines.graph_router import GraphRouter, TaskNode, CircuitBreakerGovernor, NodeCategory, RiskLevel
from src.pipelines.evidence import EvidencePack, EvidenceItem, EvidenceReducer, DeterministicContractMirror
from src.pipelines.rho_optimizer import dream_collector

def test_circuit_breaker_cutoff(tmp_path):
    router = GraphRouter(initiative_name="test_cb", project_dir=str(tmp_path), max_attempts=2)
    node = TaskNode(id="node_a", role="build", description="Build component")
    router.add_node(node)

    # Attempt 1 -> OK
    assert router.mark_running("node_a") is True
    router.mark_failed("node_a", "Temporary failure")

    # Attempt 2 -> OK
    assert router.mark_running("node_a") is True
    router.mark_failed("node_a", "Temporary failure 2")

    # Attempt 3 -> Circuit Breaker trips
    assert router.mark_running("node_a") is False
    assert router.nodes["node_a"].status == "blocked_asymmetry"
    assert "exceeded 2 attempts" in router.nodes["node_a"].error

def test_deadlock_detection(tmp_path):
    router = GraphRouter(initiative_name="test_deadlock", project_dir=str(tmp_path))
    node_a = TaskNode(id="A", role="plan", description="Node A", blocked_by=["B"])
    node_b = TaskNode(id="B", role="build", description="Node B", blocked_by=["A"])
    router.add_node(node_a)
    router.add_node(node_b)

    deadlocks = router.check_deadlocks()
    assert len(deadlocks) > 0
    assert "A" in deadlocks and "B" in deadlocks
    assert router.nodes["A"].status == "blocked_deadlock"

def test_jit_ephemeral_subagent_creation(tmp_path):
    router = GraphRouter(initiative_name="test_jit", project_dir=str(tmp_path))
    subagent = router.create_ephemeral_subagent(
        node_id="jit_sentinel",
        role="sentinel",
        description="Audit contradictoire JIT",
        tools=["Read", "Grep"],
        permissions={"edit": "deny"}
    )
    assert subagent.id == "jit_sentinel"
    assert subagent.inputs["tools"] == ["Read", "Grep"]
    assert subagent.inputs["permissions"]["edit"] == "deny"
    assert subagent.inputs["model"] == "opencode/nemotron-3-ultra-free"

def test_deterministic_contract_mirror():
    pack_fe = EvidencePack(source_node="fe_worker", initiative_name="auth_feature")
    pack_fe.add_item(EvidenceItem(
        evidence_id="FE-01",
        target_file="src/ui/login.tsx",
        line_range=(1, 10),
        rule_ref="API_ROUTE",
        confidence=1.0,
        risk_level="LOW",
        description="Calls login route",
        evidence_payload={"route": "/api/v1/auth/login", "method": "POST", "fields": ["email", "password"]}
    ))

    # Identical contract from BE
    pack_be_ok = EvidencePack(source_node="be_worker", initiative_name="auth_feature")
    pack_be_ok.add_item(EvidenceItem(
        evidence_id="BE-01",
        target_file="src/api/auth.py",
        line_range=(1, 20),
        rule_ref="API_ROUTE",
        confidence=1.0,
        risk_level="LOW",
        description="Defines login endpoint",
        evidence_payload={"route": "/api/v1/auth/login", "method": "POST", "fields": ["email", "password"]}
    ))

    is_sym, violations = DeterministicContractMirror.verify_contract_symmetry([pack_fe, pack_be_ok])
    assert is_sym is True
    assert len(violations) == 0

    # Divergent contract (Drift)
    pack_be_drift = EvidencePack(source_node="be_worker", initiative_name="auth_feature")
    pack_be_drift.add_item(EvidenceItem(
        evidence_id="BE-02",
        target_file="src/api/auth.py",
        line_range=(1, 20),
        rule_ref="API_ROUTE",
        confidence=1.0,
        risk_level="LOW",
        description="Defines login endpoint with extra field",
        evidence_payload={"route": "/api/v1/auth/login", "method": "POST", "fields": ["email", "password", "captcha_token"]}
    ))

    is_sym2, violations2 = DeterministicContractMirror.verify_contract_symmetry([pack_fe, pack_be_drift])
    assert is_sym2 is False
    assert len(violations2) > 0
    assert "Contract Drift" in violations2[0]

def test_rho_dream_collector_tombstone(tmp_path):
    project_dir = tmp_path / "Projects" / "TestProject"
    project_dir.mkdir(parents=True)
    memory_dir = project_dir / "memory"
    memory_dir.mkdir(parents=True)
    arch_dir = project_dir / "docs" / "01-architecture"
    arch_dir.mkdir(parents=True)

    # Créer rho_rules.yaml
    rho_file = memory_dir / "rho_rules.yaml"
    rho_file.write_text("""
rules:
  - keyword: legacy_xml_parser
    msg: Toujours parser en XML
    status: ACTIVE
""", encoding="utf-8")

    # Créer un ADR qui rend legacy_xml_parser obsolète
    adr_file = arch_dir / "ADR-0099-json-migration.md"
    adr_file.write_text("""
# ADR-0099 : Migration JSON
Le module legacy_xml_parser est obsolète et déprécié au profit du JSON natif.
""", encoding="utf-8")

    # Exécuter dream_collector en ciblant le projet temporaire
    cwd_backup = os.getcwd()
    try:
        os.chdir(tmp_path)
        summary = dream_collector("TestProject")
        assert summary["tombstones_applied"] == 1
        
        # Vérifier que le statut est devenu TOMBSTONE
        with open(rho_file, "r", encoding="utf-8") as f:
            import yaml
            data = yaml.safe_load(f)
            assert data["rules"][0]["status"] == "TOMBSTONE"
            assert "Contradicted or superseded" in data["rules"][0]["tombstone_reason"]
    finally:
        os.chdir(cwd_backup)
