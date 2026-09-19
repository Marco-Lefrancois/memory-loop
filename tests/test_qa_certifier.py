"""
Banc de tests déterministes pour le moteur de certification QA Phase 4 (ADR-0383 / MLOOP-090-BE).
Couvre l'intégralité des fonctionnalités :
- Exécution de tests unitaires et détection d'échecs
- Audit statique AST (ADR-0202, ADR-0369)
- Triangulation du Code Evidence Ledger (4 Piliers Gherkin)
- Génération des rapports opposables JSON et Markdown
- Intégration du handler CLI handle_validate_sprint
- Auto-audit AST du module qa_certifier.py (0 violation)
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.ast_checker import check_file_ast
from src.pipelines.qa_certifier import (
    QaCertifierEngine,
    PytestExecutionResult,
    AstAuditSummary,
    CelTriangulationResult,
    QaCertificationReport,
    format_qa_markdown,
    REQUIRED_GHERKIN_PILLARS,
)
from src.commands.handlers.validation import handle_validate_sprint


# ─── FIXTURES & HELPERS ──────────────────────────────────────────────────────

SAMPLE_CEL_COMPLETE = {
    "epic_id": "EPIC-7-AGENTIC-OBSERVABILITY",
    "project": "mLoop",
    "ledger": [
        {
            "story_id": "MLOOP-070-BE",
            "blocks": [
                {
                    "block_id": "B-01",
                    "gherkin_pillar": "PILIER_1_CHEMIN_NOMINAL",
                    "symbol": "PingPongGuard.record_handoff",
                },
                {
                    "block_id": "B-02",
                    "gherkin_pillar": "PILIER_2_EXCEPTIONS_REJETS",
                    "symbol": "PingPongRecursionError",
                },
                {
                    "block_id": "B-03",
                    "gherkin_pillar": "PILIER_3_RESILIENCE_MODE_DEGRADE",
                    "symbol": "PingPongGuard.reset",
                },
                {
                    "block_id": "B-04",
                    "gherkin_pillar": "PILIER_4_UX_OBSERVABILITE",
                    "symbol": "PingPongGuard.get_status",
                },
            ],
        }
    ],
}

SAMPLE_CEL_INCOMPLETE = {
    "epic_id": "EPIC-7-AGENTIC-OBSERVABILITY",
    "project": "mLoop",
    "ledger": [
        {
            "story_id": "MLOOP-070-BE",
            "blocks": [
                {
                    "block_id": "B-01",
                    "gherkin_pillar": "PILIER_1_CHEMIN_NOMINAL",
                    "symbol": "PingPongGuard.record_handoff",
                },
                # Piliers 2, 3 et 4 manquants
            ],
        }
    ],
}


# ─── TESTS UNITAIRES QaCertifierEngine ───────────────────────────────────────

def test_qa_certifier_module_ast_conformance():
    """Le module qa_certifier.py doit respecter à 100% ADR-0202 (<=300L, <=15Ko) et ADR-0369."""
    target = Path("src/pipelines/qa_certifier.py")
    report = check_file_ast(target)
    assert report.passed is True, f"Violations détectées : {[v.message for v in report.violations]}"
    assert report.line_count <= 300
    assert report.file_size_bytes <= 15360


def test_certify_sprint_nominal_all_passed():
    """Chemin nominal : Pytest OK, AST OK, CEL complet -> is_certified = True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        ev_dir = base / "memory" / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        cel_file = ev_dir / "EPIC-7_code_evidence_ledger.json"
        with open(cel_file, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CEL_COMPLETE, f)

        # Mock runner pytest
        mock_runner = MagicMock(return_value=PytestExecutionResult(
            all_passed=True,
            total_tests=15,
            passed_tests=15,
            failed_tests=0,
            duration_seconds=1.25,
            coverage_percent=92.5,
            details="15 passed",
        ))

        engine = QaCertifierEngine(
            project_path=base,
            project_name="test-proj",
            pytest_runner=mock_runner,
        )

        # Créer un faux fichier src conforme
        src_dir = base / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "module.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")

        report = engine.certify_sprint(save_reports=True)

        assert report.is_certified is True
        assert len(report.blocking_reasons) == 0
        assert report.pytest_result.all_passed is True
        assert report.ast_summary.passed is True
        assert report.cel_result.is_complete is True

        # Vérifier que les rapports JSON et MD ont été créés
        json_report = base / "memory" / "qa_certification_report.json"
        md_report = base / "memory" / "qa_certification_report.md"
        assert json_report.exists()
        assert md_report.exists()

        data = json.loads(json_report.read_text(encoding="utf-8"))
        assert data["is_certified"] is True
        assert data["project_name"] == "test-proj"


def test_certify_sprint_fails_on_pytest_failure():
    """Rejet si le banc de tests comporte des échecs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        mock_runner = MagicMock(return_value=PytestExecutionResult(
            all_passed=False,
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            duration_seconds=0.8,
            coverage_percent=80.0,
            details="2 failed, 8 passed",
        ))

        engine = QaCertifierEngine(
            project_path=base,
            project_name="fail-test",
            pytest_runner=mock_runner,
        )

        report = engine.certify_sprint(save_reports=False)
        assert report.is_certified is False
        assert any("pytest" in r.lower() for r in report.blocking_reasons)


def test_certify_sprint_fails_on_ast_violations():
    """Rejet si le code source comporte des violations AST (ADR-0202/ADR-0369)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        mock_runner = MagicMock(return_value=PytestExecutionResult(
            all_passed=True, total_tests=5, passed_tests=5, failed_tests=0, duration_seconds=0.1
        ))

        src_dir = base / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        # Fichier avec ressource nue interdite (RULE-AST-02)
        bad_code = "import sqlite3\nconn = sqlite3.connect('test.db')\n"
        (src_dir / "bad_db.py").write_text(bad_code, encoding="utf-8")

        engine = QaCertifierEngine(
            project_path=base,
            project_name="bad-ast",
            pytest_runner=mock_runner,
        )

        report = engine.certify_sprint(save_reports=False)
        assert report.is_certified is False
        assert report.ast_summary.passed is False
        assert report.ast_summary.total_violations > 0
        assert any("ast" in r.lower() for r in report.blocking_reasons)


def test_certify_sprint_fails_on_missing_gherkin_pillars():
    """Rejet si le Code Evidence Ledger n'a pas tous les 4 Piliers Gherkin couverts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        ev_dir = base / "memory" / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        cel_file = ev_dir / "EPIC-7_code_evidence_ledger.json"
        with open(cel_file, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CEL_INCOMPLETE, f)

        mock_runner = MagicMock(return_value=PytestExecutionResult(
            all_passed=True, total_tests=5, passed_tests=5, failed_tests=0, duration_seconds=0.1
        ))

        engine = QaCertifierEngine(
            project_path=base,
            project_name="incomplete-cel",
            pytest_runner=mock_runner,
        )

        report = engine.certify_sprint(save_reports=False)
        assert report.is_certified is False
        assert report.cel_result.is_complete is False
        assert len(report.cel_result.missing_pillars) > 0
        assert any("piliers gherkin" in r.lower() for r in report.blocking_reasons)


def test_certify_sprint_fails_on_missing_cel_file():
    """Rejet explicite si le fichier CEL est introuvable."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        mock_runner = MagicMock(return_value=PytestExecutionResult(
            all_passed=True, total_tests=5, passed_tests=5, failed_tests=0, duration_seconds=0.1
        ))

        engine = QaCertifierEngine(
            project_path=base,
            project_name="no-cel",
            pytest_runner=mock_runner,
        )

        report = engine.certify_sprint(save_reports=False)
        assert report.is_certified is False
        assert report.cel_result.cel_found is False
        assert any("introuvable" in r.lower() for r in report.blocking_reasons)


def test_format_qa_markdown_renders_all_sections():
    """Le formateur Markdown doit générer toutes les sections normatives."""
    report = QaCertificationReport(
        project_name="mLoop",
        certified_at="2026-09-19T12:00:00Z",
        is_certified=True,
        pytest_result=PytestExecutionResult(
            all_passed=True, total_tests=20, passed_tests=20, failed_tests=0, duration_seconds=2.0, coverage_percent=95.0
        ),
        ast_summary=AstAuditSummary(files_audited=10, total_violations=0, passed=True),
        cel_result=CelTriangulationResult(
            cel_found=True, ledger_path="memory/evidence/cel.json", total_blocks=4,
            covered_pillars=list(REQUIRED_GHERKIN_PILLARS), missing_pillars=[], is_complete=True
        ),
        blocking_reasons=[],
    )

    md = format_qa_markdown(report)
    assert "# 🛡️ Rapport de Certification QA Sprint" in md
    assert "SUCCÈS 100%" in md
    assert "ADR-0202 / ADR-0369" in md
    assert "4 Piliers Gherkin" in md
    assert "Autorisation Gate 4" in md


def test_handle_validate_sprint_cli_integration(monkeypatch):
    """Vérifie que la commande CLI handle_validate_sprint retourne 0 en cas de succès et 1 en cas d'échec."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        ev_dir = base / "memory" / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        (ev_dir / "EPIC-7_code_evidence_ledger.json").write_text(json.dumps(SAMPLE_CEL_COMPLETE), encoding="utf-8")

        # Mock certify_sprint pour retourner succès
        mock_report_pass = MagicMock(is_certified=True)
        monkeypatch.setattr(
            "src.pipelines.qa_certifier.QaCertifierEngine.certify_sprint",
            lambda self, *args, **kwargs: mock_report_pass,
        )

        args = argparse.Namespace(project="test", timeout=30.0)
        ret = handle_validate_sprint(args, state=MagicMock(), project_path=base)
        assert ret == 0

        # Mock certify_sprint pour retourner échec
        mock_report_fail = MagicMock(is_certified=False)
        monkeypatch.setattr(
            "src.pipelines.qa_certifier.QaCertifierEngine.certify_sprint",
            lambda self, *args, **kwargs: mock_report_fail,
        )

        ret_fail = handle_validate_sprint(args, state=MagicMock(), project_path=base)
        assert ret_fail == 1
