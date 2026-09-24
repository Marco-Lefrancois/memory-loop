"""
Tests MLOOP-181-BE : Intégration automatique des décisions et citations ancrées
dans l'EvidencePack via le harnais Phase 3 Build (CA-1 à CA-6).
"""
import json
import os
import subprocess

import pytest

from src.core.decision_recorder import (
    DecisionRecorder,
    CitationExtractionError,
    CONTRACT_TO_DEFINE,
)


@pytest.fixture
def project_dir(tmp_path):
    """Mini-projet mLoop avec memory/evidence/."""
    ev = tmp_path / "memory" / "evidence"
    ev.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def recorder(project_dir):
    return DecisionRecorder(project_path=project_dir)


@pytest.fixture
def evidence_path(project_dir):
    return project_dir / "memory" / "evidence" / "MLOOP-TEST_evidence.json"


def _write_pack(evidence_path):
    evidence_path.write_text(
        json.dumps({"story_id": "MLOOP-TEST", "implementation_decisions": []}),
        encoding="utf-8",
    )


# ─── CA-3 : Hook public record_decision + dédoublonnage hash ────────────────


def test_record_decision_nominal(recorder, evidence_path):
    """CA-3/CA-6 : décision horodatée UTC avec alternatives tracées."""
    _write_pack(evidence_path)
    dec = recorder.record_decision(
        story_id="MLOOP-TEST",
        evidence_path=evidence_path,
        category="architecture",
        rationale="Score Pareto 82.5 retenu (robustesse 90)",
        alternatives_considered=["candidat_A (rejeté: score 71)", "candidat_C (rejeté: score 65)"],
    )
    assert dec["category"] == "architecture"
    assert dec["decision_id"].startswith("DEC-")
    assert "T" in dec["timestamp"] and dec["timestamp"].endswith("+00:00")
    assert len(dec["alternatives_considered"]) == 2

    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert len(data["implementation_decisions"]) == 1
    assert data["implementation_decisions"][0]["rationale"].startswith("Score Pareto")


def test_record_decision_invalid_category(recorder, evidence_path):
    """CA-3 : catégorie hors liste fermée rejetée (fail-closed, ADR-0369)."""
    _write_pack(evidence_path)
    with pytest.raises(ValueError, match="liste fermée"):
        recorder.record_decision(
            story_id="MLOOP-TEST",
            evidence_path=evidence_path,
            category="magie_noire",
            rationale="x",
            alternatives_considered=[],
        )


def test_record_decision_missing_pack_creates_it(recorder, evidence_path):
    """Résilience : pack absent → créé à la volée, zéro crash."""
    dec = recorder.record_decision(
        story_id="MLOOP-TEST",
        evidence_path=evidence_path,
        category="testing",
        rationale="Cycle TDD complet red->green scellé",
        alternatives_considered=[],
    )
    assert dec["decision_id"].startswith("DEC-")
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert len(data["implementation_decisions"]) == 1


# ─── CA-1 : Capture tournoi ──────────────────────────────────────────────────


def test_record_tournament_decision(recorder, evidence_path):
    """CA-1 : arbitrage Pareto converti en décision architecture."""
    _write_pack(evidence_path)
    recorder.record_tournament_decision(
        evidence_path=evidence_path,
        story_id="MLOOP-TEST",
        winner_id="candidat_B",
        winner_pareto_score=82.5,
        losers=[("candidat_A", 71.0), ("candidat_C", 65.0)],
    )
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    decisions = data["implementation_decisions"]
    assert len(decisions) == 1
    assert decisions[0]["category"] == "architecture"
    assert "candidat_B" in decisions[0]["rationale"]
    assert decisions[0]["alternatives_considered"] == [
        "candidat_A (rejeté: score 71.0)",
        "candidat_C (rejeté: score 65.0)",
    ]


# ─── CA-2 : Capture TDD ──────────────────────────────────────────────────────


def test_record_tdd_cycle_decision(recorder, evidence_path):
    """CA-2 : au moins une décision testing par cycle complet red-green (+ dédoublonnage)."""
    _write_pack(evidence_path)
    kw = dict(
        evidence_path=evidence_path,
        story_id="MLOOP-TEST",
        test_file="tests/test_decision_recorder.py",
        red_exit_code=1,
        green_exit_code=0,
    )
    recorder.record_tdd_cycle_decision(**kw)
    recorder.record_tdd_cycle_decision(**kw)
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    decisions = data["implementation_decisions"]
    assert len(decisions) == 1
    assert decisions[0]["category"] == "testing"


# ─── CA-4 : Extraction citations depuis diff git ─────────────────────────────


@pytest.fixture
def git_repo(tmp_path):
    """Dépôt git jetable avec un fichier suivi puis modifié."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    f = repo / "src" / "module.py"
    f.write_text("ligne_uno = 1\nligne_dos = 2\n", encoding="utf-8")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    for args in (["init"], ["add", "."], ["commit", "-m", "init"]):
        subprocess.run(["git"] + args, cwd=repo, env=env, check=True,
                       capture_output=True, timeout=30)
    f.write_text("ligne_uno = 1\nligne_dos = 2\nligne_tres_modifiee = 42\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, env=env, check=True,
                   capture_output=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "modif"], cwd=repo, env=env, check=True,
                   capture_output=True, timeout=30)
    return repo


def test_extract_citations_from_diff(git_repo):
    """CA-4 : citation par fichier modifié, ancrage [start, end] réel."""
    rec = DecisionRecorder(project_path=git_repo)
    extracts = rec.extract_citations_from_diff(story_id="MLOOP-TEST", timeout=30, max_files=10)
    assert len(extracts) == 1
    ext = extracts[0]
    assert ext["source_file"].endswith("module.py")
    assert "ligne_tres_modifiee" in ext["quote"]
    start, end = ext["lines"]
    assert 1 <= start <= end


def test_extract_citations_deleted_file(git_repo):
    """Pilier 3 : fichier du diff supprimé → alerte source_deleted, build non crashé."""
    f = git_repo / "src" / "module.py"
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    f.unlink()
    subprocess.run(["git", "add", "-A"], cwd=git_repo, env=env, check=True,
                   capture_output=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "delete"], cwd=git_repo, env=env,
                   check=True, capture_output=True, timeout=30)
    rec = DecisionRecorder(project_path=git_repo)
    extracts, warnings = rec.extract_citations_from_diff(
        story_id="MLOOP-TEST", timeout=30, max_files=10, return_warnings=True
    )
    assert extracts == []
    assert any(w.get("alert") == "source_deleted" for w in warnings)


def test_extract_citations_timeout_raises(git_repo):
    """Pilier 3 : timeout dépassé → CitationExtractionError explicite (ADR-0369)."""
    rec = DecisionRecorder(project_path=git_repo)
    with pytest.raises(CitationExtractionError):
        rec.extract_citations_from_diff(story_id="MLOOP-TEST", timeout=0.001, max_files=10)


# ─── CA-5 : Contrat inconnu → [API à définir] + OQ ──────────────────────────


def test_record_unknown_contract(recorder, evidence_path, project_dir):
    """CA-5 : route inconnue → '[API de soumission à définir]', jamais d'URI inventée."""
    _write_pack(evidence_path)
    contract, oq = recorder.record_contract(
        story_id="MLOOP-TEST",
        evidence_path=evidence_path,
        project_path=project_dir,
        method="POST",
        hint="soumission du formulaire de couverture",
    )
    assert contract["path"] == CONTRACT_TO_DEFINE
    assert contract["status"] == "to_define"
    assert oq is not None and oq.name.startswith("OQ-")
    assert "[API de soumission à définir]" in oq.read_text(encoding="utf-8")


def test_record_known_contract(recorder, evidence_path, project_dir):
    """CA-5 : route connue → enregistrée telle quelle, statut defined."""
    _write_pack(evidence_path)
    contract, oq = recorder.record_contract(
        story_id="MLOOP-TEST",
        evidence_path=evidence_path,
        project_path=project_dir,
        method="GET",
        path="/api/v1/packs",
        source="src/pipelines/evidence_pack.py",
    )
    assert contract["path"] == "/api/v1/packs"
    assert contract["status"] == "defined"
    assert oq is None


# ─── Pilier 4 : Richesse visible (multiplicateur confiance, Déc. 5) ─────────


def test_compute_richness(recorder, evidence_path):
    """Déc. 5 : multiplicateur richesse calculé depuis le pack."""
    _write_pack(evidence_path)
    richness = recorder.compute_richness(evidence_path)
    assert richness["decisions"] == 0 and richness["citations"] == 0
    assert richness["richness"] == "EMPTY"
    recorder.record_decision(
        story_id="MLOOP-TEST", evidence_path=evidence_path, category="testing",
        rationale="cycle ok", alternatives_considered=[],
    )
    richness = recorder.compute_richness(evidence_path)
    assert richness["decisions"] == 1
    assert richness["richness"] in ("PARTIAL", "OK")


def test_record_decision_duplicate_skipped(recorder, evidence_path):
    """CA-3 : décision identique (hash category+rationale) non répétée."""
    _write_pack(evidence_path)
    kw = dict(
        story_id="MLOOP-TEST",
        evidence_path=evidence_path,
        category="architecture",
        rationale="Même rationale",
    )
    recorder.record_decision(alternatives_considered=[], **kw)
    recorder.record_decision(alternatives_considered=[], **kw)

    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert len(data["implementation_decisions"]) == 1
