"""
Tests unitaires pour le garde-fou Phase 4 (Vibe-Check) — MLOOP-123-BE.
Vérifie que le WARNING qa_certification_report.json est émis en Phase 4 VALIDATE.
"""

import shutil
from pathlib import Path

import pytest

from src.pipelines.vibe_check import run_vibe_check


@pytest.fixture
def temp_project_dir():
    """Crée un répertoire temporaire simulant un projet sous Projects/<nom>."""
    proj_dir = Path("Projects") / "TestPhase4VC"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "docs" / "00-ingested").mkdir(parents=True, exist_ok=True)
    (proj_dir / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj_dir / "memory" / "evidence").mkdir(parents=True, exist_ok=True)
    # Créer un sprint_backlog minimal pour éviter le FAIL SSOT en mode RUN
    backlog_file = proj_dir / "backlog" / "sprint_backlog.md"
    backlog_file.write_text(
        "# Sprint Backlog\n\n| ID | Titre | Statut |\n| :--- | :--- | :--- |\n",
        encoding="utf-8",
    )
    yield proj_dir
    if proj_dir.exists():
        shutil.rmtree(proj_dir, ignore_errors=True)


def test_phase4_warning_when_qa_report_absent(temp_project_dir):
    """En Phase 4 VALIDATE sans qa_certification_report.json, le check doit émettre un WARNING."""
    proj_name = "TestPhase4VC"
    res = run_vibe_check(proj_name, stage="validate")

    qa_check = next(c for c in res["checks"] if "Certification QA Sprint" in c["check"])
    assert qa_check["status"] == "WARNING"
    assert "qa_certification_report.json absent" in qa_check["check"]
    assert "validate-sprint" in qa_check["check"]


def test_phase4_pass_when_qa_report_present(temp_project_dir):
    """En Phase 4 VALIDATE avec qa_certification_report.json, le check doit émettre PASS."""
    qa_file = temp_project_dir / "memory" / "evidence" / "qa_certification_report.json"
    qa_file.write_text("{}", encoding="utf-8")

    proj_name = "TestPhase4VC"
    res = run_vibe_check(proj_name, stage="validate")

    qa_check = next(c for c in res["checks"] if "Certification QA Sprint" in c["check"])
    assert qa_check["status"] == "PASS"


def test_non_phase4_check_skipped(temp_project_dir):
    """Hors Phase 4, le check Certification QA ne doit pas émettre de WARNING."""
    proj_name = "TestPhase4VC"
    res = run_vibe_check(proj_name, stage="build")

    qa_check = next(c for c in res["checks"] if "Certification QA Sprint" in c["check"])
    assert qa_check["status"] == "PASS"


def test_warning_does_not_block_session(temp_project_dir):
    """Le WARNING Phase 4 ne doit pas faire échouer le Vibe-Check (mode passif)."""
    proj_name = "TestPhase4VC"
    res = run_vibe_check(proj_name, stage="validate")

    qa_check = next(c for c in res["checks"] if "Certification QA Sprint" in c["check"])
    assert qa_check["status"] == "WARNING"

    # Le WARNING ne doit pas provoquer de FAIL dans les checks globaux
    failed_checks = [c for c in res["checks"] if c["status"] == "FAIL"]
    assert not any("Certification QA" in c["check"] for c in failed_checks)
