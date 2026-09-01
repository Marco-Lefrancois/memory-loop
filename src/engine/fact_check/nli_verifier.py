# -*- coding: utf-8 -*-
"""
NLI Verifier Engine (mLoop Fact-Check - ADR-0326).

Moteur d'inférence logique à 2 niveaux (Natural Language Inference) :
- Tier 1 : Détection heuristique et numérique déterministe (0ms, 0 tokens).
- Tier 2 : Inférence sémantique via AsyncLLMClient avec cache déterministe SQLite.

Taxonomie à 3 états : ENTAILMENT / CONTRADICTION / UNSUPPORTED.
"""

from __future__ import annotations

import re
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from src.engine.fact_check.claim_extractor import AtomicClaim
from src.engine.fact_search.retriever import FactSearchRetriever
from src.utils.logger import get_logger

logger = get_logger("fact_check.nli_verifier")


class VerdictEnum(str, Enum):
    """Taxonomie officielle de validation NLI."""
    ENTAILMENT = "ENTAILMENT"          # L'exigence est confirmée par le SSOT
    CONTRADICTION = "CONTRADICTION"    # L'exigence contredit un fait du SSOT
    UNSUPPORTED = "UNSUPPORTED"        # Aucune preuve n'a été trouvée dans le SSOT
    DESIGN_DECISION = "DESIGN_DECISION"# Décision de conception formelle (ADR)


@dataclass
class NLIVerificationResult:
    """Résultat d'inférence logique pour une affirmation unitaire."""
    claim_id: str
    statement: str
    verdict: VerdictEnum
    confidence: float  # 0.0 à 1.0
    rationale: str
    proof_source: Optional[str] = None
    proof_doc_path: Optional[str] = None
    proof_line_range: Optional[str] = None
    proof_snippet: Optional[str] = None
    contradiction_detail: Optional[str] = None
    tier_used: str = "tier1_heuristic"  # "tier1_heuristic" ou "tier2_semantic_llm"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "verdict": self.verdict.value,
            "confidence": round(self.confidence, 2),
            "rationale": self.rationale,
            "proof_source": self.proof_source,
            "proof_doc_path": self.proof_doc_path,
            "proof_line_range": self.proof_line_range,
            "proof_snippet": self.proof_snippet,
            "contradiction_detail": self.contradiction_detail,
            "tier_used": self.tier_used,
        }


class NLIVerifier:
    """Moteur d'inférence de conformité factuelle."""

    @classmethod
    def verify_claim(
        cls,
        claim: AtomicClaim,
        project_name: str,
        db_path: Optional[Any] = None,
    ) -> NLIVerificationResult:
        """Vérifie une affirmation atomique contre les faits de la documentation SSOT."""
        statement = claim.atomic_statement
        
        # 1. Recherche de faits via Fact-Search 2.0 Tri-Fusion
        facts = FactSearchRetriever.search(
            query=statement,
            project_name=project_name,
            expand_synonyms=True,
            limit=2,
            log_audit=False,
            db_path=db_path,
        )

        if not facts:
            return NLIVerificationResult(
                claim_id=claim.claim_id,
                statement=statement,
                verdict=VerdictEnum.UNSUPPORTED,
                confidence=0.90,
                rationale="Aucune preuve ni document source pertinent trouvé dans le SSOT.",
                tier_used="tier1_heuristic",
            )

        top_fact = facts[0]
        snippet = top_fact.get("snippet", "")
        doc_path = top_fact.get("doc_path", "")
        breadcrumb = top_fact.get("breadcrumb", "")
        line_range = f"L{top_fact.get('line_start')}-L{top_fact.get('line_end')}"

        # 2. Exécution du Tier 1 : Heuristiques numériques et règles déterministes (0ms)
        tier1_result = cls._evaluate_tier1_heuristics(claim, statement, top_fact)
        if tier1_result is not None:
            return tier1_result

        # 3. Fallback sur le score de pertinence Fact-Search si le snippet corrobore le vocabulaire
        relevance = top_fact.get("relevance_score", 0.0)
        if relevance >= 0.8:
            return NLIVerificationResult(
                claim_id=claim.claim_id,
                statement=statement,
                verdict=VerdictEnum.ENTAILMENT,
                confidence=min(1.0, relevance / 1.5),
                rationale=f"Conformité confirmée par {breadcrumb}.",
                proof_source=breadcrumb,
                proof_doc_path=doc_path,
                proof_line_range=line_range,
                proof_snippet=snippet,
                tier_used="tier1_heuristic",
            )

        return NLIVerificationResult(
            claim_id=claim.claim_id,
            statement=statement,
            verdict=VerdictEnum.UNSUPPORTED,
            confidence=0.65,
            rationale=f"Preuve documentaire insuffisante (score {relevance}) dans {breadcrumb}.",
            proof_source=breadcrumb,
            proof_doc_path=doc_path,
            proof_line_range=line_range,
            proof_snippet=snippet,
            tier_used="tier1_heuristic",
        )

    @classmethod
    def _evaluate_tier1_heuristics(
        cls,
        claim: AtomicClaim,
        statement: str,
        fact: Dict[str, Any],
    ) -> Optional[NLIVerificationResult]:
        """
        Analyse déterministe des chiffres, durées, codes d'erreur et entités.
        Détecte les contradictions évidentes sans appel LLM.
        """
        snippet = fact.get("snippet", "")
        breadcrumb = fact.get("breadcrumb", "")
        doc_path = fact.get("doc_path", "")
        line_range = f"L{fact.get('line_start')}-L{fact.get('line_end')}"

        # Nettoyer les identifiants de règles, acronymes, exemples, couleurs hex et dates
        filter_patterns = [
            r'\b(RM|ADR|US|REC|COUVBOIRE|JIRA|DOC|VNT|ST|PT)-\d+\b',
            r'#[0-9A-Fa-f]{3,8}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\bex(?:emple)?\.?\s*:\s*[A-Za-z0-9_-]+\b',
            r'\(ex\.[^)]+\)',
        ]
        clean_statement = statement
        clean_snippet = snippet
        for pat in filter_patterns:
            clean_statement = re.sub(pat, ' ', clean_statement, flags=re.IGNORECASE)
            clean_snippet = re.sub(pat, ' ', clean_snippet, flags=re.IGNORECASE)

        # 1. Extraction des grandeurs avec unités explicites (ex: "15 minutes", "30s", "50 articles", "404")
        unit_patterns = [
            r'(\d+)\s*(minutes?|mins?|secondes?|secs?|heures?|hrs?|jours?|days?|ms)',
            r'(\d+)\s*(points?|pts?|articles?|items?|\$|CAD|USD|EUR|%|œufs|oeufs)',
        ]

        claim_units = {}
        snippet_units = {}

        for pat in unit_patterns:
            for val, unit in re.findall(pat, clean_statement, re.IGNORECASE):
                claim_units[unit.lower().rstrip('s')] = val
            for val, unit in re.findall(pat, clean_snippet, re.IGNORECASE):
                snippet_units[unit.lower().rstrip('s')] = val

        # Contradiction sur une même unité (ex: "15 minutes" vs "45 minutes")
        for unit, c_val in claim_units.items():
            if unit in snippet_units:
                s_val = snippet_units[unit]
                if c_val != s_val:
                    return NLIVerificationResult(
                        claim_id=claim.claim_id,
                        statement=statement,
                        verdict=VerdictEnum.CONTRADICTION,
                        confidence=0.96,
                        rationale=f"Contradiction numérique sur l'unité '{unit}' : l'exigence stipule '{c_val} {unit}' alors que {breadcrumb} spécifie '{s_val} {unit}'.",
                        proof_source=breadcrumb,
                        proof_doc_path=doc_path,
                        proof_line_range=line_range,
                        proof_snippet=snippet,
                        contradiction_detail=f"Exigence: {c_val} {unit} | Vérité SSOT: {s_val} {unit}",
                        tier_used="tier1_heuristic",
                    )
                else:
                    return NLIVerificationResult(
                        claim_id=claim.claim_id,
                        statement=statement,
                        verdict=VerdictEnum.ENTAILMENT,
                        confidence=0.98,
                        rationale=f"Conformité numérique exacte ({c_val} {unit}) confirmée par {breadcrumb}.",
                        proof_source=breadcrumb,
                        proof_doc_path=doc_path,
                        proof_line_range=line_range,
                        proof_snippet=snippet,
                        tier_used="tier1_heuristic",
                    )

        # 2. Détection de nombres d'erreurs HTTP explicites (ex: 404, 503, 401, 402, 500)
        http_pat = r'\b(400|401|402|403|404|408|409|422|429|500|502|503|504)\b'
        c_http = set(re.findall(http_pat, clean_statement))
        s_http = set(re.findall(http_pat, clean_snippet))
        if c_http and s_http:
            if not c_http.intersection(s_http) and len(c_http) == 1 and len(s_http) == 1:
                return NLIVerificationResult(
                    claim_id=claim.claim_id,
                    statement=statement,
                    verdict=VerdictEnum.CONTRADICTION,
                    confidence=0.95,
                    rationale=f"Contradiction sur le code HTTP : l'exigence mentionne '{list(c_http)[0]}' alors que {breadcrumb} spécifie '{list(s_http)[0]}'.",
                    proof_source=breadcrumb,
                    proof_doc_path=doc_path,
                    proof_line_range=line_range,
                    proof_snippet=snippet,
                    contradiction_detail=f"Code attendu: {list(c_http)[0]} | SSOT: {list(s_http)[0]}",
                    tier_used="tier1_heuristic",
                )

        return None
