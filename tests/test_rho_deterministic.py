"""
Tests déterministes pour la rétrospective RHO et la détection d'anomalies mécaniques.
"""
import pytest
import json
from pathlib import Path
from src.pipelines.deterministic_checks import (
    classify_anomaly,
    check_no_placeholders,
    check_focus_lock,
    check_python_deep_module_boundaries,
)
from src.pipelines.rho_optimizer import optimize_rho


def test_classify_anomaly_mechanical_vs_judgement():
    """Vérifie la bonne classification des anomalies en mécanique vs jugement."""
    cat, check = classify_anomaly("Detection of placeholder code or // TODO comments")
    assert cat == "MECHANICAL"
    assert check == "no_placeholders"

    cat, check = classify_anomaly("No active story identified in IN_ANALYZE status")
    assert cat == "MECHANICAL"
    assert check == "focus_lock"

    cat, check = classify_anomaly("Deep module violation: internal import without barrel")
    assert cat == "MECHANICAL"
    assert check == "deep_module_boundaries"

    cat, check = classify_anomaly("Complex business tradeoff in checkout pricing calculation")
    assert cat == "JUDGEMENT"
    assert check is None


def test_check_no_placeholders():
    """Vérifie la détection exacte des placeholders et TODOs interdits."""
    clean_code = "def add(a, b):\n    return a + b\n"
    dirty_code = "def add(a, b):\n    // TODO: implement this\n    return a + b\n"

    assert len(check_no_placeholders(clean_code)) == 0
    violations = check_no_placeholders(dirty_code)
    assert len(violations) == 1
    assert violations[0]["line"] == 2
    assert violations[0]["rule"] == "BANNED_PLACEHOLDER"


def test_check_focus_lock():
    """Vérifie le verrouillage de focus sur une User Story active."""
    assert check_focus_lock(None)["valid"] is False
    assert check_focus_lock("")["valid"] is False
    assert check_focus_lock("random-string")["valid"] is False
    assert check_focus_lock("US-102")["valid"] is True
    assert check_focus_lock("SPIKE-003")["valid"] is True


def test_optimize_rho_deterministic_bifurcation():
    """Vérifie que les règles mécaniques sont envoyées aux linters sans modifier rho_rules.yaml."""
    det_file = Path("standards") / "linters" / "deterministic_rules.json"

    success = optimize_rho(
        project_name="test_proj",
        keyword="placeholder detection",
        msg="Do not allow // TODO comments",
        scope="global",
    )
    assert success is True

    # Le fichier de règles déterministes existe et contient la règle
    assert det_file.exists()
    import json
    data = json.loads(det_file.read_text(encoding="utf-8"))
    assert any(r.get("check_type") == "no_placeholders" for r in data)


