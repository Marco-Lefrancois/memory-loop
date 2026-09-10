# -*- coding: utf-8 -*-
"""
Fact-Check Certificate Generator (mLoop Core - ADR-0326).

Agrège les résultats de vérification NLI et produit un Certificat Fact-Check
avec calcul du Fact-Check Trust Index (0-100%) et synchronisation EvidencePack.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.engine.fact_check.nli_verifier import NLIVerificationResult, VerdictEnum
from src.utils.logger import get_logger

logger = get_logger("fact_check.certificate")


@dataclass
class FactCheckCertificate:
    """Certificat formel de conformité factuelle pour une User Story."""
    story_id: str
    project_name: str
    timestamp: str
    total_claims: int
    entailment_count: int
    contradiction_count: int
    unsupported_count: int
    trust_index: float  # 0.0 à 100.0%
    status: str         # "CERTIFIED", "REJECTED", "NEEDS_REVIEW"
    is_compliant: bool  # True si 0 contradiction et trust_index >= 60%
    results: List[NLIVerificationResult] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    admission_of_limits: str = ""  # Synthèse d'aveu des limites (ADR-0353)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "story_id": self.story_id,
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "total_claims": self.total_claims,
            "entailment_count": self.entailment_count,
            "contradiction_count": self.contradiction_count,
            "unsupported_count": self.unsupported_count,
            "trust_index": self.trust_index,
            "status": self.status,
            "is_compliant": self.is_compliant,
            "admission_of_limits": self.admission_of_limits,
            "contradictions": self.contradictions,
            "results": [r.to_dict() for r in self.results],
        }

    def generate_user_facing_summary(self) -> str:
        """Génère la vue synthétique en langage clair pour l'utilisateur (ADR-0353)."""
        lines = [
            f"Bilan Fact-Check pour {self.story_id} ({self.project_name}) :",
            f"• Statut : {self.status} (Indice de confiance : {self.trust_index}%)",
            f"• Affirmations validées : {self.entailment_count}/{self.total_claims}",
            f"• Contradictions : {self.contradiction_count}",
            f"• Affirmations non documentées : {self.unsupported_count}",
            "",
            self.admission_of_limits
        ]
        return "\n".join(lines)


class FactCheckCertificateGenerator:
    """Générateur et persistant de certificats Fact-Check."""

    @classmethod
    def generate_certificate(
        cls,
        story_id: str,
        project_name: str,
        results: List[NLIVerificationResult],
    ) -> FactCheckCertificate:
        """Calcule le certificat Fact-Check à partir de la liste des résultats NLI."""
        total = len(results)
        if total == 0:
            return FactCheckCertificate(
                story_id=story_id,
                project_name=project_name,
                timestamp=datetime.now().isoformat(),
                total_claims=0,
                entailment_count=0,
                contradiction_count=0,
                unsupported_count=0,
                trust_index=100.0,
                status="CERTIFIED",
                is_compliant=True,
                results=[],
                contradictions=[],
                admission_of_limits="✅ Aucune affirmation à auditer (Récit sans exigences détectées).",
            )

        entailments = [r for r in results if r.verdict == VerdictEnum.ENTAILMENT]
        contradictions = [r for r in results if r.verdict == VerdictEnum.CONTRADICTION]
        unsupported = [r for r in results if r.verdict == VerdictEnum.UNSUPPORTED]

        trust_index = round((len(entailments) / total) * 100.0, 1)

        if len(contradictions) > 0:
            status = "REJECTED"
            is_compliant = False
        elif trust_index >= 60.0:
            status = "CERTIFIED"
            is_compliant = True
        else:
            status = "NEEDS_REVIEW"
            is_compliant = False

        contradiction_details = [
            {
                "claim_id": c.claim_id,
                "statement": c.statement,
                "rationale": c.rationale,
                "proof_source": c.proof_source,
                "contradiction_detail": c.contradiction_detail,
            }
            for c in contradictions
        ]

        # Synthèse d'aveu des limites (ADR-0353 - Dual View & Admission of Limits)
        if len(contradictions) > 0:
            admission_of_limits = (
                f"🚨 CONTRADICTION BLOQUANTE : {len(contradictions)} exigence(s) contredisent formellement "
                f"le SSOT documentaire. Aucune progression sans résolution des conflits."
            )
        elif len(unsupported) > 0:
            unsupp_samples = [f"'{u.statement[:60]}...'" if len(u.statement) > 60 else f"'{u.statement}'" for u in unsupported[:2]]
            admission_of_limits = (
                f"⚠️ LIMITES DE PREUVE : {len(entailments)}/{total} critère(s) confirmés par le SSOT. "
                f"Cependant, {len(unsupported)} critère(s) demeurent sans preuve documentaire ({', '.join(unsupp_samples)}). "
                f"Validation humaine (HITL) formellement exigée avant mise en œuvre."
            )
        else:
            admission_of_limits = (
                f"✅ PREUVES COMPLÈTES : L'intégralité des {total} critère(s) et scénarios est rigoureusement "
                f"étayée par les règles d'affaires et décisions architecturales actives du SSOT."
            )

        return FactCheckCertificate(
            story_id=story_id,
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
            total_claims=total,
            entailment_count=len(entailments),
            contradiction_count=len(contradictions),
            unsupported_count=len(unsupported),
            trust_index=trust_index,
            status=status,
            is_compliant=is_compliant,
            results=results,
            contradictions=contradiction_details,
            admission_of_limits=admission_of_limits,
        )

    @classmethod
    def persist_to_evidence_pack(
        cls,
        cert: FactCheckCertificate,
        evidence_dir: Optional[Path] = None,
    ) -> Path:
        """Sauvegarde ou enrichit l'EvidencePack JSON du récit."""
        if evidence_dir is None:
            # Chercher dans Projects/<project>/memory/evidence ou memory/evidence
            proj_mem = Path("Projects") / cert.project_name / "memory" / "evidence"
            if proj_mem.parent.exists():
                evidence_dir = proj_mem
            else:
                evidence_dir = Path("memory/evidence")

        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_file = evidence_dir / f"{cert.story_id}_evidence.json"

        evidence_data: Dict[str, Any] = {}
        if evidence_file.exists():
            try:
                evidence_data = json.loads(evidence_file.read_text(encoding="utf-8"))
            except Exception:
                evidence_data = {}

        # Mise à jour de la section fact_check_certificate
        evidence_data["story_id"] = cert.story_id
        evidence_data["project_name"] = cert.project_name
        evidence_data["last_updated"] = cert.timestamp
        evidence_data["fact_check_certificate"] = cert.to_dict()

        evidence_file.write_text(json.dumps(evidence_data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Certificat Fact-Check sauvegardé dans {evidence_file}")
        return evidence_file
