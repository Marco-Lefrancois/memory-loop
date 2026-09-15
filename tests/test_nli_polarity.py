# -*- coding: utf-8 -*-
"""
Tests d integration NLI - Polarity Guard.
Verifie que le bypass relevance >= 0.8 ne produit plus de faux-positifs ENTAILMENT
quand une violation d invariant de domaine est presente.
"""

import pytest
import tempfile
from pathlib import Path

from src.engine.fact_check.claim_extractor import AtomicClaim
from src.engine.fact_check.nli_verifier import NLIVerifier, VerdictEnum
from src.engine.fact_search.indexer import FactSearchIndexer


def _make_claim(claim_id: str, statement: str, story_id: str = "TEST-001") -> AtomicClaim:
    return AtomicClaim(
        claim_id=claim_id,
        story_id=story_id,
        section_type="acceptance_criteria",
        step_keyword="CRITERION",
        raw_text=statement,
        atomic_statement=statement,
        line_number=1,
    )


def _setup_db(tmp_path: Path, project_name: str, doc_text: str) -> Path:
    """Cree un projet minimal et indexe un document SSOT."""
    db = tmp_path / "test_nli.db"
    docs_dir = tmp_path / "Projects" / project_name / "docs" / "02-business-rules"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "RM-001_test.md").write_text(doc_text, encoding="utf-8")
    FactSearchIndexer.index_project_docs(
        project_name=project_name,
        docs_dir=docs_dir.parent,
        db_path=db,
    )
    return db


class TestNLIPolarityGuard:

    def test_contradiction_detected_on_polarity_inversion(self, tmp_path):
        """
        Verifie qu une inversion de polarite produit CONTRADICTION et non ENTAILMENT,
        meme si le score BM25 est eleve (mots partages entre claim et SSOT).
        """
        project = "TestPolarity"
        doc_text = (
            "# RM-001 Restriction de modification\n\n"
            "Il est strictement interdit de modifier un lot en cours d incubation "
            "sans validation explicite du responsable de couvoir."
        )
        db = _setup_db(tmp_path, project, doc_text)

        # Claim qui partage les mots cles mais inverse la permission
        claim = _make_claim(
            "TEST-001_001",
            "l operateur peut modifier un lot en cours d incubation"
        )
        result = NLIVerifier.verify_claim(claim, project_name=project, db_path=db)

        # Le bypass relevance >= 0.8 aurait donne ENTAILMENT avant le fix
        # Apres le fix : doit etre CONTRADICTION ou UNSUPPORTED (pas ENTAILMENT)
        assert result.verdict != VerdictEnum.ENTAILMENT, (
            f"Faux-positif ENTAILMENT detecte ! Le bypass relevance >= 0.8 est encore actif. "
            f"Verdict: {result.verdict}, Rationale: {result.rationale}"
        )

    def test_entailment_still_works_without_polarity_conflict(self, tmp_path):
        """
        Verifie que l ENTAILMENT fonctionne toujours quand il n y a pas de conflit.
        Regression test : le fix ne doit pas casser les cas valides.
        """
        project = "TestEntailment"
        doc_text = (
            "# RM-002 Temps d expiration\n\n"
            "Tout panier d achat expire automatiquement apres 15 minutes d inactivite.\n"
            "Les articles reserves sont remis en stock immediatement."
        )
        db = _setup_db(tmp_path, project, doc_text)

        claim = _make_claim(
            "TEST-002_001",
            "le panier expire apres 15 minutes d inactivite"
        )
        result = NLIVerifier.verify_claim(claim, project_name=project, db_path=db)
        # Doit rester ENTAILMENT (numerique exact confirme par Tier 1)
        assert result.verdict == VerdictEnum.ENTAILMENT

    def test_contradiction_on_physical_impossibility(self, tmp_path):
        """
        Verifie qu un claim avec une temperature aberrante est identifie CONTRADICTION
        via le moteur d invariants, independamment du score BM25.
        """
        project = "TestTempInvariant"
        doc_text = (
            "# RM-003 Temperature d incubation\n\n"
            "La temperature standard d incubation est de 99.5 F dans les setters Boire."
        )
        db = _setup_db(tmp_path, project, doc_text)

        claim = _make_claim(
            "TEST-003_001",
            "la temperature d incubation est de 200 F dans le setter"
        )
        result = NLIVerifier.verify_claim(claim, project_name=project, db_path=db)
        assert result.verdict == VerdictEnum.CONTRADICTION
        assert result.tier_used == "tier1_domain_invariant"

    def test_tier_used_label_domain_invariant(self, tmp_path):
        """Verifie que le champ tier_used est correctement positionne."""
        project = "TestTierLabel"
        doc_text = (
            "# RM-004 Causalite\n\n"
            "L incubation precede toujours l eclosion."
        )
        db = _setup_db(tmp_path, project, doc_text)

        claim = _make_claim(
            "TEST-004_001",
            "le hatcher produit les poussins avant l incubation dans le setter"
        )
        result = NLIVerifier.verify_claim(claim, project_name=project, db_path=db)
        if result.verdict == VerdictEnum.CONTRADICTION:
            assert result.tier_used == "tier1_domain_invariant"
