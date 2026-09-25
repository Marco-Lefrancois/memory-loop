"""
Types partagés pour EvidencePack 2.0 — brise la dépendance circulaire.
Conforme ADR-0394, ADR-0369.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


# ──────────────────────────────────────────────────────────────────────────────
# MLOOP-180-BE : Types de parité Phase 2 (ADR-0320 / ADR-0361)
# ──────────────────────────────────────────────────────────────────────────────

DecisionCategory = Literal[
    "architecture",
    "pattern",
    "refactoring",
    "performance",
    "security",
    "tooling",
    "testing",
]

_ALLOWED_DECISION_CATEGORIES = {
    "architecture",
    "pattern",
    "refactoring",
    "performance",
    "security",
    "tooling",
    "testing",
}


class VerbatimExtract(TypedDict, total=False):
    """Citation verbatim ancrée avec numéros de ligne (ADR-0320 §G)."""

    source_file: str
    lines: List[int]  # [start, end] — obligatoire pour VALIDATED
    quote: str  # texte verbatim non vide
    established_fact: str  # fait établi dérivé de la citation


class ImplementationDecision(TypedDict, total=False):
    """Décision d'implémentation tracée avec catégorie fermée."""

    decision_id: str
    category: str  # validé contre _ALLOWED_DECISION_CATEGORIES
    rationale: str
    alternatives_considered: List[str]
    timestamp: str  # ISO-8601 UTC


class DeclarativeContract(TypedDict, total=False):
    """Référence déclarative à une route/CTA réellement utilisée (Zéro Fausse Route)."""

    method: str  # GET | POST | PUT | PATCH | DELETE | N/A
    path: str  # route ou "[API de soumission à définir]"
    status: str  # "defined" | "to_define"
    source: str  # fichier source où la route est déclarée


class ConflictResolution(TypedDict, total=False):
    """Résolution documentée d'une divergence récit vs code/maquette."""

    artifact: str
    narrative_claim: str
    code_reality: str
    resolution: str
    authority: str  # "code" | "mockup" | "spec"


# ──────────────────────────────────────────────────────────────────────────────
# MLOOP-330-BE : Traçabilité Code ↔ Exigences (ADR-0394 / OpenSpec Ready)
# ──────────────────────────────────────────────────────────────────────────────


class CodeTraceabilityEntry(TypedDict, total=False):
    """Entrée de traçabilité Code ↔ Exigences (ADR-0394 / OpenSpec Ready)."""

    ast_symbol: (
        str  # chemin/fichier.ext::Symbole (ex: "src/core/auth.py::TokenVerifier.verify_expiration")
    )
    requirement_ref: str  # Règle Métier RM-XXX ou catégorie autorisée (INFRA, TECH-FOUNDATION)
    gherkin_scenario: str  # Scénario Gherkin associé (Pilier 1-4)
    rationale: str  # Justification technique/métier (minimum 10 caractères)
    test_symbol: Optional[str]  # Test unitaire associé (ex: "tests/test_auth.py::test_expired")


# Export des constantes pour validation
__all__ = [
    "DecisionCategory",
    "_ALLOWED_DECISION_CATEGORIES",
    "VerbatimExtract",
    "ImplementationDecision",
    "DeclarativeContract",
    "ConflictResolution",
    "CodeTraceabilityEntry",
]
