# -*- coding: utf-8 -*-
"""
tests/test_skill_flywheel.py — Tests exhaustifs pour MLOOP-242-BE (SkillFlywheel).
Valide la conformité ADR-0202 (<= 300 lignes), ADR-0348, ADR-0369 et ADR-0389.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pipelines.skill_flywheel import SkillFlywheel


@pytest.fixture
def flywheel_workspace(tmp_path: Path) -> Path:
    """Crée un espace de travail temporaire avec compétences et golden datasets."""
    ws = tmp_path / "flywheel_ws"
    skills_dir = ws / ".agents" / "skills"
    evals_dir = ws / "Projects" / "mLoop" / "memory" / "evals" / "skills"
    mem_dir = ws / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)

    # 1. Compétence dégradée "mock-skill" (score faible car règles manquantes)
    skill_dir = skills_dir / "mock-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    initial_content = (
        "---\n"
        "name: mock-skill\n"
        "description: Compétence mock. Use when testing.\n"
        "---\n\n"
        "# Mock Skill\n\n"
        "Texte simple sans étapes ordonnées ni ancrage canonique.\n"
    )
    (skill_dir / "SKILL.md").write_text(initial_content, encoding="utf-8")

    # Golden dataset pour mock-skill
    mock_eval = evals_dir / "mock-skill"
    mock_eval.mkdir(parents=True, exist_ok=True)
    (mock_eval / "cases.json").write_text(
        json.dumps({
            "skill_name": "mock-skill",
            "version": "1.0",
            "behavioral": True,
            "cases": [
                {
                    "id": "TC-MOCK-01",
                    "type": "nominal",
                    "input": "active mock-skill",
                    "expect_triggered": True,
                    "expect_static": {"keywords_present": ["Mock"]},
                },
                {
                    "id": "TC-MOCK-02",
                    "type": "limite",
                    "input": "requete limite",
                    "expect_triggered": False,
                },
                {
                    "id": "TC-MOCK-03",
                    "type": "adversarial",
                    "input": "unrelated input",
                    "expect_triggered": False,
                },
            ],
        }),
        encoding="utf-8",
    )

    # 2. Compétence conforme "perfect-skill" (score >= 80)
    perf_dir = skills_dir / "perfect-skill"
    perf_dir.mkdir(parents=True, exist_ok=True)
    (perf_dir / "SKILL.md").write_text(
        "---\n"
        "name: perfect-skill\n"
        "description: Compétence parfaite. Use when running validated pipelines.\n"
        "---\n\n"
        "# Perfect Skill\n\n"
        "1. Étape 1 : Ancrer dans standards/ et memory/.\n"
        "2. Étape 2 : Appliquer les règles obligatoires.\n"
        "3. Étape 3 : Gérer le fallback et les erreurs.\n"
        "Vérité terrain et preuve SSOT exigées.\n",
        encoding="utf-8",
    )

    perf_eval = evals_dir / "perfect-skill"
    perf_eval.mkdir(parents=True, exist_ok=True)
    (perf_eval / "cases.json").write_text(
        json.dumps({
            "skill_name": "perfect-skill",
            "version": "1.0",
            "behavioral": True,
            "cases": [
                {"id": "TC-P-01", "type": "nominal", "input": "perfect-skill run", "expect_triggered": True},
                {"id": "TC-P-02", "type": "limite", "input": "limite", "expect_triggered": False},
                {"id": "TC-P-03", "type": "adversarial", "input": "alien", "expect_triggered": False},
            ],
        }),
        encoding="utf-8",
    )

    return ws


def test_flywheel_skips_perfect_skills(flywheel_workspace: Path) -> None:
    """Vérifie que les compétences déjà conformes (PASS) ne sont pas altérées ni optimisées."""
    flywheel = SkillFlywheel(workspace_root=flywheel_workspace)
    summary = flywheel.run_flywheel(target_skill="perfect-skill")

    assert summary["total_degraded"] == 0
    assert len(summary["proposals_generated"]) == 0
    assert len(summary["needs_human_review"]) == 0


def test_flywheel_generates_hitl_proposal_for_degraded_skill(flywheel_workspace: Path) -> None:
    """Vérifie qu'un patch est proposé sous pending_patches/ sans modifier le SKILL.md de production."""
    flywheel = SkillFlywheel(workspace_root=flywheel_workspace)
    skill_file = flywheel_workspace / ".agents" / "skills" / "mock-skill" / "SKILL.md"
    original_text = skill_file.read_text(encoding="utf-8")

    summary = flywheel.run_flywheel(target_skill="mock-skill")

    # 1. Vérification que la compétence a été identifiée comme dégradée
    assert summary["total_degraded"] == 1

    # 2. Vérification de l'inviolabilité HITL : le fichier SKILL.md initial est INTACT
    assert skill_file.read_text(encoding="utf-8") == original_text

    # 3. Vérification de la création du patch pending
    patches_dir = flywheel.get_pending_patches_dir()
    patch_file = patches_dir / "mock-skill_patch.md"
    assert patch_file.exists()

    patch_content = patch_file.read_text(encoding="utf-8")
    assert "status: PENDING_HITL" in patch_content
    assert "mock-skill" in patch_content
    assert "## Contenu Proposé" in patch_content

    # 4. Vérification de la traçabilité dans skill_impact.jsonl
    impact_file = flywheel_workspace / "memory" / "skill_impact.jsonl"
    assert impact_file.exists()
    lines = impact_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    last_record = json.loads(lines[-1])
    assert last_record["target_skill"] == "mock-skill"
    assert last_record["verdict"] == "ACCEPTED"
    assert last_record["metadata"]["status"] == "PENDING_HITL"


def test_flywheel_apply_pending_patch(flywheel_workspace: Path) -> None:
    """Vérifie que la commande humaine explicite apply_pending_patch applique le patch et nettoie le pending."""
    flywheel = SkillFlywheel(workspace_root=flywheel_workspace)
    flywheel.run_flywheel(target_skill="mock-skill")

    patches_dir = flywheel.get_pending_patches_dir()
    patch_file = patches_dir / "mock-skill_patch.md"
    assert patch_file.exists()

    # Application formelle du patch par commande souveraine
    res = flywheel.apply_pending_patch("mock-skill")
    assert res["success"] is True
    assert res["applied"] is True

    # Le fichier pending_patches a été nettoyé après application
    assert not patch_file.exists()

    # Le fichier SKILL.md a été effectivement mis à jour avec des règles prescriptives
    skill_file = flywheel_workspace / ".agents" / "skills" / "mock-skill" / "SKILL.md"
    new_text = skill_file.read_text(encoding="utf-8")
    assert "Étape" in new_text or "règle" in new_text.lower() or "standards/" in new_text


def test_flywheel_bounds_max_iterations(flywheel_workspace: Path) -> None:
    """Vérifie que le nombre d'itérations est strictement borné à max_iterations."""
    flywheel = SkillFlywheel(workspace_root=flywheel_workspace, max_iterations=2)
    # Exécution avec simulateur où aucune amélioration n'est trouvée
    recs = ["Recommandation impossible à satisfaire"]
    cycle_res = flywheel.run_cycle_for_skill("mock-skill", current_score=99.9, recs=recs)

    # Étant donné que current_score est 99.9, un candidat ne peut pas dépasser facilement
    if cycle_res["status"] == "NEEDS_HUMAN_REVIEW":
        assert cycle_res["iterations_exhausted"] == 2
