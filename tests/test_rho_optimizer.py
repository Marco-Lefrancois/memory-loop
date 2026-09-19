"""
Unit tests for RHO Optimizer & Rejected Hypotheses Registry (WikiSkill).
"""
import pytest
import yaml
from pathlib import Path
from src.pipelines.rho_optimizer import (
    record_rejected_hypothesis,
    get_rejected_hypotheses,
    optimize_rho,
    get_rho_impact_file
)


def test_record_and_get_rejected_hypothesis(tmp_path: Path, monkeypatch):
    # Pointer la racine vers tmp_path
    monkeypatch.chdir(tmp_path)
    
    project_name = "TestProject"
    
    entry = record_rejected_hypothesis(
        project_name=project_name,
        keyword="fake_api_mock",
        reason="Interdiction formelle de générer des payloads synthétiques non documentés.",
        score_delta=-0.4,
        scope="project"
    )
    
    assert entry["keyword"] == "fake_api_mock"
    assert entry["verdict"] == "REJECTED"
    
    impact_file = get_rho_impact_file(project_name, scope="project")
    assert impact_file.exists()
    
    rejected_list = get_rejected_hypotheses(project_name, scope="project")
    assert len(rejected_list) == 1
    assert rejected_list[0]["keyword"] == "fake_api_mock"
    assert "Interdiction formelle" in rejected_list[0]["reason"]


def test_optimize_rho_creates_rule(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project_name = "TestProject"
    
    success = optimize_rho(
        project_name=project_name,
        keyword="onetrust",
        msg="Toujours vérifier le slug RFC 3986 de la politique de cookies.",
        scope="project"
    )
    
    assert success is True
    
    rho_file = tmp_path / "Projects" / project_name / "memory" / "rho_rules.yaml"
    assert rho_file.exists()
    
    with open(rho_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert len(data["rules"]) == 1
    assert data["rules"][0]["keyword"] == "onetrust"
    assert data["rules"][0]["status"] == "ACTIVE"


def test_optimize_rho_compact_strings_bifurcation(tmp_path: Path, monkeypatch):
    """Vérifie que les découvertes de compaction de commentaires bifurquent vers un linter déterministe."""
    monkeypatch.chdir(tmp_path)
    project_name = "TestProject"

    success = optimize_rho(
        project_name=project_name,
        keyword="commentaires verbeux",
        msg="Compacter les longues strings multi-lignes et commentaires verbeux",
        scope="global"
    )

    assert success is True
    det_file = tmp_path / "standards" / "linters" / "deterministic_rules.json"
    assert det_file.exists()

    import json
    data = json.loads(det_file.read_text(encoding="utf-8"))
    assert any(r["check_type"] == "compact_strings_and_comments" for r in data)

