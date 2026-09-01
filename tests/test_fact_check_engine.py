# -*- coding: utf-8 -*-
"""
Tests unitaires & TDD pour le Moteur Fact-Check 1.0 (Zero-Blindspot NLI Engine).
"""

import pytest
import tempfile
from pathlib import Path

from src.engine.fact_check.claim_extractor import ClaimExtractor, AtomicClaim
from src.engine.fact_check.nli_verifier import NLIVerifier, NLIVerificationResult, VerdictEnum
from src.engine.fact_check.certificate import FactCheckCertificateGenerator, FactCheckCertificate
from src.engine.fact_check import FactCheckEngine, verify_story_facts
from src.engine.fact_search.indexer import FactSearchIndexer


def test_claim_extractor_atomic_decomposition():
    """Vérifie que ClaimExtractor décompose les phrases complexes en assertions atomiques."""
    sample_markdown = """---
id: US-101
title: Gestion des Paniers Clients
---

# Gestion des Paniers Clients

## Critères d'acceptation
- Le panier expire après 15 minutes, et libère immédiatement l'inventaire réservé.
- Un email de rappel est envoyé ainsi que l'archivage de la commande.

## Scénarios de test

### Pilier 1 : Scénario Nominal
- Étant donné un panier actif
- Quand l'utilisateur reste inactif pendant 15 minutes
- Alors le panier est marqué expiré, et les articles sont remis en stock.

### Pilier 2 : Scénario d'Exception
- Étant donné un paiement par carte refusé
- Quand Stripe retourne une erreur 402
- Alors une notification rouge s'affiche afin de guider le client.
"""
    claims = ClaimExtractor.extract_claims_from_markdown(sample_markdown, story_id="US-101")
    assert len(claims) >= 6

    statements = [c.atomic_statement for c in claims]
    
    # Vérifier que les phrases composées ont été découpées
    assert any("Le panier expire après 15 minutes" in s for s in statements)
    assert any("libère immédiatement l'inventaire réservé" in s for s in statements)
    assert any("Un email de rappel est envoyé" in s for s in statements)
    assert any("le panier est marqué expiré" in s for s in statements)
    assert any("les articles sont remis en stock" in s for s in statements)


def test_nli_verifier_entailment_and_contradiction(tmp_path):
    """Vérifie la détection d'entailment (vrai) et de contradiction (faux) par le moteur NLI."""
    test_db = tmp_path / "fact_check_test.db"
    project_name = "TestProject_NLI"
    docs_dir = tmp_path / "Projects" / project_name / "docs"
    
    rm_dir = docs_dir / "02-business-rules"
    rm_dir.mkdir(parents=True, exist_ok=True)
    
    (rm_dir / "RM-042_Cart_Timeout.md").write_text(
        "# RM-042 : Expiration des Paniers\n\n"
        "## Spécification\n"
        "Tout panier d'achat expire automatiquement après 15 minutes d'inactivité de l'utilisateur.\n"
        "Les articles réservés sont remis en stock immédiatement.\n",
        encoding="utf-8"
    )

    # 1. Indexation du SSOT
    FactSearchIndexer.index_project_docs(
        project_name=project_name,
        docs_dir=docs_dir,
        db_path=test_db,
    )

    # 2. Test ENTAILMENT (Exigence exacte)
    valid_claim = AtomicClaim(
        claim_id="US-101_001",
        story_id="US-101",
        section_type="gherkin_nominal",
        step_keyword="WHEN",
        raw_text="Quand le panier expire après 15 minutes d'inactivité",
        atomic_statement="le panier expire après 15 minutes d'inactivité",
        line_number=10,
    )
    res_valid = NLIVerifier.verify_claim(valid_claim, project_name=project_name, db_path=test_db)
    assert res_valid.verdict == VerdictEnum.ENTAILMENT
    assert "RM-042" in res_valid.proof_source
    assert res_valid.confidence > 0.8

    # 3. Test CONTRADICTION (Exigence contradictoire : 45 minutes au lieu de 15 minutes)
    invalid_claim = AtomicClaim(
        claim_id="US-101_002",
        story_id="US-101",
        section_type="gherkin_nominal",
        step_keyword="WHEN",
        raw_text="Quand le panier expire après 45 minutes d'inactivité",
        atomic_statement="le panier expire après 45 minutes d'inactivité",
        line_number=11,
    )
    res_invalid = NLIVerifier.verify_claim(invalid_claim, project_name=project_name, db_path=test_db)
    assert res_invalid.verdict == VerdictEnum.CONTRADICTION
    assert "45" in res_invalid.rationale
    assert "15" in res_invalid.rationale
    assert res_invalid.contradiction_detail is not None


def test_fact_check_certificate_generation_and_evidence(tmp_path):
    """Vérifie la génération du certificat Fact-Check et sa persistance EvidencePack."""
    test_db = tmp_path / "fact_check_e2e.db"
    project_name = "TestProject_Cert"
    docs_dir = tmp_path / "Projects" / project_name / "docs"
    
    rm_dir = docs_dir / "02-business-rules"
    rm_dir.mkdir(parents=True, exist_ok=True)
    
    (rm_dir / "RM-088_Max_Items.md").write_text(
        "# RM-088 : Limite d'Articles par Panier\n\n"
        "## Règle de Gestion\n"
        "Un panier ne peut pas contenir plus de 50 articles au total.\n",
        encoding="utf-8"
    )

    FactSearchIndexer.index_project_docs(
        project_name=project_name,
        docs_dir=docs_dir,
        db_path=test_db,
    )

    story_file = tmp_path / "US-088.md"
    story_file.write_text(
        "---\nid: US-088\ntitle: Limite panier\n---\n\n"
        "# Limite panier\n\n"
        "## Scénarios de test\n\n"
        "### Pilier 1 : Scénario Nominal\n"
        "- Étant donné un panier contenant 50 articles\n"
        "- Quand l'utilisateur tente d'ajouter un 51ème article\n"
        "- Alors une erreur de dépassement s'affiche.\n",
        encoding="utf-8"
    )

    evidence_dir = tmp_path / "evidence"
    certificate = FactCheckEngine.check_story(
        story_path=story_file,
        project_name=project_name,
        persist_evidence=False,
        db_path=test_db,
    )

    # Persister dans le dossier temporaire
    evidence_file = FactCheckCertificateGenerator.persist_to_evidence_pack(certificate, evidence_dir=evidence_dir)

    assert certificate.total_claims >= 2
    assert certificate.trust_index > 50.0
    assert certificate.contradiction_count == 0
    assert evidence_file.exists()
    assert "fact_check_certificate" in evidence_file.read_text(encoding="utf-8")
