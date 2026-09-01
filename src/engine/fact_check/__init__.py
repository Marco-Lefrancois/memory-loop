# -*- coding: utf-8 -*-
"""
Fact-Check 1.0 Engine (mLoop Core - NLI Verification Architecture).

Expose les interfaces publiques d'extraction d'assertions,
d'inférence logique NLI et de certification EvidencePack.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any

from src.engine.fact_check.claim_extractor import ClaimExtractor, AtomicClaim
from src.engine.fact_check.nli_verifier import NLIVerifier, NLIVerificationResult, VerdictEnum
from src.engine.fact_check.certificate import FactCheckCertificate, FactCheckCertificateGenerator


class FactCheckEngine:
    """Moteur canonique d'audit Fact-Check pour les User Stories."""

    @classmethod
    def check_story(
        cls,
        story_path: str | Path,
        project_name: str,
        persist_evidence: bool = True,
        db_path: Optional[Any] = None,
    ) -> FactCheckCertificate:
        """
        Exécute le pipeline Fact-Check complet sur une User Story :
        1. Extraction des affirmations atomiques via ClaimExtractor.
        2. Inférence logique NLI pour chaque affirmation via NLIVerifier.
        3. Génération du certificat Fact-Check et persistance EvidencePack.
        """
        path_obj = Path(story_path)
        claims = ClaimExtractor.extract_claims_from_story_file(path_obj)
        story_id = ClaimExtractor._extract_story_id(
            path_obj.read_text(encoding="utf-8", errors="ignore") if path_obj.exists() else "",
            path_obj.stem
        )

        results: List[NLIVerificationResult] = []
        for claim in claims:
            res = NLIVerifier.verify_claim(claim, project_name=project_name, db_path=db_path)
            results.append(res)

        certificate = FactCheckCertificateGenerator.generate_certificate(
            story_id=story_id,
            project_name=project_name,
            results=results,
        )

        if persist_evidence:
            FactCheckCertificateGenerator.persist_to_evidence_pack(certificate)

        return certificate


def verify_story_facts(
    story_path: str | Path,
    project_name: str,
    persist_evidence: bool = True,
    db_path: Optional[Any] = None,
) -> FactCheckCertificate:
    """Interface canonique de Fact-Checking pour une story."""
    return FactCheckEngine.check_story(
        story_path=story_path,
        project_name=project_name,
        persist_evidence=persist_evidence,
        db_path=db_path,
    )


__all__ = [
    "FactCheckEngine",
    "verify_story_facts",
    "ClaimExtractor",
    "AtomicClaim",
    "NLIVerifier",
    "NLIVerificationResult",
    "VerdictEnum",
    "FactCheckCertificate",
    "FactCheckCertificateGenerator",
]
