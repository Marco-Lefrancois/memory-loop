"""
Banc d'épreuves déterministes pytest pour le Moteur de Tournoi Multi-Draft (MLOOP-081-BE / ADR-0381).
Couvre l'intégralité des 4 Piliers Gherkin de MLOOP-081-BE :
- Pilier 1 : Nominal (2 candidats valides, arbitrage Pareto, promotion Golden Master)
- Pilier 2 : Exceptions (Disqualification d'un candidat défaillant aux tests ou à l'AST)
- Pilier 3 : Résilience (Aucun candidat qualifié -> NoQualifiedCandidateError, cible préservée)
- Pilier 4 : UX / Observabilité (Matrice comparative Pareto et rapport lisible)
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from src.pipelines.code_tournament import (
    CodeTournamentEngine,
    CandidateResult,
    TournamentReport,
    NoQualifiedCandidateError,
    DraftFolderNotFoundError,
    format_tournament_report,
)


# ─── FIXTURES & CANDIDATS DE TEST ────────────────────────────────────────────

CANDIDATE_A_MINIMAL = '''"""Candidat A : Minimaliste standard library."""
def compute_sum(a: int, b: int) -> int:
    return a + b

def compute_product(a: int, b: int) -> int:
    return a * b
'''

CANDIDATE_B_VERBOSE = '''"""Candidat B : Plus verbeux et complexe."""
def compute_sum(a: int, b: int) -> int:
    if a < 0 and b < 0:
        return a + b
    elif a < 0:
        return a + b
    elif b < 0:
        return a + b
    else:
        total = 0
        for val in [a, b]:
            total += val
        return total

def compute_product(a: int, b: int) -> int:
    return a * b
'''

CANDIDATE_C_DEFECTIVE = '''"""Candidat C : Viole l'AST (bare connect)."""
import sqlite3

def compute_sum(a: int, b: int) -> int:
    conn = sqlite3.connect("test.db")
    return a + b
'''

TEST_SUITE_CODE = '''"""Banc de test unitaire pour les candidats."""
import pytest

def test_math_operations():
    # Import dynamique du module cible sous test
    import target_module
    assert target_module.compute_sum(2, 3) == 5
    assert target_module.compute_product(4, 5) == 20
'''


# ─── PILIER 1 : CHEMIN NOMINAL (Happy Path) ──────────────────────────────────

def test_tournament_nominal_two_valid_candidates():
    """Deux candidats valides : le plus sobre/optimal (Candidat A) l'emporte et est promu."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        drafts_dir = Path(tmp_dir) / "drafts"
        drafts_dir.mkdir(parents=True)
        target_path = Path(tmp_dir) / "src" / "target_module.py"
        test_file = Path(tmp_dir) / "tests" / "test_target.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(TEST_SUITE_CODE, encoding="utf-8")

        # Écrire les 2 candidats
        (drafts_dir / "candidate_A_minimal.py").write_text(CANDIDATE_A_MINIMAL, encoding="utf-8")
        (drafts_dir / "candidate_B_verbose.py").write_text(CANDIDATE_B_VERBOSE, encoding="utf-8")

        engine = CodeTournamentEngine(
            story_id="STORY-TEST-01",
            drafts_dir=drafts_dir,
            target_path=target_path,
            test_file=test_file,
        )

        report = engine.run_tournament()

        assert report.promoted is True
        assert report.winner_id is not None
        assert "candidate_A" in report.winner_id
        assert target_path.exists()
        assert "Candidat A : Minimaliste" in target_path.read_text(encoding="utf-8")
        assert len(report.candidates) == 2
        assert all(c.disqualified is False for c in report.candidates)
        # Candidat A a une complexité moindre et moins de lignes, son score Pareto est plus haut
        cand_a = next(c for c in report.candidates if "candidate_A" in c.candidate_id)
        cand_b = next(c for c in report.candidates if "candidate_B" in c.candidate_id)
        assert cand_a.pareto_score > cand_b.pareto_score


# ─── PILIER 2 : EXCEPTIONS & REJETS MÉTIER ───────────────────────────────────

def test_tournament_disqualifies_ast_violator():
    """Un candidat violant les règles AST est disqualifié sans calcul de score."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        drafts_dir = Path(tmp_dir) / "drafts"
        drafts_dir.mkdir(parents=True)
        target_path = Path(tmp_dir) / "src" / "target_module.py"
        test_file = Path(tmp_dir) / "tests" / "test_target.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(TEST_SUITE_CODE, encoding="utf-8")

        (drafts_dir / "candidate_A_minimal.py").write_text(CANDIDATE_A_MINIMAL, encoding="utf-8")
        (drafts_dir / "candidate_C_bad.py").write_text(CANDIDATE_C_DEFECTIVE, encoding="utf-8")

        engine = CodeTournamentEngine(
            story_id="STORY-TEST-02",
            drafts_dir=drafts_dir,
            target_path=target_path,
            test_file=test_file,
        )

        report = engine.run_tournament()

        assert report.promoted is True
        assert "candidate_A" in report.winner_id
        cand_c = next(c for c in report.candidates if "candidate_C" in c.candidate_id)
        assert cand_c.disqualified is True
        assert "AST" in cand_c.disqualification_reason


# ─── PILIER 3 : RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ ──────────────────────────

def test_tournament_resilience_no_qualified_candidates():
    """Si tous les candidats sont disqualifiés, NoQualifiedCandidateError est levée."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        drafts_dir = Path(tmp_dir) / "drafts"
        drafts_dir.mkdir(parents=True)
        target_path = Path(tmp_dir) / "src" / "target_module.py"
        test_file = Path(tmp_dir) / "tests" / "test_target.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(TEST_SUITE_CODE, encoding="utf-8")

        (drafts_dir / "candidate_bad1.py").write_text(CANDIDATE_C_DEFECTIVE, encoding="utf-8")

        engine = CodeTournamentEngine(
            story_id="STORY-TEST-03",
            drafts_dir=drafts_dir,
            target_path=target_path,
            test_file=test_file,
        )

        with pytest.raises(NoQualifiedCandidateError):
            engine.run_tournament()

        assert not target_path.exists()


def test_tournament_resilience_missing_draft_dir():
    """Un dossier de drafts introuvable lève DraftFolderNotFoundError."""
    engine = CodeTournamentEngine(
        story_id="STORY-TEST-04",
        drafts_dir=Path("non_existent_drafts_dir_xyz"),
        target_path=Path("target.py"),
        test_file=Path("test.py"),
    )
    with pytest.raises(DraftFolderNotFoundError):
        engine.run_tournament()


# ─── PILIER 4 : UX / OBSERVABILITÉ ───────────────────────────────────────────

def test_tournament_format_report():
    """Le rapport formaté met en valeur le gagnant et les scores."""
    report = TournamentReport(
        story_id="STORY-081",
        winner_id="candidate_A_minimal.py",
        winner_path=Path("drafts/candidate_A_minimal.py"),
        target_path=Path("src/module.py"),
        promoted=True,
        candidates=[
            CandidateResult(
                candidate_id="candidate_A_minimal.py",
                file_path=Path("drafts/candidate_A_minimal.py"),
                pytest_passed=True,
                ast_passed=True,
                disqualified=False,
                disqualification_reason=None,
                robustness_score=95.0,
                simplicity_score=98.0,
                performance_score=99.0,
                pareto_score=97.05,
                execution_duration_ms=12.5,
            ),
            CandidateResult(
                candidate_id="candidate_B_verbose.py",
                file_path=Path("drafts/candidate_B_verbose.py"),
                pytest_passed=True,
                ast_passed=True,
                disqualified=False,
                disqualification_reason=None,
                robustness_score=80.0,
                simplicity_score=75.0,
                performance_score=90.0,
                pareto_score=80.75,
                execution_duration_ms=14.0,
            ),
        ],
    )
    formatted = format_tournament_report(report)
    assert "STORY-081" in formatted
    assert "candidate_A_minimal.py" in formatted
    assert "97.05" in formatted
    assert "VAINQUEUR" in formatted or "PROMU" in formatted
