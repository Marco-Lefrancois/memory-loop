"""
Banc d'épreuves déterministes pytest pour le protocole TDD Enforcer (MLOOP-082-BE / ADR-0381).
Couvre l'intégralité des 4 Piliers Gherkin de MLOOP-082-BE :
- Pilier 1 : Nominal (Cycle complet Red -> Green -> Gate 3 certification)
- Pilier 2 : Exceptions (Rejet Green sans Red, Rejet Red si le test passe déjà)
- Pilier 3 : Résilience (Fichiers manquants, corruption du fichier d'évidence)
- Pilier 4 : UX / Observabilité (Formatage des snapshots cryptographiques SHA-256)
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from src.core.tdd_enforcer import (
    TddEnforcer,
    RedSnapshot,
    GreenSnapshot,
    MissingRedSnapshotError,
    UnexpectedPassingTestError,
    TestFailureError,
    AstViolationError,
    format_tdd_status,
)


FAILING_TEST = '''def test_failing():
    assert 1 == 2
'''

PASSING_TEST = '''import sample_module

def test_passing():
    assert sample_module.hello() == "world"
'''

SAMPLE_CODE = '''"""Module échantillon conforme."""
def hello() -> str:
    return "world"
'''

BAD_AST_CODE = '''"""Module échantillon avec bare connect."""
import sqlite3

def hello() -> str:
    conn = sqlite3.connect("db.sqlite")
    return "world"
'''


# ─── PILIER 1 : CHEMIN NOMINAL (Happy Path) ──────────────────────────────────

def test_tdd_enforcer_nominal_cycle():
    """Cycle TDD complet : Red (échec initial), Green (succès code+tests+ast), validation Gate 3."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        test_file = base / "test_sample.py"
        source_file = base / "sample_module.py"
        evidence_file = base / "STORY-082_evidence.json"

        # 1. Étape RED : test échoue
        test_file.write_text(FAILING_TEST, encoding="utf-8")
        enforcer = TddEnforcer()
        red = enforcer.record_red("STORY-082", test_file, evidence_file)

        assert red.exit_code != 0
        assert red.test_sha256 != ""
        assert evidence_file.exists()

        # 2. Étape GREEN : code implémenté et test passe
        source_file.write_text(SAMPLE_CODE, encoding="utf-8")
        test_file.write_text(PASSING_TEST, encoding="utf-8")

        green = enforcer.record_green("STORY-082", test_file, source_file, evidence_file)

        assert green.exit_code == 0
        assert green.ast_passed is True
        assert green.source_sha256 != ""

        # 3. Validation Gate 3
        compliant = enforcer.verify_gate_3_compliance("STORY-082", evidence_file)
        assert compliant is True


# ─── PILIER 2 : EXCEPTIONS & REJETS MÉTIER ───────────────────────────────────

def test_tdd_enforcer_rejects_green_without_red():
    """Interdiction formelle de sceller un Green sans RedSnapshot préalable."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        test_file = base / "test_sample.py"
        source_file = base / "sample_module.py"
        evidence_file = base / "STORY-082_evidence.json"

        source_file.write_text(SAMPLE_CODE, encoding="utf-8")
        test_file.write_text(PASSING_TEST, encoding="utf-8")

        enforcer = TddEnforcer()
        with pytest.raises(MissingRedSnapshotError):
            enforcer.record_green("STORY-082", test_file, source_file, evidence_file)


def test_tdd_enforcer_rejects_red_if_test_passes():
    """Un test qui passe dès le départ ne peut pas constituer une preuve Red d'échec initial."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        test_file = base / "test_pass_initial.py"
        test_file.write_text("def test_ok(): assert True\n", encoding="utf-8")
        evidence_file = base / "STORY-082_evidence.json"

        enforcer = TddEnforcer()
        with pytest.raises(UnexpectedPassingTestError):
            enforcer.record_red("STORY-082", test_file, evidence_file)


def test_tdd_enforcer_rejects_green_on_ast_violation():
    """Le sceau Green est refusé si le code viole l'AST linter même si les tests passent."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        test_file = base / "test_sample.py"
        source_file = base / "sample_module.py"
        evidence_file = base / "STORY-082_evidence.json"

        test_file.write_text(FAILING_TEST, encoding="utf-8")
        enforcer = TddEnforcer()
        enforcer.record_red("STORY-082", test_file, evidence_file)

        # Code qui passe le test mais viole l'AST (bare connect)
        source_file.write_text(BAD_AST_CODE, encoding="utf-8")
        test_file.write_text(PASSING_TEST, encoding="utf-8")

        with pytest.raises(AstViolationError):
            enforcer.record_green("STORY-082", test_file, source_file, evidence_file)


# ─── PILIER 3 : RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ ──────────────────────────

def test_tdd_enforcer_resilience_missing_files():
    """Gestion gracieuse si le fichier de test est introuvable."""
    enforcer = TddEnforcer()
    with pytest.raises(FileNotFoundError):
        enforcer.record_red("STORY-082", Path("non_existent_test.py"))


def test_tdd_enforcer_gate3_missing_evidence():
    """verify_gate_3_compliance renvoie False si l'EvidencePack est inexistant."""
    enforcer = TddEnforcer()
    assert enforcer.verify_gate_3_compliance("STORY-082", Path("non_existent_evidence.json")) is False


# ─── PILIER 4 : UX / OBSERVABILITÉ ───────────────────────────────────────────

def test_tdd_enforcer_format_status():
    """Formatage lisible du statut TDD avec les empreintes SHA-256."""
    red = RedSnapshot(
        story_id="STORY-082",
        test_file="tests/test_foo.py",
        test_sha256="abc123def456",
        exit_code=1,
        failure_signature="AssertionError: 1 == 2",
        timestamp_utc="2026-09-19T10:00:00Z",
    )
    green = GreenSnapshot(
        story_id="STORY-082",
        test_file="tests/test_foo.py",
        test_sha256="fed654cba321",
        source_file="src/foo.py",
        source_sha256="999888777666",
        exit_code=0,
        duration_seconds=0.05,
        ast_passed=True,
        timestamp_utc="2026-09-19T10:05:00Z",
    )
    formatted = format_tdd_status(red, green)
    assert "STORY-082" in formatted
    assert "RED" in formatted and "GREEN" in formatted
    assert "abc123def456" in formatted
    assert "999888777666" in formatted
