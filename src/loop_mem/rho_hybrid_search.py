"""
Recherche Hybride RHO (BM25 + Vector + Graph) avec RRF et poids configurables.
Consolide le flux vectoriel RHO et la recherche hybride sur embeddings locaux (MLOOP-102-BE).
"""

import json
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.loop_mem.ollama_embed import cosine_similarity, get_embedding

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {"bm25": 0.4, "vector": 0.4, "graph": 0.2}
VECTOR_SIMILARITY_THRESHOLD = 0.30
MAX_RESULTS_PER_STREAM = 50


class RHOHybridSearch:
    """Moteur de recherche hybride RHO combinant BM25, Vectoriel et Graph."""

    def __init__(
        self,
        project_name: str,
        weights: Optional[Dict[str, float]] = None,
        db_path: Optional[Path] = None,
    ):
        self.project_name = project_name
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self._normalize_weights()
        self.db_path = db_path or Path("memory/loop_mem.db")
        self.graph_file = Path("Projects") / project_name / "memory" / "knowledge_graph.json"
        self.graphify_file = Path("Projects") / project_name / "graphify-out" / "graph.json"

    def _normalize_weights(self) -> None:
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def _stream_bm25(self, query: str) -> List[Dict[str, Any]]:
        """Flux BM25 sur les champs texte de rho_memory."""
        results = []
        tokens = [t.lower() for t in re.split(r"\W+", query) if len(t) > 2]
        if not tokens:
            return results

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, keyword, error_trace, solution FROM rho_memory "
                    "WHERE project_name = ?",
                    (self.project_name,),
                )
                for row in cursor.fetchall():
                    text = f"{row['keyword']} {row['error_trace']} {row['solution']}".lower()
                    matches = sum(text.count(tok) for tok in tokens)
                    if matches > 0:
                        results.append(
                            {
                                "id": f"rho://{row['id']}",
                                "title": row["keyword"],
                                "score_raw": float(matches),
                                "stream": "bm25",
                                "data": dict(row),
                            }
                        )
        except Exception as exc:
            logger.warning(
                "Erreur flux BM25 RHO",
                exc_info=True,
                extra={"project": self.project_name, "query_len": len(query)},
            )

        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results[:MAX_RESULTS_PER_STREAM]

    def _stream_vector(self, query: str) -> List[Dict[str, Any]]:
        """Flux vectoriel dense sur les embeddings RHO."""
        query_vec = get_embedding(query)
        if not query_vec:
            return []

        results = []
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, keyword, error_trace, solution, embedding_json "
                    "FROM rho_memory WHERE project_name = ?",
                    (self.project_name,),
                )
                for row in cursor.fetchall():
                    try:
                        db_embed = json.loads(row["embedding_json"])
                        if not db_embed:
                            continue
                        score = cosine_similarity(query_vec, db_embed)
                        if score >= VECTOR_SIMILARITY_THRESHOLD:
                            results.append(
                                {
                                    "id": f"rho://{row['id']}",
                                    "title": row["keyword"],
                                    "score_raw": float(score),
                                    "stream": "vector",
                                    "data": {
                                        "id": row["id"],
                                        "keyword": row["keyword"],
                                        "error_trace": row["error_trace"],
                                        "solution": row["solution"],
                                    },
                                }
                            )
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.debug(
                            "Embedding corrompu ou invalide pour une ligne RHO, ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "loop_mem.rho_hybrid_search",
                                "operation": "stream_vector_parse_embedding",
                                "row_id": row["id"],
                                "error": str(e),
                            },
                        )
                        continue
        except Exception as exc:
            logger.warning(
                "Erreur flux vectoriel RHO",
                exc_info=True,
                extra={"project": self.project_name},
            )

        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results[:MAX_RESULTS_PER_STREAM]

    def _stream_graph(self, query: str) -> List[Dict[str, Any]]:
        """Flux graph : recherche de nœuds dans les graphes de connaissances."""
        results = []
        q_lower = query.lower()
        for g_file in [self.graph_file, self.graphify_file]:
            if g_file.exists():
                try:
                    data = json.loads(g_file.read_text(encoding="utf-8"))
                    for n in data.get("nodes", []):
                        name = str(n.get("name") or n.get("id") or "").lower()
                        if q_lower in name:
                            results.append(
                                {
                                    "id": f"graph://{n.get('id', name)}",
                                    "title": n.get("name", name),
                                    "score_raw": 1.0,
                                    "stream": "graph",
                                    "data": n,
                                }
                            )
                except Exception as exc:
                    logger.debug("Erreur lecture graphe RHO", exc_info=True)

        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results[:MAX_RESULTS_PER_STREAM]

    def search(
        self,
        query: str,
        top_k: int = 5,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Recherche hybride RHO avec fusion RRF et poids configurables."""
        t0 = time.perf_counter()
        if not query or not query.strip():
            return {"results": [], "latency_ms": 0.0, "total": 0}

        current_weights = weights or self.weights
        total_weight = sum(current_weights.values())
        if total_weight > 0:
            current_weights = {k: v / total_weight for k, v in current_weights.items()}

        bm25_res = self._stream_bm25(query)
        vector_res = self._stream_vector(query)
        graph_res = self._stream_graph(query)

        rrf_scores: Dict[str, float] = {}
        matched_streams: Dict[str, set] = {}
        meta_map: Dict[str, Dict[str, Any]] = {}

        streams = [
            (bm25_res, current_weights.get("bm25", 0.4)),
            (vector_res, current_weights.get("vector", 0.4)),
            (graph_res, current_weights.get("graph", 0.2)),
        ]

        for stream_items, weight in streams:
            for rank, item in enumerate(stream_items, 1):
                doc_id = item["id"]
                rrf_increment = weight * (1.0 / (60 + rank))
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_increment
                matched_streams.setdefault(doc_id, set()).add(item["stream"])
                if doc_id not in meta_map:
                    meta_map[doc_id] = item

        final_list = []
        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

        for doc_id, rrf_val in rrf_scores.items():
            meta = meta_map[doc_id]
            stream_count = len(matched_streams[doc_id])
            relevance = min(1.0, (stream_count / 3.0) * 0.6 + (rrf_val / max_rrf) * 0.4)
            if meta.get("is_superseded", False):
                relevance *= 0.1

            final_list.append(
                {
                    "id": doc_id,
                    "title": meta.get("title", doc_id),
                    "relevance": round(relevance, 4),
                    "rrf_score": round(rrf_val, 6),
                    "streams": list(matched_streams[doc_id]),
                    "is_superseded": meta.get("is_superseded", False),
                    "data": meta.get("data", {}),
                }
            )

        final_list.sort(
            key=lambda x: (not x["is_superseded"], x["relevance"], x["rrf_score"]),
            reverse=True,
        )

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "results": final_list[:top_k],
            "latency_ms": latency_ms,
            "total": len(final_list),
            "weights_used": current_weights,
        }

    def _get_db_connection(self) -> sqlite3.Connection:
        """Retourne une connexion à la base de données avec timeout explicite (ADR-0369)."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=20000;")
        except Exception as e:
            logger.debug(
                "Configuration des PRAGMA SQLite échouée, connexion retournée avec les défauts",
                exc_info=True,
                extra={
                    "component": "loop_mem.rho_hybrid_search",
                    "operation": "db_connection_pragma",
                    "db_path": str(self.db_path),
                    "error": str(e),
                },
            )
        return conn


def search_rho_hybrid(
    project_name: str,
    query: str,
    top_k: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Fonction publique pour la recherche hybride RHO."""
    searcher = RHOHybridSearch(project_name, weights=weights)
    return searcher.search(query, top_k=top_k)


# Ré-export API publique (extraction ADR-0202 vers _rho_stats.py)
from src.loop_mem._rho_stats import get_rho_hybrid_stats  # noqa: E402

__all__ = ["RHOHybridSearch", "search_rho_hybrid", "get_rho_hybrid_stats"]
