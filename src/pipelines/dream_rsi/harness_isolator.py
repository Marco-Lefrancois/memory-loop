"""
src/pipelines/dream_rsi/harness_isolator.py — Isolation Modulaire du Harnais (ADR-0372).

Isole la performance et les défaillances du harnais (mémoire, outillage, portes,
prompt) indépendamment des poids du LLM sous-jacent.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class HarnessFailureCategory(str, Enum):
    """Taxonomie d'isolation des défaillances du harnais selon Dream RSI."""
    MEMORY = "Memory"
    TOOLING = "Tooling"
    GATE = "Gate"
    PROMPT = "Prompt"


@dataclass
class HarnessDiagnosis:
    """Diagnostic quantifié de l'isolation du harnais."""
    total_failures: int
    distribution: Dict[str, float] = field(default_factory=dict)
    primary_bottleneck: str = HarnessFailureCategory.GATE.value
    recommendations: List[str] = field(default_factory=list)
    isolated_harness_score: int = 80


class ModularHarnessIsolator:
    """
    Isolateur modulaire de performance et de goulots d'étranglement du harnais.
    Permet d'optimiser le harnais d'agent sans ré-entraînement de modèle.
    """

    KEYWORD_MAPPING = {
        HarnessFailureCategory.MEMORY: [
            "context", "token", "history", "health", "overflow", "hygiene",
            "memory", "recall", "compaction", "stale"
        ],
        HarnessFailureCategory.TOOLING: [
            "tool", "syntax", "timeout", "exit code", "exception", "attributeerror",
            "typeerror", "connection", "missing argument", "ioerror"
        ],
        HarnessFailureCategory.GATE: [
            "gate", "gherkin", "invest", "wikifix", "mermaid", "lint",
            "pytest", "test", "rejected", "blocking_issues", "validation"
        ],
        HarnessFailureCategory.PROMPT: [
            "hallucination", "drift", "format", "instruction", "unprompted",
            "clarification", "repetition", "slop"
        ],
    }

    @classmethod
    def categorize_issue(cls, text: str) -> HarnessFailureCategory:
        """Catégorise un message d'erreur ou issue bloquante dans la taxonomie du harnais."""
        lower = text.lower()
        scores: Dict[HarnessFailureCategory, int] = {cat: 0 for cat in HarnessFailureCategory}

        for cat, keywords in cls.KEYWORD_MAPPING.items():
            for kw in keywords:
                if kw in lower:
                    scores[cat] += 1

        best_cat = max(scores, key=scores.get)
        if scores[best_cat] > 0:
            return best_cat
        return HarnessFailureCategory.GATE  # Par défaut, rejet de conformité/porte

    @classmethod
    def analyze(cls, raw_data: Union[List[Dict[str, Any]], List[Any]]) -> HarnessDiagnosis:
        """
        Analyse une collection de traces ou d'issues pour produire le diagnostic d'isolation.
        """
        counts: Dict[str, int] = {cat.value: 0 for cat in HarnessFailureCategory}
        total_failures = 0

        for item in raw_data:
            issues_to_check: List[str] = []
            if isinstance(item, dict):
                critique = item.get("rubber_duck_critique") or {}
                issues_to_check.extend(critique.get("blocking_issues") or [])
                val_res = item.get("validation_result") or {}
                if val_res.get("error_code"):
                    issues_to_check.append(str(val_res.get("error_code")))
            elif hasattr(item, "metadata") and isinstance(item.metadata, dict):
                issues_to_check.extend(item.metadata.get("blocking_issues") or [])
                if getattr(item, "status", None) == "failure":
                    issues_to_check.append(getattr(item, "action_type", "failure"))

            for issue in issues_to_check:
                cat = cls.categorize_issue(str(issue))
                counts[cat.value] += 1
                total_failures += 1

        if total_failures == 0:
            # Baseline nominale si aucun échec détecté
            return HarnessDiagnosis(
                total_failures=0,
                distribution={cat.value: 25.0 for cat in HarnessFailureCategory},
                primary_bottleneck="None",
                recommendations=["Le harnais actuel ne présente aucun goulot d'étranglement bloquant."],
                isolated_harness_score=95,
            )

        distribution = {
            cat: round((cnt / total_failures) * 100.0, 1) for cat, cnt in counts.items()
        }
        primary = max(distribution, key=distribution.get)

        recs: List[str] = []
        if primary == HarnessFailureCategory.GATE.value:
            recs.append("Augmenter la tolérance pré-porte et enrichir les contextes INVEST/Gherkin.")
            recs.append("Ajuster le paramètre patience p pour éviter les abandons hâtifs de porte.")
        elif primary == HarnessFailureCategory.TOOLING.value:
            recs.append("Durcir les timeouts d'outils et injecter des schémas d'arguments plus stricts.")
            recs.append("Activer un retry déterministe exponentiel sur les commandes système.")
        elif primary == HarnessFailureCategory.MEMORY.value:
            recs.append("Déclencher la pré-compaction (ADR-0364) et le nettoyage SESSION_MEMORY_HEALTH.")
            recs.append("Restreindre le write-path à 200 lignes par bloc mémoire (ADR-0362).")
        else:  # PROMPT
            recs.append("Injecter des anti-slop templates Hallmark (ADR-0340).")
            recs.append("Séparer les instructions de contraintes des descriptions d'objectifs.")

        harness_score = max(40, 100 - min(60, total_failures * 5))

        return HarnessDiagnosis(
            total_failures=total_failures,
            distribution=distribution,
            primary_bottleneck=primary,
            recommendations=recs,
            isolated_harness_score=harness_score,
        )
