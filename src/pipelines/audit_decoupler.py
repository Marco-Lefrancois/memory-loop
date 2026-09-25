"""
Grille d'Audit Architectural Découplée : Structure Sémantique vs Rendu (MLOOP-303-BE / EPIC-30).

Applique une barrière multiplicative stricte subordonnant la note globale d'un
artefact d'architecture à sa vérité topologique. Un schéma dont les flux causaux
sont manquants ou inversés ne peut jamais obtenir la moyenne, éliminant l'illusion
cosmétique (scores visuels flatteurs sur diagrammes structurellement faux).

Formule : Score = S_topo * (0.7 + 0.3 * S_visuel)   avec S_topo, S_visuel ∈ [0.0, 1.0].
Sanction éliminatoire : inversion causale => S_topo forcé à 0.0 => Score = 0.0.
Seuil Gate 2 / Gate 4 : Score >= 0.85.

Motifs : CAUSAL_FLOW_INVERSION_DETECTED, TOPOLOGY_INTEGRITY_DEFICIT.

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, logging structuré, failure contract).
Référence scientifique : ReFigBench (arXiv:2609.18844, Découplage Topologique).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.logger import get_logger

logger = get_logger("pipelines.audit_decoupler")

# Coefficients de la barrière multiplicative.
BASE_WEIGHT: float = 0.7
VISUAL_WEIGHT: float = 0.3

# Seuil d'admissibilité aux Gate 2 / Gate 4.
GATE_THRESHOLD: float = 0.85

# Codes de diagnostic standardisés.
ERR_CAUSAL_INVERSION = "CAUSAL_FLOW_INVERSION_DETECTED"
ERR_TOPOLOGY_DEFICIT = "TOPOLOGY_INTEGRITY_DEFICIT"


class ScoreOutOfBoundsError(ValueError):
    """Levée lorsqu'une note d'entrée est hors des bornes [0.0, 1.0]."""


@dataclass
class AuditScoreResult:
    """Résultat du calcul d'audit découplé (contrat gelé MLOOP-303-BE)."""

    composite_score: float
    is_approved: bool
    topological_penalty: float
    details: dict = field(default_factory=dict)


def _validate_bounds(name: str, value: float) -> float:
    """Valide qu'une note est numérique et bornée dans [0.0, 1.0]."""
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ScoreOutOfBoundsError(f"La note '{name}' n'est pas numérique : {value!r}") from exc
    if numeric < 0.0 or numeric > 1.0:
        raise ScoreOutOfBoundsError(
            f"La note '{name}' = {numeric} est hors des bornes autorisées [0.0, 1.0]"
        )
    return numeric


def calculate_decoupled_architecture_score(
    topology_score: float,
    visual_score: float,
    causal_inversion: bool = False,
    anomalies: list[str] | None = None,
) -> AuditScoreResult:
    """
    Calcule la note composite découplée à barrière multiplicative.

    Args:
        topology_score: Note topologique S_topo ∈ [0.0, 1.0].
        visual_score: Note visuelle S_visuel ∈ [0.0, 1.0].
        causal_inversion: True si une inversion causale de flux est détectée
            (force S_topo à 0.0, sanction éliminatoire).
        anomalies: Liste optionnelle d'anomalies topologiques relevées en amont.

    Returns:
        AuditScoreResult : score composite, verdict d'approbation, pénalité
        topologique et détail transparent (S_topo, S_visuel, seuil, diagnostic).

    Raises:
        ScoreOutOfBoundsError: si une note d'entrée est non numérique ou hors [0.0, 1.0].
    """
    s_topo = _validate_bounds("topology_score", topology_score)
    s_visual = _validate_bounds("visual_score", visual_score)
    anomalies = list(anomalies) if anomalies else []

    effective_topo = s_topo
    diagnostic = None

    # Sanction éliminatoire : inversion causale => S_topo = 0.0.
    if causal_inversion:
        effective_topo = 0.0
        diagnostic = ERR_CAUSAL_INVERSION
    elif s_topo < 1.0:
        diagnostic = ERR_TOPOLOGY_DEFICIT

    composite = round(effective_topo * (BASE_WEIGHT + VISUAL_WEIGHT * s_visual), 4)
    is_approved = composite >= GATE_THRESHOLD
    topological_penalty = round(s_topo - effective_topo, 4)

    details = {
        "S_topo": s_topo,
        "S_topo_effective": effective_topo,
        "S_visuel": s_visual,
        "gate_threshold": GATE_THRESHOLD,
        "causal_inversion": causal_inversion,
        "diagnostic": diagnostic,
        "anomalies": anomalies,
        "formula": "S_topo * (0.7 + 0.3 * S_visuel)",
    }

    result = AuditScoreResult(
        composite_score=composite,
        is_approved=is_approved,
        topological_penalty=topological_penalty,
        details=details,
    )

    logger.debug(
        "Calcul d'audit découplé achevé.",
        extra={
            "check_name": "audit_decoupler",
            "composite_score": composite,
            "is_approved": is_approved,
            "s_topo": s_topo,
            "s_visuel": s_visual,
            "diagnostic": diagnostic,
        },
    )
    return result


__all__ = [
    "calculate_decoupled_architecture_score",
    "AuditScoreResult",
    "ScoreOutOfBoundsError",
    "GATE_THRESHOLD",
]
