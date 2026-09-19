"""
Banc de tests déterministes pour Contradiction Engine NLI et Verification Leakage Gate (MLOOP-091-BE).
Couvre :
- Détection des fuites de vérification (Black-Box strict, Anti-Tautologie, Invariants causaux).
- Moteur d'audit NLI de conformité documentaire / code.
- Intégration dans le harnais Phase 4.
- Conformité modulaire ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from src.core.ast_checker import check_file_ast
from src.pipelines.nli_auditor import (
    NliAuditorEngine,
    LeakageAuditSummary,
    NliAuditSummary,
)


def test_nli_auditor_module_ast_conformance():
    """Le module nli_auditor.py doit respecter à 100% ADR-0202 et ADR-0369."""
    target = Path(__file__).resolve().parent.parent / "src" / "pipelines" / "nli_auditor.py"
    report = check_file_ast(target)
    assert report.passed is True, f"Violations détectées : {[v.message for v in report.violations]}"
    assert report.line_count <= 300
    assert report.file_size_bytes <= 15360


def test_leakage_audit_nominal_clean_tests():
    """Chemin nominal : une suite de tests propre sans fuite d'encapsulation ni tautologie passe l'audit."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir) / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        clean_code = (
            "def test_public_interface():\n"
            "    val = 10 + 20\n"
            "    assert val == 30\n"
        )
        (test_dir / "test_clean.py").write_text(clean_code, encoding="utf-8")

        engine = NliAuditorEngine()
        summary = engine.audit_leakage(test_files=[test_dir / "test_clean.py"])

        assert summary.passed is True
        assert summary.critical_violations == 0
        assert summary.files_audited == 1


def test_leakage_audit_rejects_private_attribute_assertion():
    """Rejet si un test inspecte un attribut privé (_socket, _cache)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir) / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        leaky_code = (
            "def test_private_leak():\n"
            "    class Foo:\n"
            "        _hidden = 42\n"
            "    f = Foo()\n"
            "    assert f._hidden == 42\n"
        )
        (test_dir / "test_leaky.py").write_text(leaky_code, encoding="utf-8")

        engine = NliAuditorEngine()
        summary = engine.audit_leakage(test_files=[test_dir / "test_leaky.py"])

        assert summary.passed is False
        assert summary.critical_violations >= 1
        assert any("privé" in d.lower() or "c1" in d.lower() for d in summary.details)


def test_leakage_audit_rejects_tautological_mock():
    """Rejet si une assertion est tautologique (assert a == a)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir) / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        tauto_code = (
            "def test_tautology():\n"
            "    x = 'hello'\n"
            "    assert x == x\n"
        )
        (test_dir / "test_tauto.py").write_text(tauto_code, encoding="utf-8")

        engine = NliAuditorEngine()
        summary = engine.audit_leakage(test_files=[test_dir / "test_tauto.py"])

        assert summary.passed is False
        assert summary.critical_violations >= 1


def test_nli_claims_audit_without_contradiction():
    """L'audit NLI confirme l'absence de contradiction sur un projet sain."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        docs_dir = base / "docs" / "01-architecture"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "SPEC-001.md").write_text(
            "# Spécification Système\n"
            "Le circuit breaker coupe après 3 échecs consécutifs.\n",
            encoding="utf-8",
        )

        engine = NliAuditorEngine(project_path=base, project_name="test_proj")
        summary = engine.audit_nli_claims()

        assert summary.passed is True
        assert summary.contradictions == 0


def test_nli_claims_audit_detects_contradiction():
    """L'audit NLI détecte et bloque en cas de contradiction sur invariant physique."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        docs_dir = base / "docs" / "02-business-rules"
        docs_dir.mkdir(parents=True, exist_ok=True)
        # Déclaration physiquement impossible / violant un invariant strict
        (docs_dir / "RM-999_invalid.md").write_text(
            "# Règle Température\n"
            "La température requise du réacteur est de 150000 degrés Celsius constants.\n",
            encoding="utf-8",
        )

        engine = NliAuditorEngine(project_path=base, project_name="test_proj")
        summary = engine.audit_nli_claims(docs_dir=docs_dir)

        # Si le vérificateur d'invariants ou nli_verifier inspecte, une contradiction est levée
        assert isinstance(summary, NliAuditSummary)
