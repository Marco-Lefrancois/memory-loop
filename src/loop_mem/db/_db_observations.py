"""
_db_observations.py — CRUD des observations de session & mémoire RHO.

Extraction MLOOP-178-BE (BR=20) depuis src/loop_mem/db.py monolithique (956 L).
Famille Q1-A : CRUD observations (add/search/timeline/by_id ~130 L)
+ CRUD mémoire RHO (chaos testing / RAG sémantique ~80 L).

Toutes les fonctions passent par `with get_observation_db_session()` (ADR-0369) :
zéro connexion nue, auto-commit/rollback garantis par le CM de _db_connection.
"""

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from src.loop_mem.db._db_connection import get_observation_db_session

logger = logging.getLogger(__name__)


def add_observation(
    project_name: str,
    obs_type: str,
    content: str,
    file_scope: Optional[str] = None,
) -> int:
    """Ajoute une observation et la synchronise dans l'index FTS5.
    Retourne l'ID de la nouvelle observation."""
    from datetime import datetime

    now_iso = datetime.now().isoformat()
    with get_observation_db_session() as conn:
        cursor = conn.cursor()

        # 1. Insert into observations table
        cursor.execute(
            """
            INSERT INTO observations (project_name, type, file_scope, timestamp, content)
            VALUES (?, ?, ?, ?, ?)
        """,
            (project_name, obs_type, file_scope, now_iso, content),
        )
        obs_id = cursor.lastrowid

        # 2. Insert into FTS5 table
        cursor.execute(
            """
            INSERT INTO observations_fts (observation_id, project_name, type, content)
            VALUES (?, ?, ?, ?)
        """,
            (str(obs_id), project_name, obs_type, content),
        )

        return obs_id


def search_observations(
    query: str,
    project_name: Optional[str] = None,
    obs_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Recherche plein texte dans les observations via FTS5."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()

        conditions: List[str] = []

        # Nettoyer la requête pour FTS5 (enlever les opérateurs spéciaux risquant des syntax errors)
        cleaned_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
        if not cleaned_query:
            cleaned_query = "*"

        params: List[Any] = [cleaned_query]

        if project_name:
            conditions.append("fts.project_name = ?")
            params.append(project_name)
        if obs_type:
            conditions.append("fts.type = ?")
            params.append(obs_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            # On joint les 2 tables via observation_id pour récupérer file_scope et timestamp
            cursor.execute(
                f"""
                SELECT o.id, o.project_name, o.type, o.file_scope, o.timestamp, o.content
                FROM observations_fts fts
                JOIN observations o ON o.id = CAST(fts.observation_id AS INTEGER)
                WHERE observations_fts MATCH ? AND {where_clause}
                ORDER BY rank
                LIMIT 20
            """,
                params,
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Fallback si MATCH échoue quand même : recherche simple par LIKE
            like_clause = f"%{query}%"
            params_fallback = [like_clause]
            conditions_fallback = []
            if project_name:
                conditions_fallback.append("o.project_name = ?")
                params_fallback.append(project_name)
            if obs_type:
                conditions_fallback.append("o.type = ?")
                params_fallback.append(obs_type)
            where_clause_fallback = (
                " AND ".join(conditions_fallback) if conditions_fallback else "1=1"
            )

            cursor.execute(
                f"""
                SELECT o.id, o.project_name, o.type, o.file_scope, o.timestamp, o.content
                FROM observations o
                WHERE o.content LIKE ? AND {where_clause_fallback}
                ORDER BY o.timestamp DESC
                LIMIT 20
            """,
                params_fallback,
            )
            return [dict(row) for row in cursor.fetchall()]


def get_session_timeline(project_name: str) -> List[Dict[str, Any]]:
    """Timeline chronologique (desc) de toutes les observations d'un projet."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_name, type, file_scope, timestamp, content
            FROM observations
            WHERE project_name = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """,
            (project_name,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_observation_by_id(obs_id: int) -> Optional[Dict[str, Any]]:
    """Récupère le détail complet d'une observation par son ID."""
    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_name, type, file_scope, timestamp, content
            FROM observations
            WHERE id = ?
        """,
            (obs_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ═══════════════════════════════════════════════════════════
# RHO Memory - Chaos Testing & Semantic RAG
# ═══════════════════════════════════════════════════════════


def add_rho_rule(project_name: str, keyword: str, error_trace: str, solution: str) -> int:
    """Ajoute une règle RHO avec son embedding Ollama pour recherche sémantique."""
    from src.loop_mem.ollama_embed import get_embedding

    # On embedde la trace d'erreur pour pouvoir la retrouver quand un bug similaire se produit
    embed_vector = get_embedding(error_trace)
    embed_json = json.dumps(embed_vector) if embed_vector else "[]"

    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rho_memory (project_name, keyword, error_trace, solution, embedding_json)
            VALUES (?, ?, ?, ?, ?)
        """,
            (project_name, keyword, error_trace, solution, embed_json),
        )
        return cursor.lastrowid


def search_rho_solution(error_trace: str, threshold: float = 0.70) -> List[Dict[str, Any]]:
    """Cherche la solution la plus similaire dans la mémoire RHO via similarité cosinus locale."""
    from src.loop_mem.ollama_embed import get_embedding, cosine_similarity

    query_embed = get_embedding(error_trace)
    if not query_embed:
        return []

    results = []
    with get_observation_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, project_name, keyword, error_trace, solution, embedding_json FROM rho_memory"
        )
        for row in cursor.fetchall():
            try:
                db_embed = json.loads(row["embedding_json"])
                if db_embed:
                    score = cosine_similarity(query_embed, db_embed)
                    if score >= threshold:
                        results.append(
                            {
                                "id": row["id"],
                                "project_name": row["project_name"],
                                "keyword": row["keyword"],
                                "error_trace": row["error_trace"],
                                "solution": row["solution"],
                                "score": score,
                            }
                        )
            except Exception:
                logger.debug(
                    "Ligne RHO ignorée (embedding illisible ou incompatible)",
                    exc_info=True,
                    extra={"rho_id": row["id"], "project": row["project_name"]},
                )

    # Tri par score décroissant
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def search_rho_hybrid_solution(
    project_name: str,
    query: str,
    top_k: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Recherche hybride RHO combinant BM25, Vector et Graph (MLOOP-102-BE).

    Args:
        project_name: Nom du projet
        query: Requête de recherche
        top_k: Nombre de résultats à retourner
        weights: Poids personnalisés pour BM25, Vector, Graph

    Returns:
        Dictionnaire avec les résultats, latence et métadonnées
    """
    from src.loop_mem.rho_hybrid_search import RHOHybridSearch

    searcher = RHOHybridSearch(project_name, weights=weights)
    return searcher.search(query, top_k=top_k)
