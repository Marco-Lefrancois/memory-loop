# -*- coding: utf-8 -*-
"""
src/dashboard/routers/graph.py — Routeur FastAPI pour les statistiques du graphe de connaissances.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from src.dashboard.project_utils import (
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.graph")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Graphe de Connaissances"])


@router.get("/api/graph")
def get_graph_stats(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Statistiques du graphe de connaissances (Ground Truth) et de l'hypergraphe.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    graph_candidates = [
        p_root / "memory" / "knowledge_graph.json",
        p_root / "memory" / "hypergraph.json",
        p_root / "graphify-out" / "graph.json",
        REPO_ROOT / "memory" / "knowledge_graph.json",
        REPO_ROOT / "graphify-out" / "graph.json",
    ]

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    for gc in graph_candidates:
        if gc.exists():
            try:
                with open(gc, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "nodes" in data and isinstance(data["nodes"], list):
                    nodes.extend(data["nodes"])
                if "edges" in data and isinstance(data["edges"], list):
                    edges.extend(data["edges"])
                if nodes:
                    break
            except Exception as e:
                logger.debug(
                    "Lecture d'un fichier de graphe échouée, candidat suivant essayé",
                    exc_info=True,
                    extra={
                        "component": "dashboard.routers.graph",
                        "operation": "get_graph_stats",
                        "graph_path": str(gc),
                        "error": str(e),
                    },
                )

    unique_nodes: Dict[str, Dict[str, Any]] = {}
    for n in nodes:
        nid = n.get("id") or n.get("name")
        if nid and nid not in unique_nodes:
            unique_nodes[nid] = n

    node_types: Dict[str, int] = {}
    for n in unique_nodes.values():
        ntype = n.get("type") or n.get("layer") or n.get("label") or "Concept"
        node_types[ntype] = node_types.get(ntype, 0) + 1

    sample_nodes = list(unique_nodes.values())[:15]

    return {
        "project": target_project,
        "total_nodes": len(unique_nodes),
        "total_edges": len(edges),
        "node_types": node_types,
        "sample_nodes": sample_nodes,
    }
