"""
Banc d'épreuves déterministes pytest pour le linter statique AST mLoop (ADR-0381 / MLOOP-080-BE).
Couvre l'intégralité des 4 Piliers Gherkin de MLOOP-080-BE :
- Pilier 1 : Nominal (Happy path, 0 violation, performance < 50ms)
- Pilier 2 : Exceptions (Détection unitaire des 5 règles RULE-AST-01 à 05)
- Pilier 3 : Résilience (Fichier inexistant, syntaxe invalide)
- Pilier 4 : UX / Observabilité (Formatage du rapport et métadonnées)
"""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from src.core.ast_checker import (
    AstChecker,
    AstAuditReport,
    AstViolation,
    check_file_ast,
    format_audit_report,
)


# ─── PILIER 1 : CHEMIN NOMINAL (Happy Path) ──────────────────────────────────

def test_ast_checker_nominal_clean_file():
    """Un fichier parfaitement conforme passe l'audit sans aucune violation en moins de 50ms."""
    clean_code = '''"""Module parfait."""
import sqlite3
import subprocess
import warnings
import logging

logger = logging.getLogger(__name__)

def execute_safe_query(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")

def run_safe_process() -> None:
    res = subprocess.run(["echo", "ok"], check=True, timeout=5)

def safe_exception_handler() -> None:
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.debug("Division par zéro interceptée", exc_info=True)

def safe_deprecation() -> None:
    warnings.warn("Ancienne API", DeprecationWarning, stacklevel=2)
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(clean_code)
        tmp_path = Path(tmp.name)

    try:
        t0 = time.perf_counter()
        report: AstAuditReport = check_file_ast(tmp_path)
        duration_ms = (time.perf_counter() - t0) * 1000

        assert report.passed is True
        assert len(report.violations) == 0
        assert duration_ms < 50.0, f"Le linter a pris {duration_ms:.2f}ms (> 50ms)"
        assert report.line_count == len(clean_code.splitlines())
        assert report.file_size_bytes > 0
    finally:
        tmp_path.unlink(missing_ok=True)


# ─── PILIER 2 : EXCEPTIONS & REJETS MÉTIER (5 Règles AST) ────────────────────

def test_ast_checker_rule_01_max_lines():
    """RULE-AST-01 : Rejet si le fichier dépasse 300 lignes physiques (ADR-0202)."""
    long_code = "\n".join([f"# Ligne {i}" for i in range(305)])
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(long_code)
        tmp_path = Path(tmp.name)

    try:
        report = check_file_ast(tmp_path)
        assert report.passed is False
        rule_ids = [v.rule_id for v in report.violations]
        assert "RULE-AST-01" in rule_ids
        v = next(v for v in report.violations if v.rule_id == "RULE-AST-01")
        assert "305 lignes" in v.message or "300" in v.message
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ast_checker_rule_02_bare_resource():
    """RULE-AST-02 : Rejet si sqlite3.connect, open ou httpx.Client n'est pas dans un with."""
    code_with_bare_resource = '''import sqlite3

def leak():
    conn = sqlite3.connect("test.db")
    return conn
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_with_bare_resource)
        tmp_path = Path(tmp.name)

    try:
        report = check_file_ast(tmp_path)
        assert report.passed is False
        rule_ids = [v.rule_id for v in report.violations]
        assert "RULE-AST-02" in rule_ids
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ast_checker_rule_03_missing_timeout():
    """RULE-AST-03 : Rejet si subprocess.run ou subprocess.Popen n'a pas de timeout=..."""
    code_without_timeout = '''import subprocess

def run_proc():
    subprocess.run(["ls", "-la"])
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_without_timeout)
        tmp_path = Path(tmp.name)

    try:
        report = check_file_ast(tmp_path)
        assert report.passed is False
        rule_ids = [v.rule_id for v in report.violations]
        assert "RULE-AST-03" in rule_ids
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ast_checker_rule_04_silent_except_pass():
    """RULE-AST-04 : Rejet si except: pass sans journalisation (ADR-0369 Standard 4)."""
    code_silent_except = '''def swallow():
    try:
        val = 1 / 0
    except ZeroDivisionError:
        pass
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_silent_except)
        tmp_path = Path(tmp.name)

    try:
        report = check_file_ast(tmp_path)
        assert report.passed is False
        rule_ids = [v.rule_id for v in report.violations]
        assert "RULE-AST-04" in rule_ids
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ast_checker_rule_05_missing_stacklevel_2():
    """RULE-AST-05 : Rejet si warnings.warn n'inclut pas stacklevel=2."""
    code_warning_no_stacklevel = '''import warnings

def deprecated():
    warnings.warn("Old method")
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_warning_no_stacklevel)
        tmp_path = Path(tmp.name)

    try:
        report = check_file_ast(tmp_path)
        assert report.passed is False
        rule_ids = [v.rule_id for v in report.violations]
        assert "RULE-AST-05" in rule_ids
    finally:
        tmp_path.unlink(missing_ok=True)


# ─── PILIER 3 : RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ ──────────────────────────

def test_ast_checker_resilience_missing_file():
    """Un fichier introuvable renvoie une exception ou un rapport d'échec sans crasher."""
    report = check_file_ast(Path("non_existent_file_xyz123.py"))
    assert report.passed is False
    assert len(report.violations) == 1
    assert "introuvable" in report.violations[0].message.lower() or "not found" in report.violations[0].message.lower()


def test_ast_checker_resilience_syntax_error():
    """Un fichier avec une syntaxe invalide retourne un rapport d'échec avec RULE-AST-SYNTAX."""
    corrupted_code = "def syntax_error(:\n    pass\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(corrupted_code)
        tmp_path = Path(tmp.name)

    try:
        report = check_file_ast(tmp_path)
        assert report.passed is False
        assert any(v.rule_id == "RULE-AST-SYNTAX" for v in report.violations)
    finally:
        tmp_path.unlink(missing_ok=True)


# ─── PILIER 4 : UX / OBSERVABILITÉ ───────────────────────────────────────────

def test_ast_checker_format_report():
    """Le rapport formaté contient les informations nécessaires de lisibilité."""
    report = AstAuditReport(
        file_path=Path("src/test_mod.py"),
        passed=False,
        line_count=42,
        file_size_bytes=1024,
        violations=[
            AstViolation(
                rule_id="RULE-AST-03",
                line_number=12,
                message="Timeout manquant sur subprocess.run",
                corrective_action="Ajouter timeout=5"
            )
        ],
        duration_ms=1.23,
    )
    formatted = format_audit_report(report)
    assert "src/test_mod.py" in formatted
    assert "RULE-AST-03" in formatted
    assert "L12" in formatted or "12" in formatted
    assert "Timeout manquant" in formatted
    assert "Ajouter timeout=5" in formatted
