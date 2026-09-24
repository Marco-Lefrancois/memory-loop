"""
Tests unitaires & d'intégration — StandardsGraph & Bouclier de Confinement Runtime (ADR-0379).
Conforme aux 7 standards de robustesse Python Senior (ADR-0369).
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from src.core.standards_graph import StandardsGraphStore, ADRContract, SkillManifest, AgentManifest
from src.core.confinement_shield import (
    AgentContext,
    ConfinementShield,
    PermissionDeniedError,
    SandboxViolationError,
)
from src.core.skill_registry import get_skill_catalog, resolve_skill, InvalidSkillURIError, SkillNotFoundError


def test_standards_graph_initialization_and_sync():
    """Test 1 : Initialisation de la base SQLite et synchronisation incrémentale SSOT."""
    store = StandardsGraphStore.get_instance()
    assert store.db_path.exists()

    stats = store.sync_all()
    assert stats["adrs"] >= 87
    assert stats["skills"] >= 38
    assert stats["agents"] == 5
    assert stats["rules"] >= 3


def test_standards_graph_skills_discovery():
    """Test 2 : Découverte dynamique des compétences (au moins 38)."""
    store = StandardsGraphStore.get_instance()
    skills = store.get_skills()
    assert len(skills) >= 38

    # Vérifier des compétences clés
    assert "markitdown" in skills
    assert "graph-engineering" in skills
    assert "plan" in skills
    assert "sentinel" in skills

    markitdown = store.get_skill("markitdown")
    assert markitdown is not None
    assert "MarkItDown" in markitdown.description or "ingestion" in markitdown.description.lower()


def test_standards_graph_agents_unification():
    """Test 3 : Profils d'agents unifiés (.agents/agents/*.md) sans aucun fichier .toml."""
    store = StandardsGraphStore.get_instance()
    agents = store.get_agents()
    assert len(agents) == 5
    assert set(agents.keys()) == {"explorer", "orchestrator", "plan", "sentinel", "worker"}

    # Vérifier l'agent Explorer (Phase 1)
    explorer = agents["explorer"]
    assert explorer.model == "gemini-3.8-flash"
    assert explorer.sandbox_mode == "read-only"
    assert "markitdown" in explorer.skills
    assert "graphify" in explorer.skills
    assert "backlog/stories/**" in explorer.forbidden_write_paths


def test_standards_graph_adrs_scoping_by_stage():
    """Test 4 : Scoping JIT des ADRs par phase de cycle de vie."""
    store = StandardsGraphStore.get_instance()

    # Récupérer les ADRs de la phase 1
    phase_1_adrs = store.get_adrs_by_stage("STAGE_1_INGEST")
    assert len(phase_1_adrs) >= 1

    adr_0378 = store.get_adr("0378")
    assert adr_0378 is not None
    assert "Phase 1" in adr_0378.title
    assert len(adr_0378.validation_rules) >= 1


def test_confinement_shield_skill_whitelisting():
    """Test 5 : Le bouclier de confinement runtime bloque tout outil non autorisé."""
    # En contexte explorer :
    with AgentContext("explorer"):
        # Outils autorisés
        assert ConfinementShield.verify_skill_access("markitdown") is True
        assert ConfinementShield.verify_skill_access("graphify") is True

        # Outil interdit : tentative d'outrepassage
        with pytest.raises(PermissionDeniedError, match="STRICTEMENT INTERDITE"):
            ConfinementShield.verify_skill_access("deploy-to-prod")

        # Résolution via skill_registry
        with pytest.raises(PermissionDeniedError):
            resolve_skill("skill://deploy-to-prod")


def test_confinement_shield_filesystem_write_jail(tmp_path: Path):
    """Test 6 : Le bouclier de confinement runtime bloque les écritures hors sandbox (Check 13)."""
    project_dir = tmp_path / "Projects" / "TestProject"
    project_dir.mkdir(parents=True)

    with AgentContext("explorer", project_path=project_dir):
        # Écriture autorisée
        allowed_file = project_dir / "docs" / "00-ingested" / "fact.md"
        assert ConfinementShield.verify_write_path(allowed_file) is True

        # Écriture interdite : récits sous backlog/stories/ en Phase 1
        forbidden_story = project_dir / "backlog" / "stories" / "US001.md"
        with pytest.raises(SandboxViolationError, match="Écriture STRICTEMENT INTERDITE"):
            ConfinementShield.verify_write_path(forbidden_story)

        # Écriture interdite : code source sous src/
        forbidden_src = project_dir / "src" / "app.py"
        with pytest.raises(SandboxViolationError):
            ConfinementShield.verify_write_path(forbidden_src)


def test_confinement_shield_proof_of_work_validation(tmp_path: Path):
    """Test 7 : Validation déterministe de la preuve de travail Phase 1 (source_manifest.json)."""
    project_dir = tmp_path / "Projects" / "MockProj"
    ref_dir = project_dir / "reference"
    docs_ingested = project_dir / "docs" / "00-ingested"
    ref_dir.mkdir(parents=True)
    docs_ingested.mkdir(parents=True)

    # 1. Si reference/ est vide, la validation passe (rien à ingérer)
    valid, violations = ConfinementShield.verify_phase_1_proof_of_work(project_dir)
    assert valid is True
    assert len(violations) == 0

    # 2. Si un fichier existe dans reference/ mais pas de manifeste : échec
    sample_file = ref_dir / "spec.pdf"
    sample_file.write_bytes(b"sample pdf binary content")
    valid, violations = ConfinementShield.verify_phase_1_proof_of_work(project_dir)
    assert valid is False
    assert any("source_manifest.json manquant" in v for v in violations)

    # 3. Créer un manifeste valide
    import hashlib
    sha = hashlib.sha256(sample_file.read_bytes()).hexdigest()
    manifest = {
        "sources": [
            {
                "source_path": "reference/spec.pdf",
                "sha256": sha,
                "what_it_actually_proves": "Spécification formelle du besoin client.",
                "what_it_does_not_prove": "Ne garantit pas la faisabilité technique."
            }
        ]
    }
    (docs_ingested / "source_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    valid, violations = ConfinementShield.verify_phase_1_proof_of_work(project_dir)
    assert valid is True
    assert len(violations) == 0


def test_daemon_roles_list_json_rpc():
    """Test 8 : Parité JSON-RPC roles/list dans le serveur daemon avec StandardsGraph."""
    from src.daemon.app_server import AppServerProtocol
    server = AppServerProtocol()
    response_str = server.handle_request(json.dumps({
        "jsonrpc": "2.0",
        "method": "roles/list",
        "params": {},
        "id": 1
    }))
    response = json.loads(response_str)
    assert "result" in response
    roles = response["result"]["roles"]
    assert len(roles) == 5
    role_names = {r["name"] for r in roles}
    assert role_names == {"explorer", "orchestrator", "plan", "sentinel", "worker"}
