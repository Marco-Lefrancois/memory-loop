"""
mLoop INVEST Evaluator & Quality Engine (ADR-0300, ADR-0301)
Évalue la conformité des récits utilisateurs aux critères INVEST et aux 4 Piliers Gherkin.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class InvestCriteriaScore:
    name: str
    passed: bool
    weight: float
    description: str
    details: Optional[str] = None


@dataclass
class InvestEvaluationResult:
    is_compliant: bool
    total_score: float  # Sur 100
    criteria: List[InvestCriteriaScore] = field(default_factory=list)
    has_nominal: bool = False
    has_exceptions: bool = False
    has_resilience: bool = False
    has_ux: bool = False
    code_leak_detected: bool = False
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "total_score": round(self.total_score, 1),
            "pillars": {
                "nominal": self.has_nominal,
                "exceptions": self.has_exceptions,
                "resilience": self.has_resilience,
                "ux": self.has_ux,
            },
            "code_leak_detected": self.code_leak_detected,
            "recommendations": self.recommendations,
        }


class InvestEvaluator:
    """Moteur d'évaluation déterministe de qualité INVEST et des 4 Piliers Gherkin."""

    CODE_LEAK_PATTERNS = [
        r'\b(?:def|class|function|async def|public void|import |from [a-zA-Z_]+ import)\b',
        r'```(?:python|javascript|typescript|csharp|rust|go)\b',
        r'\b[A-Za-z0-9_]+\.[a-zA-Z0-9_]+\([^\)]*\)',
    ]

    @classmethod
    def evaluate_story_content(cls, markdown_content: str) -> InvestEvaluationResult:
        """Audite le texte Markdown complet d'un récit utilisateur."""
        content = markdown_content or ""
        criteria = []
        recommendations = []

        # 1. Détection des 4 Piliers Gherkin (ADR-0301)
        has_nominal = bool(re.search(r'Pilier\s*1\s*[:\-]|Nominal|Scénario\s*Nominal', content, re.IGNORECASE))
        has_exceptions = bool(re.search(r'Pilier\s*2\s*[:\-]|Exceptions?|Scénario\s*d[\'e]Exception', content, re.IGNORECASE))
        has_resilience = bool(re.search(r'Pilier\s*3\s*[:\-]|Résilience|Resilience', content, re.IGNORECASE))
        has_ux = bool(re.search(r'Pilier\s*4\s*[:\-]|UX|Accessibilité|Affichage', content, re.IGNORECASE))

        # 2. Détection de fuite de code physique (Boundary Rule)
        code_leak = False
        for pattern in cls.CODE_LEAK_PATTERNS:
            if re.search(pattern, content):
                code_leak = True
                recommendations.append("Présence suspecte de code source physique ou de classes dans le récit (violation no-code).")
                break

        # 3. Évaluation INVEST
        # I - Indépendant (pas de référence à des implémentations couplées)
        criteria.append(InvestCriteriaScore(
            name="Independent",
            passed=not code_leak,
            weight=15.0,
            description="Le récit est autonome et déclaratif."
        ))

        # N - Négociable (présence de critères d'acceptation clairs)
        has_ca = bool(re.search(r'Critères\s*d[\'e]acceptation|Acceptance\s*Criteria|Scénarios', content, re.IGNORECASE))
        criteria.append(InvestCriteriaScore(
            name="Negotiable",
            passed=has_ca,
            weight=15.0,
            description="Présence de critères d'acceptation clairs."
        ))

        # V - Valuable (section En tant que / Valeur métier)
        has_value = bool(re.search(r'En tant que|Afin de|Valeur|Bénéfice', content, re.IGNORECASE))
        criteria.append(InvestCriteriaScore(
            name="Valuable",
            passed=has_value,
            weight=20.0,
            description="Valeur métier explicitement formulée."
        ))

        # E - Estimable (structure claire sans points d'interrogation critiques non résolus)
        has_unresolved = bool(re.search(r'TODO|TBD|FIXME|\?\?\?', content))
        criteria.append(InvestCriteriaScore(
            name="Estimable",
            passed=not has_unresolved,
            weight=15.0,
            description="Absence de blocages ou de TODOs non résolus."
        ))

        # S - Small (longueur mesurée, sans concaténation de multiples épiques)
        lines_count = len(content.splitlines())
        is_small = lines_count < 350
        criteria.append(InvestCriteriaScore(
            name="Small",
            passed=is_small,
            weight=15.0,
            description="Taille de récit découpée verticalement."
        ))

        # T - Testable (Gherkin avec Étant donné / Quand / Alors)
        has_gherkin = bool(re.search(r'Étant donné|Given|Quand|When|Alors|Then', content, re.IGNORECASE))
        criteria.append(InvestCriteriaScore(
            name="Testable",
            passed=has_gherkin and (has_nominal or has_exceptions),
            weight=20.0,
            description="Scénarios Gherkin vérifiables."
        ))

        # Calcul du score global
        total_score = sum(c.weight for c in criteria if c.passed)
        if code_leak:
            total_score = max(0.0, total_score - 20.0)

        if not (has_nominal and has_exceptions):
            recommendations.append("Il manque au moins un scénario nominal ou un scénario d'exception dans les 4 piliers Gherkin.")

        is_compliant = total_score >= 80.0 and not code_leak

        return InvestEvaluationResult(
            is_compliant=is_compliant,
            total_score=total_score,
            criteria=criteria,
            has_nominal=has_nominal,
            has_exceptions=has_exceptions,
            has_resilience=has_resilience,
            has_ux=has_ux,
            code_leak_detected=code_leak,
            recommendations=recommendations,
        )
