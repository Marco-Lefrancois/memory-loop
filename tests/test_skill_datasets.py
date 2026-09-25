# -*- coding: utf-8 -*-
"""
tests/test_skill_datasets.py — Tests de conformité et de validation pour MLOOP-241-BE.
Valide la conformité ADR-0202 (<= 300 lignes), ADR-0369 et ADR-0389.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.pipelines.skill_eval import HEAVY_META_SKILLS, SkillEvalEngine


@pytest.fixture
def repo_root() -> Path:
    """Racine du dépôt mLoop."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def schema_data(repo_root: Path) -> dict:
    """Charge le schéma JSON canonique des Golden Datasets."""
    schema_file = repo_root / "standards" / "schemas" / "skill_eval_case_schema.json"
    assert schema_file.exists(), f"Schéma introuvable : {schema_file}"
    return json.loads(schema_file.read_text(encoding="utf-8"))


def test_schema_validates_all_39_generated_datasets(repo_root: Path, schema_data: dict) -> None:
    """Vérifie que chacun des 39 fichiers cases.json est strictement conforme au schéma JSON Schema."""
    skills_eval_dir = repo_root / "Projects" / "mLoop" / "memory" / "evals" / "skills"
    assert skills_eval_dir.exists(), f"Dossier introuvable : {skills_eval_dir}"

    cases_files = sorted(list(skills_eval_dir.glob("*/cases.json")))
    assert len(cases_files) == 39, f"Attendu 39 fichiers cases.json, trouvé {len(cases_files)}"

    for cf in cases_files:
        payload = json.loads(cf.read_text(encoding="utf-8"))
        # Doit valider sans lever de jsonschema.ValidationError
        jsonschema.validate(instance=payload, schema=schema_data)


def test_parity_between_agents_skills_and_datasets(repo_root: Path) -> None:
    """Vérifie la parité 1:1 exacte entre les compétences déclarées et les Golden Datasets."""
    declared_skills = sorted([d.name for d in (repo_root / ".agents" / "skills").iterdir() if d.is_dir() and (d / "SKILL.md").exists()])
    dataset_skills = sorted([d.name for d in (repo_root / "Projects" / "mLoop" / "memory" / "evals" / "skills").iterdir() if d.is_dir() and (d / "cases.json").exists()])

    assert len(declared_skills) == 39
    assert len(dataset_skills) == 39
    assert declared_skills == dataset_skills


def test_heavy_meta_skills_behavioral_false(repo_root: Path) -> None:
    """Vérifie que les 8 HEAVY_META_SKILLS ont 'behavioral: false' et category 'META_ORCHESTRATION'."""
    skills_eval_dir = repo_root / "Projects" / "mLoop" / "memory" / "evals" / "skills"
    for meta_name in HEAVY_META_SKILLS:
        cf = skills_eval_dir / meta_name / "cases.json"
        assert cf.exists(), f"Fichier cases.json manquant pour le méta-skill {meta_name}"
        data = json.loads(cf.read_text(encoding="utf-8"))
        assert data.get("behavioral") is False, f"{meta_name} doit avoir behavioral=False"
        assert data.get("category") == "META_ORCHESTRATION"


def test_each_dataset_has_minimum_3_tripartite_cases(repo_root: Path) -> None:
    """Vérifie que chaque fichier possède au minimum 3 cas (1 nominal, 1 limite, 1 adversarial)."""
    skills_eval_dir = repo_root / "Projects" / "mLoop" / "memory" / "evals" / "skills"
    for cf in skills_eval_dir.glob("*/cases.json"):
        data = json.loads(cf.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        assert len(cases) >= 3, f"{cf.parent.name} doit avoir au moins 3 cas de test"
        types = {c.get("type") for c in cases}
        assert "nominal" in types, f"Cas nominal manquant pour {cf.parent.name}"
        assert "limite" in types, f"Cas limite manquant pour {cf.parent.name}"
        assert "adversarial" in types, f"Cas adversarial manquant pour {cf.parent.name}"


def test_schema_rejects_invalid_dataset(schema_data: dict) -> None:
    """Vérifie que le schéma rejette formellement un jeu de données invalide."""
    invalid_payload = {
        "skill_name": "x",  # Trop court (minLength=2)
        "version": "1.0",
        "cases": [
            {"id": "TC-01", "type": "unsupported_type", "description": "Court", "input": "hi"}
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_payload, schema=schema_data)


def test_skill_eval_engine_evaluates_all_39_with_datasets(repo_root: Path) -> None:
    """Test d'intégration global : SkillEvalEngine évalue l'ensemble des 39 compétences avec Golden Datasets."""
    engine = SkillEvalEngine(workspace_root=repo_root)
    summary = engine.evaluate_all_skills()

    assert summary["total_skills"] == 39
    assert summary["average_score"] > 60.0
    assert len(summary["results"]) == 39

    # Vérification que le champ golden_dataset est bien renseigné
    for res in summary["results"]:
        skill_name = res["skill_name"]
        b = res["scores_breakdown"]
        if skill_name in HEAVY_META_SKILLS:
            assert b["golden_dataset"] is None
        else:
            assert b["golden_dataset"] is not None
            assert isinstance(b["golden_dataset"], (int, float))
