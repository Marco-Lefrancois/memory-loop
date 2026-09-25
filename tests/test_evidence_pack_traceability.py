# -*- coding: utf-8 -*-
"""
tests/test_evidence_pack_traceability.py — Tests unitaires TDD pour MLOOP-330-BE.
Validation de la Matrice de Traçabilité Code ↔ Exigences (ADR-0394 / OpenSpec Ready).
"""

import json
import pytest
from pathlib import Path
from src.pipelines.evidence_pack import (
    EvidencePackEngine,
    CodeTraceabilityEntry,
)


@pytest.fixture
def temp_project(tmp_path: Path):
    """Initialise une structure de projet de test mLoop avec dossier evidence."""
    proj = tmp_path / "Projects" / "TestProject"
    evidence_dir = proj / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return proj


def test_code_traceability_nominal_valid(temp_project: Path):
    """Pilier 1 (Nominal) : Validation et sérialisation d'une entrée conforme."""
    engine = EvidencePackEngine(project_path=temp_project)

    entries = [
        CodeTraceabilityEntry(
            ast_symbol="src/core/auth.py::TokenVerifier.verify_expiration",
            requirement_ref="RM-012",
            gherkin_scenario="Pilier 2 (Exception - Jeton expiré)",
            rationale="Lève HTTP 401 et consigne l'événement pour initier le refresh token asynchrone.",
            test_symbol="tests/test_auth.py::test_token_expired_triggers_401",
        )
    ]

    # 1. Validation unitaire
    assert engine.validate_code_traceability(entries) is True

    # 2. Sérialisation dans l'EvidencePack sidecar
    target_path = engine.set_code_traceability("MLOOP-330-BE", entries)
    assert target_path.exists()

    saved_data = json.loads(target_path.read_text(encoding="utf-8"))
    assert "code_traceability_matrix" in saved_data
    matrix = saved_data["code_traceability_matrix"]
    assert len(matrix) == 1
    assert matrix[0]["ast_symbol"] == "src/core/auth.py::TokenVerifier.verify_expiration"
    assert matrix[0]["requirement_ref"] == "RM-012"
    assert matrix[0]["test_symbol"] == "tests/test_auth.py::test_token_expired_triggers_401"


def test_code_traceability_rejection_invalid_ast_or_empty_rationale(temp_project: Path):
    """Pilier 2 (Exception) : Rejet strict des entrées mal formées ou sans justification."""
    engine = EvidencePackEngine(project_path=temp_project)

    # Cas A : ast_symbol sans qualificateur de fichier (pas de '::')
    invalid_ast = [
        CodeTraceabilityEntry(
            ast_symbol="verify_token_without_path",
            requirement_ref="RM-012",
            gherkin_scenario="Scénario Nominal",
            rationale="Justification valide de plus de 10 caractères.",
        )
    ]
    with pytest.raises(ValueError) as excinfo:
        engine.validate_code_traceability(invalid_ast)
    assert "ast_symbol" in str(excinfo.value)

    # Cas B : rationale trop courte (< 10 caractères)
    short_rationale = [
        CodeTraceabilityEntry(
            ast_symbol="src/utils/csv.py::clean_cell",
            requirement_ref="RM-014",
            gherkin_scenario="Scénario Nominal",
            rationale="Court",
        )
    ]
    with pytest.raises(ValueError) as excinfo:
        engine.validate_code_traceability(short_rationale)
    assert "rationale" in str(excinfo.value)

    # Cas C : requirement_ref manquant ou vide
    missing_req = [
        CodeTraceabilityEntry(
            ast_symbol="src/utils/csv.py::clean_cell",
            requirement_ref="",
            gherkin_scenario="Scénario Nominal",
            rationale="Justification suffisante pour tester l'absence de règle.",
        )
    ]
    with pytest.raises(ValueError) as excinfo:
        engine.validate_code_traceability(missing_req)
    assert "requirement_ref" in str(excinfo.value)


def test_code_traceability_infra_tech_resilience(temp_project: Path):
    """Pilier 3 (Résilience) : Fonctions techniques avec INFRA / TECH-FOUNDATION autorisées."""
    engine = EvidencePackEngine(project_path=temp_project)

    entries = [
        CodeTraceabilityEntry(
            ast_symbol="src/utils/csv_cleaner.py::sanitize_input",
            requirement_ref="INFRA",
            gherkin_scenario="Pilier 3 (Résilience)",
            rationale="Neutralise l'injection de formules de calcul CSV pour éviter l'exécution de code malveillant.",
            test_symbol="tests/test_csv_cleaner.py::test_sanitize",
        ),
        CodeTraceabilityEntry(
            ast_symbol="src/core/context_mgr.py::safe_sqlite_conn",
            requirement_ref="TECH-FOUNDATION",
            gherkin_scenario="Pilier 3 (Résilience)",
            rationale="Fournit un context manager strict avec timeout et fermeture garantie selon ADR-0369.",
        ),
    ]

    assert engine.validate_code_traceability(entries) is True

    target_path = engine.set_code_traceability("MLOOP-330-BE", entries)
    saved_data = json.loads(target_path.read_text(encoding="utf-8"))
    matrix = saved_data["code_traceability_matrix"]
    assert len(matrix) == 2
    assert matrix[0]["requirement_ref"] == "INFRA"
    assert matrix[1]["requirement_ref"] == "TECH-FOUNDATION"


def test_code_traceability_empty_list_accepted(temp_project: Path):
    """Cas limite : une liste vide de traçabilité est valide (récit sans code produit)."""
    engine = EvidencePackEngine(project_path=temp_project)
    assert engine.validate_code_traceability([]) is True
