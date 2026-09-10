"""
Unit tests for SkillAutoTuner with WikiSkill Validation Gating & Rollback.
"""
import pytest
from pathlib import Path
from src.pipelines.skill_auto_tuner import SkillAutoTuner, tune_skill


@pytest.fixture
def mock_skill_workspace(tmp_path: Path):
    skills_dir = tmp_path / ".agents" / "skills" / "sentinel"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    skill_content = """---
name: sentinel
description: Quality assurance sentinel
---
# Sentinel Skill

## Instructions
1. Vérifier les 4 piliers Gherkin.



2. Assurer la traçabilité INVEST.
"""
    (skills_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
    return tmp_path


def test_auto_tuner_acceptance_on_positive_score(mock_skill_workspace: Path):
    tuner = SkillAutoTuner(workspace_root=mock_skill_workspace)
    
    result = tuner.run_tuning_cycle(
        target_skill="sentinel",
        evaluation_feedback="Amélioration de clarté textuelle",
        simulated_score_delta=0.15
    )
    
    assert result["success"] is True
    assert result["status"] == "ACCEPTED_OPTIMIZED"
    assert result["score_delta"] == 0.15
    
    # Vérifier l'enregistrement dans le tracker
    history = tuner.tracker.get_history(target_skill="sentinel")
    assert len(history) == 1
    assert history[0]["verdict"] == "ACCEPTED"


def test_auto_tuner_rollback_on_negative_score(mock_skill_workspace: Path):
    skill_file = mock_skill_workspace / ".agents" / "skills" / "sentinel" / "SKILL.md"
    original_content = skill_file.read_text(encoding="utf-8")
    
    tuner = SkillAutoTuner(workspace_root=mock_skill_workspace)
    
    result = tuner.run_tuning_cycle(
        target_skill="sentinel",
        evaluation_feedback="Régression des critères Gherkin",
        simulated_score_delta=-0.25
    )
    
    assert result["success"] is False
    assert result["status"] == "REJECTED_ROLLED_BACK"
    assert result["score_delta"] == -0.25
    
    # Le fichier doit avoir été restauré à l'identique (ROLLBACK)
    assert skill_file.read_text(encoding="utf-8") == original_content
    
    # L'échec doit être consigné dans le tracker (Anti-Amnesia)
    history = tuner.tracker.get_history(target_skill="sentinel", verdict_filter="REJECTED")
    assert len(history) == 1
    assert history[0]["verdict"] == "REJECTED"
    assert "Régression" in history[0]["reason"]
    
    # Vérifier que la contrainte négative est désormais consultable
    constraints = tuner.tracker.get_negative_constraints("sentinel")
    assert len(constraints) == 1
    assert "Régression des critères Gherkin" in constraints[0]


def test_auto_tuner_missing_skill(mock_skill_workspace: Path):
    tuner = SkillAutoTuner(workspace_root=mock_skill_workspace)
    result = tuner.run_tuning_cycle(target_skill="nonexistent_skill")
    assert result["success"] is False
    assert "introuvable" in result["error"]
