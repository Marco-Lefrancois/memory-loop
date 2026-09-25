"""
Validation Topologique Anti-Effondrement des Connecteurs Archify (MLOOP-301-BE / EPIC-30).

Contrôle rigoureusement que les connecteurs (edges) d'un diagramme Archify JSON IR
sont ancrés à de véritables nœuds déclaratifs, interdisant le phénomène de
*Connector Collapse* (boîtes flottantes sans liens) et les arêtes orphelines.

Règles :
  - Graphe Fermé Strict : toute arête relie un `from` et un `to` de nœuds existants.
  - Anti-Effondrement : > 3 nœuds et 0 arête => CONNECTOR_COLLAPSE_DETECTED.
  - Auto-boucles non déclarées : edge from == to sans flag `self_loop` => faute.
  - Sens causal : direction ∈ {forward, backward, bidirectional} si présent.

Motifs : CONNECTOR_INTEGRITY_FAIL, CONNECTOR_COLLAPSE_DETECTED.

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, logging structuré, zéro except pass nu).
Référence scientifique : ReFigBench (arXiv:2609.18844, §5).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.logger import get_logger

logger = get_logger("pipelines.connector_validator")

# Seuil anti-effondrement : au-delà de ce nombre de nœuds, l'absence d'arête est fatale.
COLLAPSE_NODE_THRESHOLD: int = 3

# Codes d'erreur standardisés.
ERR_INTEGRITY_FAIL = "CONNECTOR_INTEGRITY_FAIL"
ERR_COLLAPSE = "CONNECTOR_COLLAPSE_DETECTED"

_VALID_DIRECTIONS = {"forward", "backward", "bidirectional"}


@dataclass
class ConnectorValidationResult:
    """Résultat de la validation topologique (contrat gelé MLOOP-301-BE)."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


def _build_node_registry(nodes: list) -> tuple[set[str], list[str]]:
    """Construit le registre des identifiants de nœuds valides et remonte les anomalies."""
    registry: set[str] = set()
    errors: list[str] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"{ERR_INTEGRITY_FAIL}: nœud #{index} n'est pas un objet valide")
            continue
        node_id = node.get("id")
        if node_id is None or str(node_id).strip() == "":
            errors.append(f"{ERR_INTEGRITY_FAIL}: nœud #{index} sans identifiant non vide")
            continue
        node_id = str(node_id)
        if node_id in registry:
            errors.append(f"{ERR_INTEGRITY_FAIL}: identifiant de nœud dupliqué '{node_id}'")
            continue
        registry.add(node_id)
    return registry, errors


def _edge_endpoints(edge: dict) -> tuple:
    """Résout les extrémités d'une arête selon la convention Archify IR ou JSONCanvas.

    Archify JSON IR utilise `from`/`to` ; le format Obsidian JSONCanvas (.canvas)
    utilise `fromNode`/`toNode`. Les deux conventions sont acceptées.
    """
    src = edge.get("from", edge.get("fromNode"))
    dst = edge.get("to", edge.get("toNode"))
    return src, dst


def _validate_edge(edge, index: int, registry: set[str]) -> list[str]:
    """Valide une arête unique contre le registre de nœuds. Retourne la liste d'erreurs."""
    errors: list[str] = []
    if not isinstance(edge, dict):
        return [f"{ERR_INTEGRITY_FAIL}: arête #{index} n'est pas un objet valide"]

    src, dst = _edge_endpoints(edge)

    if src is None or str(src).strip() == "":
        errors.append(f"{ERR_INTEGRITY_FAIL}: arête #{index} sans extrémité 'from' définie")
    elif str(src) not in registry:
        errors.append(
            f"{ERR_INTEGRITY_FAIL}: arête #{index} référence un nœud source inexistant '{src}'"
        )

    if dst is None or str(dst).strip() == "":
        errors.append(f"{ERR_INTEGRITY_FAIL}: arête #{index} sans extrémité 'to' définie")
    elif str(dst) not in registry:
        errors.append(
            f"{ERR_INTEGRITY_FAIL}: arête #{index} référence un nœud cible inexistant '{dst}'"
        )

    # Auto-boucle non déclarée explicitement.
    if src is not None and dst is not None and str(src) == str(dst):
        if not edge.get("self_loop", False):
            errors.append(
                f"{ERR_INTEGRITY_FAIL}: auto-boucle non déclarée sur le nœud '{src}' (arête #{index})"
            )

    # Sens causal, si fourni, doit être univoque.
    direction = edge.get("direction")
    if direction is not None and str(direction).lower() not in _VALID_DIRECTIONS:
        errors.append(
            f"{ERR_INTEGRITY_FAIL}: arête #{index} avec sens causal invalide '{direction}' "
            f"(attendu: {', '.join(sorted(_VALID_DIRECTIONS))})"
        )
    return errors


def validate_connector_integrity(diagram: dict) -> ConnectorValidationResult:
    """
    Valide l'intégrité topologique d'un diagramme Archify JSON IR.

    Args:
        diagram: Spécification JSON IR avec clés `nodes` (list[dict]) et `edges` (list[dict]).

    Returns:
        ConnectorValidationResult : verdict, erreurs détaillées, comptes nœuds/arêtes.
        Ne lève jamais d'exception non gérée (Zero Crash Policy).
    """
    if not isinstance(diagram, dict):
        return ConnectorValidationResult(
            is_valid=False,
            errors=[f"{ERR_INTEGRITY_FAIL}: spécification de diagramme absente ou invalide"],
        )

    nodes = diagram.get("nodes")
    edges = diagram.get("edges")
    nodes = nodes if isinstance(nodes, list) else []
    edges = edges if isinstance(edges, list) else []

    registry, errors = _build_node_registry(nodes)
    node_count = len(registry)
    edge_count = len(edges)

    # Détection d'effondrement relationnel (Connector Collapse).
    if node_count > COLLAPSE_NODE_THRESHOLD and edge_count == 0:
        errors.append(
            f"{ERR_COLLAPSE}: {node_count} blocs modulaires sans aucun connecteur relationnel"
        )

    for index, edge in enumerate(edges):
        errors.extend(_validate_edge(edge, index, registry))

    is_valid = len(errors) == 0
    result = ConnectorValidationResult(
        is_valid=is_valid,
        errors=errors,
        node_count=node_count,
        edge_count=edge_count,
    )

    if is_valid:
        logger.debug(
            "Validation topologique Archify réussie (graphe fermé).",
            extra={
                "check_name": "connector_validator",
                "node_count": node_count,
                "edge_count": edge_count,
                "completeness": "100%",
            },
        )
    else:
        logger.debug(
            "Validation topologique Archify en échec.",
            extra={
                "check_name": "connector_validator",
                "node_count": node_count,
                "edge_count": edge_count,
                "error_count": len(errors),
            },
        )
    return result


__all__ = ["validate_connector_integrity", "ConnectorValidationResult"]
