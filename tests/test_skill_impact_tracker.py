"""
Unit tests for SkillImpactTracker & WikiSkill memory integration.
"""
import json
import pytest
from pathlib import Path
from src.core.skill_impact_tracker import SkillImpactTracker, SkillImpactRecord


def test_record_attempt_accepted(tmp_path: Path):
    tracker = SkillImpactTracker(workspace_root=tmp_path)
    
    rec = tracker.record_attempt(
        target_skill="plan",
        proposed_diff="Ajout du verrou INVEST 4 Piliers",
        score_delta=0.18,
        verdict="ACCEPTED",
        reason="Amélioration significative de la complétude Gherkin.",
        metadata={"model": "claude-sonnet-5"}
    )
    
    assert rec.target_skill == "plan"
    assert rec.verdict == "ACCEPTED"
    assert rec.score_delta == 0.18
    
    # Vérifier l'écriture disque
    storage_path = tracker.get_storage_path()
    assert storage_path.exists()
    
    history = tracker.get_history(target_skill="plan")
    assert len(history) == 1
    assert history[0]["verdict"] == "ACCEPTED"
    assert history[0]["score_delta"] == 0.18


def test_negative_constraints_extraction(tmp_path: Path):
    tracker = SkillImpactTracker(workspace_root=tmp_path)
    
    # Enregistrer deux échecs et un succès
    tracker.record_attempt(
        target_skill="sentinel",
        proposed_diff="Injecter le code source Python brut",
        score_delta=-0.35,
        verdict="REJECTED",
        reason="Violation de la frontière No-Code et saturation de contexte."
    )
    tracker.record_attempt(
        target_skill="sentinel",
        proposed_diff="Supprimer la vérification du frontmatter",
        score_delta=-0.20,
        verdict="REJECTED",
        reason="Entraîne un échec immédiat au linter physique WikiFix."
    )
    tracker.record_attempt(
        target_skill="sentinel",
        proposed_diff="Clarifier les critères de résilience Gherkin",
        score_delta=0.12,
        verdict="ACCEPTED",
        reason="Conforme aux 4 Piliers."
    )
    
    # Extraire les contraintes négatives
    constraints = tracker.get_negative_constraints("sentinel")
    assert len(constraints) == 2
    assert "Violation de la frontière No-Code" in constraints[0] or "Violation de la frontière No-Code" in constraints[1]
    assert "linter physique WikiFix" in constraints[0] or "linter physique WikiFix" in constraints[1]
    
    # Vérifier le bloc prompt formaté
    block = tracker.format_negative_prompt_block("sentinel")
    assert "🚫 Contraintes Négatives" in block
    assert "WikiSkill Anti-Amnesia" in block
    assert "Violation de la frontière No-Code" in block


def test_project_scoped_isolation(tmp_path: Path):
    tracker = SkillImpactTracker(workspace_root=tmp_path)
    
    # Enregistrer dans un scope projet
    tracker.record_attempt(
        target_skill="triage",
        proposed_diff="Forcer le découpage en 10 mini-stories",
        score_delta=-0.5,
        verdict="REJECTED",
        reason="Sur-fragmentation du sprint backlog.",
        project_name="Metro_SANTE"
    )
    
    proj_path = tracker.get_storage_path(project_name="Metro_SANTE")
    assert proj_path.exists()
    assert "Projects" in str(proj_path)
    assert "Metro_SANTE" in str(proj_path)
    
    # L'historique global doit être vide pour triage
    global_hist = tracker.get_history(target_skill="triage")
    assert len(global_hist) == 0
    
    # L'historique projet doit contenir l'enregistrement
    proj_hist = tracker.get_history(target_skill="triage", project_name="Metro_SANTE")
    assert len(proj_hist) == 1
    assert proj_hist[0]["verdict"] == "REJECTED"
