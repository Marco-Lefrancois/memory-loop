"""
_db_search.py — Helpers JSON, recherche FTS lexique & Fact-Search 2.0.

Extraction MLOOP-178-BE (BR=20) depuis src/loop_mem/db.py monolithique (956 L).
Famille Q1-A : helpers JSON (active_project, graphe mémoire), recherche FTS5
du lexique métier, pondération SSOT LAYER_WEIGHTS et façade Fact-Search 2.0
(ADR-0326 — délégation canonique vers src.engine.fact_search).

Tout accès SQLite passe par `with get_observation_db_session()` (ADR-0369) ;
les helpers fichiers utilisent exclusivement `with open(...)` (zéro ressource nue).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.loop_mem.db._db_connection import get_observation_db_session

logger = logging.getLogger(__name__)


def get_active_project() -> Optional[str]:
    """Retourne le nom du projet actif stocké dans memory/active_project.json."""
    active_json = Path("memory/active_project.json")
    if active_json.exists():
        try:
            with open(active_json, "r", encoding="utf-8") as f:
                return json.load(f).get("active_project")
        except Exception as e:
            logger.debug(
                "Lecture de active_project.json échouée",
                exc_info=True,
                extra={
                    "component": "loop_mem.db",
                    "operation": "get_active_project",
                    "path": str(active_json),
                    "error": str(e),
                },
            )
    return None


def search_in_memory(project_path: Path, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Recherche plein texte en mémoire dans le graphe consolidé du projet.
    Fusionne knowledge_graph.json et graph.json, et filtre sur les attributs textuels.
    """
    nodes = []

    # 1. Charger knowledge_graph.json
    kg_file = project_path / "memory" / "knowledge_graph.json"
    if kg_file.exists():
        try:
            with open(kg_file, "r", encoding="utf-8") as f:
                nodes.extend(json.load(f).get("nodes", []))
        except Exception as e:
            logger.debug(
                "Lecture de knowledge_graph.json échouée (recherche mémoire partielle)",
                exc_info=True,
                extra={
                    "component": "loop_mem.db",
                    "operation": "search_in_memory",
                    "kg_file": str(kg_file),
                    "error": str(e),
                },
            )

    # 2. Charger graph.json
    graph_file = project_path / "graphify-out" / "graph.json"
    if graph_file.exists():
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                nodes.extend(json.load(f).get("nodes", []))
        except Exception as e:
            logger.debug(
                "Lecture de graph.json échouée (recherche mémoire partielle)",
                exc_info=True,
                extra={
                    "component": "loop_mem.db",
                    "operation": "search_in_memory",
                    "graph_file": str(graph_file),
                    "error": str(e),
                },
            )

    # Dédupliquer les nœuds par ID pour éviter les doublons de fusion
    seen_ids = set()
    unique_nodes = []
    for n in nodes:
        node_id = n.get("id")
        if node_id and node_id not in seen_ids:
            seen_ids.add(node_id)
            unique_nodes.append(n)

    query_lower = query.lower().strip()
    if not query_lower:
        return []

    results = []
    for n in unique_nodes:
        node_id = n.get("id", "")
        label = n.get("label", "")
        category = n.get("category", "")
        props = n.get("properties", {})

        desc = props.get("description", "")
        text_chunk = props.get("text_chunk", "")

        # Concaténation de recherche
        search_content = f"{node_id} {label} {category} {desc} {text_chunk}".lower()

        if query_lower in search_content:
            # Calcul du score de pertinence simple
            score = 1.0
            if query_lower == node_id.lower():
                score += 5.0
            elif query_lower in node_id.lower():
                score += 3.0

            if query_lower == label.lower():
                score += 4.0
            elif query_lower in label.lower():
                score += 2.0

            if query_lower in category.lower():
                score += 1.0

            # Snippet d'aperçu propre
            snippet_source = text_chunk or desc or "Pas de description."
            snippet = snippet_source[:150] + "..." if len(snippet_source) > 150 else snippet_source

            results.append(
                {
                    "id": node_id,
                    "label": label or node_id,
                    "category": category,
                    "snippet": snippet,
                    "score": score,
                }
            )

    # Trier par score décroissant
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def search_lexicon_terms(
    query: str,
    project_name: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Recherche plein texte dans le lexique métier via FTS5."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()

        # Nettoyage de la requête pour syntaxe FTS5 (remplacer ponctuation par des espaces)
        clean_q = "".join(c if c.isalnum() else " " for c in query).strip()
        if not clean_q:
            return []

        words = clean_q.split()
        fts_query = " ".join(f"{w}*" for w in words)

        if project_name:
            cursor.execute(
                """
                SELECT l.id, l.project_name, l.term, l.aliases_json, l.category,
                       l.definition, l.target_type, l.target_id, l.source_file,
                       bm25(project_lexicon_fts) as rank
                FROM project_lexicon_fts f
                JOIN project_lexicon l ON l.id = CAST(f.lexicon_id AS INTEGER)
                WHERE project_lexicon_fts MATCH ? AND f.project_name = ?
                ORDER BY rank ASC LIMIT ?
            """,
                (fts_query, project_name, limit),
            )
        else:
            cursor.execute(
                """
                SELECT l.id, l.project_name, l.term, l.aliases_json, l.category,
                       l.definition, l.target_type, l.target_id, l.source_file,
                       bm25(project_lexicon_fts) as rank
                FROM project_lexicon_fts f
                JOIN project_lexicon l ON l.id = CAST(f.lexicon_id AS INTEGER)
                WHERE project_lexicon_fts MATCH ?
                ORDER BY rank ASC LIMIT ?
            """,
                (fts_query, limit),
            )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "project_name": row["project_name"],
                    "term": row["term"],
                    "aliases": json.loads(row["aliases_json"] or "[]"),
                    "category": row["category"],
                    "definition": row["definition"],
                    "target_type": row["target_type"],
                    "target_id": row["target_id"],
                    "source_file": row["source_file"],
                }
            )
        return results


# ═══════════════════════════════════════════════════════════
# Fact-Search 2.0 — Chunks SSOT, Breadcrumbs & Coverage (ADR-0326)
# ═══════════════════════════════════════════════════════════

LAYER_WEIGHTS = {
    "architecture": 1.2,
    "business_rules": 1.2,
    "context": 1.1,
    "models": 1.0,
    "knowledge": 0.9,
    "ingested": 0.8,
    "reference": 1.0,
    "docs": 0.7,
}


def _determine_ssot_layer(rel_path: str) -> str:
    p = rel_path.replace("\\", "/").lower()
    if "architecture-segment2" in p or "01-architecture" in p or "adr-" in p:
        return "architecture"
    if "analyse-fonctionnelle" in p or "02-business-rules" in p or "rm-" in p:
        return "business_rules"
    if "03-models" in p or "model" in p or "structure-de-données" in p:
        return "models"
    if "reference" in p or ".wiki" in p:
        return "reference"
    if "00-ingested" in p or "ingested" in p:
        return "ingested"
    if "06-knowledge" in p:
        return "knowledge"
    if "context.md" in p:
        return "context"
    return "docs"


# ──────────────────────────────────────────────────────────────────────────────
# 6. MOTEUR FACT-SEARCH 2.0 (Délégation Canonique vers src.engine.fact_search)
# ──────────────────────────────────────────────────────────────────────────────
def index_project_docs_to_fts5(project_name: str, db_path: Optional[Path] = None) -> int:
    """Scanne et indexe les documents d'un projet dans SQLite FTS5 via TriFusionChunker."""
    from src.engine.fact_search import FactSearchIndexer

    project_dir = (
        Path("Projects") / project_name
        if (Path("Projects") / project_name).exists()
        else Path.cwd()
    )
    docs_dir = project_dir / "docs"
    return FactSearchIndexer.index_project_docs(
        project_name=project_name, docs_dir=docs_dir, db_path=db_path
    )


def fact_search_query(
    query: str,
    project_name: Optional[str] = None,
    expand_synonyms: bool = True,
    limit: int = 10,
    log_audit: bool = True,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Recherche plein texte déterministe avec expansion, BM25 et extraits KWIC."""
    from src.engine.fact_search import FactSearchRetriever

    return FactSearchRetriever.search(
        query=query,
        project_name=project_name,
        expand_synonyms=expand_synonyms,
        limit=limit,
        log_audit=log_audit,
        db_path=db_path,
    )


def calculate_story_fact_coverage(
    story_path: Path,
    project_name: str,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Calcule le score de couverture Fact-Search d'une User Story (ADR-0326)."""
    from src.engine.fact_search import FactSearchCoverageEvaluator

    return FactSearchCoverageEvaluator.evaluate_story_coverage(
        story_path=story_path,
        project_name=project_name,
        db_path=db_path,
    )
