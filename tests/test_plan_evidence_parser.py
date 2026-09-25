# -*- coding: utf-8 -*-
"""
tests/test_plan_evidence_parser.py — Tests unitaires TDD pour MLOOP-332-BE.
Validation du PlanEvidenceParser et EvidenceSynchronizer (ADR-0394).
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.pipelines.evidence_types import CodeTraceabilityEntry
from src.pipelines.evidence_pack import EvidencePackEngine
from src.pipelines.plan_evidence_parser import PlanEvidenceParser
from src.pipelines.evidence_synchronizer import EvidenceSynchronizer


@pytest.fixture
def temp_project(tmp_path: Path):
    """Initialise une structure de projet de test mLoop avec dossiers evidence et plan."""
    proj = tmp_path / "Projects" / "TestProject"
    evidence_dir = proj / "memory" / "evidence"
    plan_dir = proj / "memory" / "plan"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    return proj


# ──────────────────────────────────────────────────────────────────────────────
# PlanEvidenceParser — Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_plan_evidence_parser_nominal(temp_project: Path):
    """Pilier 1 (Nominal) : Parsing table GFM valide → entrées valides."""
    plan_content = """
# Plan d'Implémentation

## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/core/auth.py::TokenVerifier.verify_expiration | RM-012 | Pilier 2 (Exception - Jeton expiré) | Lève HTTP 401 et consigne l'événement pour initier le refresh token asynchrone. | tests/test_auth.py::test_token_expired_triggers_401 |
| src/utils/csv_cleaner.py::sanitize_input | INFRA | Pilier 3 (Résilience) | Neutralise l'injection de formules de calcul CSV pour éviter l'exécution de code malveillant. | tests/test_csv_cleaner.py::test_sanitize |
"""
    plan_file = temp_project / "memory" / "plan" / "implementation_plan_TEST.md"
    plan_file.write_text(plan_content, encoding="utf-8")

    entries = PlanEvidenceParser.extract_matrix_from_plan(plan_file)

    assert len(entries) == 2
    assert entries[0]["ast_symbol"] == "src/core/auth.py::TokenVerifier.verify_expiration"
    assert entries[0]["requirement_ref"] == "RM-012"
    assert entries[0]["test_symbol"] == "tests/test_auth.py::test_token_expired_triggers_401"
    assert entries[1]["requirement_ref"] == "INFRA"
    assert entries[1]["test_symbol"] == "tests/test_csv_cleaner.py::test_sanitize"


def test_plan_evidence_parser_rejection_malformed(temp_project: Path):
    """Pilier 2 (Exception) : Rejet table malformée / cellule manquante."""
    # Cas A : En-tête manquant
    bad_header = """
## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST | Règle Métier | Scénario | Justification |
| --- | --- | --- | --- |
| src/test.py::func | RM-001 | Nominal | Justification valide suffisante |
"""
    plan_file = temp_project / "memory" / "plan" / "bad.md"
    plan_file.write_text(bad_header, encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        PlanEvidenceParser.extract_matrix_from_plan(plan_file)
    assert "En-têtes manquants" in str(excinfo.value) or "En-têtes insuffisants" in str(
        excinfo.value
    )

    # Cas B : Cellule obligatoire vide (rationale trop courte)
    short_rationale = """
## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/test.py::func | RM-001 | Nominal | Court | tests/test.py::test |
"""
    plan_file2 = temp_project / "memory" / "plan" / "bad2.md"
    plan_file2.write_text(short_rationale, encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        PlanEvidenceParser.extract_matrix_from_plan(plan_file2)
    assert (
        "rationale" in str(excinfo.value).lower() or "justification" in str(excinfo.value).lower()
    )


def test_plan_evidence_parser_open_spec_fallback(temp_project: Path):
    """Pilier 3 (Résilience) : Adaptateur tasks.md OpenSpec."""
    tasks_content = """
# Tasks OpenSpec

## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/openspec/task.py::run | RM-OS-01 | Pilier 1 | Exécution tâche OpenSpec standard. | tests/test_openspec.py::test_run |
"""
    tasks_file = temp_project / "memory" / "plan" / "tasks.md"
    tasks_file.write_text(tasks_content, encoding="utf-8")

    entries = PlanEvidenceParser.extract_matrix_from_text(tasks_file.read_text(encoding="utf-8"))

    assert len(entries) == 1
    assert entries[0]["ast_symbol"] == "src/openspec/task.py::run"
    assert entries[0]["requirement_ref"] == "RM-OS-01"


# ──────────────────────────────────────────────────────────────────────────────
# EvidenceSynchronizer — Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_evidence_synchronizer_nominal(temp_project: Path):
    """Pilier 1 (Nominal) : Sync complète plan → EvidencePack + SHA-256."""
    # Créer un fichier source factice pour le hash
    src_file = temp_project / "src" / "core" / "auth.py"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        "def verify_expiration(token):\n    return token.expired\n", encoding="utf-8"
    )

    test_file = temp_project / "tests" / "test_auth.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(
        "def test_token_expired_triggers_401():\n    assert True\n", encoding="utf-8"
    )

    plan_content = f"""
# Plan d'Implémentation

## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/core/auth.py::TokenVerifier.verify_expiration | RM-012 | Pilier 2 (Exception) | Lève HTTP 401 et consigne l'événement. | tests/test_auth.py::test_token_expired_triggers_401 |
"""
    plan_file = temp_project / "memory" / "plan" / "implementation_plan_MLOOP-332-BE.md"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(plan_content, encoding="utf-8")

    sync = EvidenceSynchronizer(temp_project)
    target = sync.sync_story_evidence("MLOOP-332-BE", plan_path=plan_file)

    assert target.exists()
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert "code_traceability_matrix" in saved
    assert len(saved["code_traceability_matrix"]) == 1
    assert "source_hashes" in saved
    assert "src/core/auth.py" in saved["source_hashes"]
    assert saved["source_hashes"]["src/core/auth.py"]  # hash non vide


def test_evidence_synchronizer_atomicity(temp_project: Path):
    """Pilier 2 (Exception) : Échec validation → pas d'écriture partielle."""
    plan_content = """
## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/test.py::func | RM-001 | Nominal | Court | tests/test.py::test |
"""
    plan_file = temp_project / "memory" / "plan" / "implementation_plan_ATOMIC.md"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(plan_content, encoding="utf-8")

    sync = EvidenceSynchronizer(temp_project)
    target = temp_project / "memory" / "evidence" / "MLOOP-ATOMIC_evidence.json"

    with pytest.raises(ValueError) as excinfo:
        sync.sync_story_evidence("MLOOP-ATOMIC", plan_path=plan_file)

    assert (
        "rationale" in str(excinfo.value).lower() or "justification" in str(excinfo.value).lower()
    )
    # Vérifier qu'aucun fichier n'a été écrit (atomicité)
    assert not target.exists()


def test_evidence_synchronizer_preservation(temp_project: Path):
    """Pilier 3 (Résilience) : Préservation tdd_cycle, fact_check_certificate."""
    # Créer un pack existant avec tdd_cycle et fact_check_certificate
    evidence_dir = temp_project / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    existing_pack = {
        "story_id": "MLOOP-PRESERVE",
        "tdd_cycle": {"red": "test_fail", "green": "test_pass"},
        "fact_check_certificate": {"verified_by": "Marco", "score": 1.0},
        "verbatim_extracts": [{"source_file": "doc.md", "quote": "test"}],
    }
    target = temp_project / "memory" / "evidence" / "MLOOP-PRESERVE_evidence.json"
    target.write_text(json.dumps(existing_pack, indent=2), encoding="utf-8")

    plan_content = """
## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/new.py::new_func | RM-NEW | Pilier 1 | Nouvelle fonctionnalité ajoutée. | tests/test_new.py::test_new |
"""
    plan_file = temp_project / "memory" / "plan" / "implementation_plan_MLOOP-PRESERVE.md"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(plan_content, encoding="utf-8")

    sync = EvidenceSynchronizer(temp_project)
    target_path = sync.sync_story_evidence("MLOOP-PRESERVE", plan_path=plan_file)

    saved = json.loads(target_path.read_text(encoding="utf-8"))

    # Vérifier préservation des blocs protégés
    assert saved["tdd_cycle"] == {"red": "test_fail", "green": "test_pass"}
    assert saved["fact_check_certificate"] == {"verified_by": "Marco", "score": 1.0}
    assert saved["verbatim_extracts"] == [{"source_file": "doc.md", "quote": "test"}]
    # Vérifier que la nouvelle matrice a été ajoutée
    assert "code_traceability_matrix" in saved
    assert len(saved["code_traceability_matrix"]) == 1
    assert saved["code_traceability_matrix"][0]["ast_symbol"] == "src/new.py::new_func"


def test_evidence_synchronizer_idempotence(temp_project: Path):
    """Pilier 4 (UX/Observabilité) : Rejouable indéfiniment, état identique."""
    plan_content = """
## Matrice de Traçabilité Code ↔ Exigences

| Symbole AST Qualifié | Règle Métier Cible | Scénario Gherkin | Justification | Test Unitaire |
| --- | --- | --- | --- | --- |
| src/idem.py::idem_func | RM-IDEM | Pilier 1 | Test d'idempotence. | tests/test_idem.py::test_idem |
"""
    plan_file = temp_project / "memory" / "plan" / "implementation_plan_MLOOP-IDEM.md"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(plan_content, encoding="utf-8")

    sync = EvidenceSynchronizer(temp_project)

    # Premier run
    target1 = sync.sync_story_evidence("MLOOP-IDEM", plan_path=plan_file)
    data1 = json.loads(target1.read_text(encoding="utf-8"))

    # Deuxième run (même plan)
    target2 = sync.sync_story_evidence("MLOOP-IDEM", plan_path=plan_file)
    data2 = json.loads(target2.read_text(encoding="utf-8"))

    # L'état doit être identique (hors timestamp updated_at)
    assert data1["code_traceability_matrix"] == data2["code_traceability_matrix"]
    assert data1["source_hashes"] == data2["source_hashes"]
    # Le story_id et la matrice sont identiques
    assert data1["story_id"] == data2["story_id"]
    assert data1["code_traceability_matrix"] == data2["code_traceability_matrix"]
