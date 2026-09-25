# -*- coding: utf-8 -*-
"""
tests/test_skill_eval.py — Tests unitaires et d'intégration pour MLOOP-240-BE (SkillEvalEngine).
Valide la conformité ADR-0202 (<= 300 lignes), ADR-0369 et ADR-0389.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pipelines.skill_eval import (
    HEAVY_META_SKILLS,
    SkillEvalEngine,
    SkillEvalResult,
)


@pytest.fixture
def temp_skills_workspace(tmp_path: Path) -> Path:
    """Crée une arborescence de compétences temporaire pour les tests."""
    ws = tmp_path / "workspace"
    skills_dir = ws / ".agents" / "skills"
    evals_dir = ws / "Projects" / "mLoop" / "memory" / "evals" / "skills"

    # 1. Compétence standard "grill"
    grill_dir = skills_dir / "grill"
    grill_dir.mkdir(parents=True, exist_ok=True)
    (grill_dir / "SKILL.md").write_text(
        "---\n"
        "name: grill\n"
        "description: Session contradictoire Grill-Me. Use when analyzing epics and validating stories.\n"
        "---\n\n"
        "# Grill Skill\n\n"
        "## Pipeline d'exécution\n"
        "1. Étape 1 : Analyser le contexte dans standards/ et memory/.\n"
        "2. Étape 2 : Poser des questions orthogonales (règle obligatoire : zéro complaisance).\n"
        "3. Étape 3 : Spécifier le comportement en cas de timeout ou erreur de validation.\n"
        "Vérité terrain garantie par verbatim.\n",
        encoding="utf-8",
    )

    # Golden dataset pour "grill"
    grill_eval_dir = evals_dir / "grill"
    grill_eval_dir.mkdir(parents=True, exist_ok=True)
    cases_grill = {
        "skill_name": "grill",
        "version": "1.0",
        "behavioral": True,
        "cases": [
            {
                "id": "TC-GRILL-01",
                "type": "nominal",
                "input": "grill EPIC-24",
                "expect_triggered": True,
                "expect_static": {
                    "keywords_present": ["Pipeline", "Étape"],
                    "keywords_absent": ["hardcoded_secret"],
                },
            },
            {
                "id": "TC-GRILL-02",
                "type": "limite",
                "input": "débogue ce script python",
                "expect_triggered": False,
                "expect_static": {
                    "keywords_present": ["standards/"],
                },
            },
        ],
    }
    (grill_eval_dir / "cases.json").write_text(json.dumps(cases_grill), encoding="utf-8")

    # 2. Compétence méta lourde "sentinel" (dans HEAVY_META_SKILLS)
    sentinel_dir = skills_dir / "sentinel"
    sentinel_dir.mkdir(parents=True, exist_ok=True)
    (sentinel_dir / "SKILL.md").write_text(
        "---\n"
        "name: sentinel\n"
        "description: Contrôle souverain Sentinel. Use when evaluating critical security fences.\n"
        "disable-model-invocation: true\n"
        "---\n\n"
        "# Sentinel Skill\n\n"
        "1. Étape 1 : Vérifier les standards/ et memory/.\n"
        "Règle stricte et obligatoire. Fallback en cas d'erreur réseau.\n"
        "Preuve et vérité terrain exigées.\n",
        encoding="utf-8",
    )

    # 3. Compétence avec Golden Dataset manquant "archify"
    archify_dir = skills_dir / "archify"
    archify_dir.mkdir(parents=True, exist_ok=True)
    (archify_dir / "SKILL.md").write_text(
        "---\n"
        "name: archify\n"
        "description: Cartographie d'architecture. Use when generating architecture diagrams.\n"
        "---\n\n"
        "# Archify\n\n"
        "1. Étape 1 : Ancrer dans standards/ et memory/.\n"
        "Règle de confinement stricte. Gestion d'erreur et fallback.\n"
        "Preuve SSOT validée.\n",
        encoding="utf-8",
    )

    return ws


def test_evaluate_skill_nominal_with_golden_dataset(temp_skills_workspace: Path) -> None:
    """Vérifie l'évaluation nominale avec couplage 80/20 de la rubrique et du Golden Dataset."""
    engine = SkillEvalEngine(workspace_root=temp_skills_workspace, pass_threshold=80.0)
    skill_file = temp_skills_workspace / ".agents" / "skills" / "grill" / "SKILL.md"

    res = engine.evaluate_skill(skill_file)

    assert isinstance(res, SkillEvalResult)
    assert res.skill_name == "grill"
    assert res.scores_breakdown["golden_dataset"] == 100.0
    assert res.total_score >= 80.0
    assert res.verdict == "PASS"
    assert res.golden_dataset_detail is not None
    assert res.golden_dataset_detail["passed_cases"] == 2
    assert res.golden_dataset_detail["total_cases"] == 2


def test_heavy_meta_skill_excludes_golden_dataset(temp_skills_workspace: Path) -> None:
    """Vérifie que les HEAVY_META_SKILLS ont un score 100% statique et golden_dataset = None."""
    assert "sentinel" in HEAVY_META_SKILLS
    engine = SkillEvalEngine(workspace_root=temp_skills_workspace, pass_threshold=80.0)
    skill_file = temp_skills_workspace / ".agents" / "skills" / "sentinel" / "SKILL.md"

    res = engine.evaluate_skill(skill_file)

    assert res.skill_name == "sentinel"
    assert res.scores_breakdown["golden_dataset"] is None
    assert res.golden_dataset_detail["status"] == "EXCLUDED"
    assert res.verdict == "PASS"


def test_evaluate_with_missing_golden_dataset(temp_skills_workspace: Path) -> None:
    """Vérifie la dégradation gracieuse quand cases.json est absent (golden_score = 0, warning/recs)."""
    engine = SkillEvalEngine(workspace_root=temp_skills_workspace, pass_threshold=80.0)
    skill_file = temp_skills_workspace / ".agents" / "skills" / "archify" / "SKILL.md"

    res = engine.evaluate_skill(skill_file)

    assert res.skill_name == "archify"
    assert res.scores_breakdown["golden_dataset"] == 0.0
    assert any("Golden Dataset" in rec for rec in res.recommendations)
    # Dégradation gracieuse : l'évaluation s'est terminée sans exception
    assert res.total_score > 0.0


def test_evaluate_with_golden_dataset_direct_method(temp_skills_workspace: Path) -> None:
    """Vérifie la méthode evaluate_with_golden_dataset par nom de compétence."""
    engine = SkillEvalEngine(workspace_root=temp_skills_workspace)
    res = engine.evaluate_with_golden_dataset("grill")

    assert res.skill_name == "grill"
    assert res.verdict == "PASS"
    assert res.scores_breakdown["golden_dataset"] == 100.0


def test_evaluate_with_custom_cases_path(temp_skills_workspace: Path, tmp_path: Path) -> None:
    """Vérifie l'évaluation avec un fichier cases.json personnalisé spécifié explicitement."""
    custom_cases = tmp_path / "custom_cases.json"
    custom_cases.write_text(
        json.dumps({
            "skill_name": "grill",
            "cases": [
                {
                    "id": "TC-CUSTOM-01",
                    "input": "non_matching_query",
                    "expect_triggered": True,  # Doit échouer car pas de trigger match
                }
            ],
        }),
        encoding="utf-8",
    )

    engine = SkillEvalEngine(workspace_root=temp_skills_workspace)
    res = engine.evaluate_with_golden_dataset("grill", cases_path=custom_cases)

    assert res.golden_dataset_detail["passed_cases"] == 0
    assert res.scores_breakdown["golden_dataset"] == 0.0
    assert any("Déclenchement attendu non détecté" in f for f in res.blocking_flaws)


def test_evaluate_all_skills_and_save_reports(temp_skills_workspace: Path) -> None:
    """Vérifie evaluate_all_skills et la persistance des 4 fichiers de rapport (ADR-0389)."""
    engine = SkillEvalEngine(workspace_root=temp_skills_workspace)
    summary = engine.evaluate_all_skills()

    assert summary["total_skills"] == 3
    assert "average_score" in summary
    assert "passed" in summary
    assert len(summary["results"]) == 3

    out_dir = temp_skills_workspace / "output_reports"
    s_json, s_md = engine.save_reports(summary, output_dir=out_dir)

    assert s_json.exists()
    assert s_md.exists()
    assert (out_dir / "skills_eval_summary.json").exists()
    assert (out_dir / "skills_eval_summary.md").exists()
    assert (out_dir / "skills_eval_report.json").exists()
    assert (out_dir / "skills_eval_report.md").exists()

    # Vérification du contenu JSON
    data = json.loads(s_json.read_text(encoding="utf-8"))
    assert data["total_skills"] == 3
    assert "certified_at" in data

    # Vérification du contenu Markdown
    md_content = s_md.read_text(encoding="utf-8")
    assert "Matrice d'Évaluation Complète" in md_content
    assert "Golden (/100)" in md_content
