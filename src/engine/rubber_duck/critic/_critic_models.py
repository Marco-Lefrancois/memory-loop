"""
_critic_models.py — Modèles de données du moteur Avocat du Diable (MLOOP-172-BE).

Définit DevilAdvocateCritique, le rapport d'audit complet produit
par DevilAdvocateCritic.evaluate_story().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.engine.rubber_duck.coherence import CoherenceIssue
from src.engine.rubber_duck.remediator import RemediationPatch


@dataclass
class DevilAdvocateCritique:
    """Rapport d'audit complet de l'Avocat du Diable."""

    story_id: str
    project_name: str
    timestamp: str
    status: str  # "APPROVED", "ACTION_REQUIRED", "REJECTED"
    business_discernment_score: float  # 0-100
    ecosystem_coherence_score: float  # 0-100
    technical_rigor_score: float  # 0-100
    overall_trust_score: float  # 0-100
    critical_flaws: List[str] = field(default_factory=list)
    silent_failures: List[str] = field(default_factory=list)
    coherence_issues: List[CoherenceIssue] = field(default_factory=list)
    remediation_patches: List[RemediationPatch] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "story_id": self.story_id,
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "status": self.status,
            "scores": {
                "business_discernment": self.business_discernment_score,
                "ecosystem_coherence": self.ecosystem_coherence_score,
                "technical_rigor": self.technical_rigor_score,
                "overall_trust": self.overall_trust_score,
            },
            "critical_flaws": self.critical_flaws,
            "silent_failures": self.silent_failures,
            "coherence_issues": [c.to_dict() for c in self.coherence_issues],
            "remediation_patches": [p.to_dict() for p in self.remediation_patches],
            "recommendations": self.recommendations,
        }
