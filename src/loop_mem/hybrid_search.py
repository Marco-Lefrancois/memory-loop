import hashlib
import json
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List

from src.loop_mem.ollama_embed import (
    OLLAMA_EMBED_MODEL,
    cosine_similarity,
    get_embedding,
)

logger = logging.getLogger(__name__)

RRF_K = 60


class TriStreamHybridSearch:
    """Moteur de recherche hybride Tri-Flux (BM25 + Vectoriel + Graphify) avec RRF et score de confiance."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.graph_file = project_path / "memory" / "knowledge_graph.json"
        self.graphify_file = project_path / "graphify-out" / "graph.json"
        self._vector_cache_db = str(project_path / "memory" / "vector_cache.db")

    def _stream_text(self, query: str) -> List[Dict[str, Any]]:
        results = []
        tokens = [t.lower() for t in re.split(r"\W+", query) if len(t) > 2]
        if not tokens:
            return results

        docs_dir = self.project_path / "docs"
        if docs_dir.exists():
            for f in docs_dir.rglob("*.md"):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore").lower()
                    matches = sum(text.count(tok) for tok in tokens)
                    if matches > 0:
                        doc_id = str(f.relative_to(self.project_path)).replace("\\", "/")
                        is_stale = (
                            "superseded" in text
                            or "statut : stale" in text
                            or "statut: obsolete" in text
                        )
                        results.append(
                            {
                                "id": doc_id,
                                "title": f.stem,
                                "score_raw": float(matches),
                                "is_superseded": is_stale,
                                "stream": "text",
                            }
                        )
                except Exception as exc:
                    logger.debug(f"Erreur lecture doc {f}: {exc}", exc_info=True)

        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results

    def _stream_vector(self, query: str) -> List[Dict[str, Any]]:
        """Flux vectoriel dense via embeddings locaux (mxbai-embed-large) avec
        similarité cosinus et cache SQLite. Bascule silencieuse et tracée vers
        l'approximation lexicale (Jaccard) si le moteur d'embedding est indisponible
        (mode dégradé non bloquant — MLOOP-102-BE / ADR-0369)."""
        query_vec = get_embedding(query)
        if not query_vec:
            logger.warning(
                "Moteur d'embedding local indisponible : bascule du flux vectoriel "
                "sur l'approximation lexicale (mode dégradé)",
                extra={"query_len": len(query)},
            )
            return self._stream_vector_lexical_fallback(query)

        results = []
        docs_dir = self.project_path / "docs"
        if docs_dir.exists():
            for f in docs_dir.rglob("*.md"):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                    doc_vec = self._get_or_compute_doc_vector(f, text)
                    if not doc_vec:
                        continue
                    score = cosine_similarity(query_vec, doc_vec)
                    if score <= 0.0:
                        continue
                    text_lower = text.lower()
                    doc_id = str(f.relative_to(self.project_path)).replace("\\", "/")
                    is_stale = (
                        "superseded" in text_lower
                        or "statut : stale" in text_lower
                        or "statut: obsolete" in text_lower
                    )
                    results.append(
                        {
                            "id": doc_id,
                            "title": f.stem,
                            "score_raw": float(score),
                            "is_superseded": is_stale,
                            "stream": "vector",
                        }
                    )
                except Exception as exc:
                    logger.debug(f"Erreur flux vectoriel dense {f}: {exc}", exc_info=True)

        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results

    def _stream_vector_lexical_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Approximation lexicale (Jaccard) utilisée uniquement en mode dégradé,
        lorsque le moteur d'embedding dense local est injoignable."""
        results = []
        q_tokens = set(re.split(r"\W+", query.lower()))
        docs_dir = self.project_path / "docs"
        if docs_dir.exists():
            for f in docs_dir.rglob("*.md"):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore").lower()
                    words = set(re.split(r"\W+", text))
                    intersection = q_tokens.intersection(words)
                    if intersection:
                        jaccard = len(intersection) / len(q_tokens.union(words))
                        doc_id = str(f.relative_to(self.project_path)).replace("\\", "/")
                        is_stale = (
                            "superseded" in text
                            or "statut : stale" in text
                            or "statut: obsolete" in text
                        )
                        results.append(
                            {
                                "id": doc_id,
                                "title": f.stem,
                                "score_raw": float(jaccard),
                                "is_superseded": is_stale,
                                "stream": "vector",
                            }
                        )
                except Exception as exc:
                    logger.debug(f"Erreur vector fallback {f}: {exc}", exc_info=True)

        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results

    def _get_or_compute_doc_vector(self, doc_path: Path, text: str) -> List[float]:
        """Retourne l'embedding dense d'un document, depuis le cache SQLite si l'empreinte
        de contenu est inchangée, sinon le calcule et le met en cache (MLOOP-102-BE)."""
        content_hash = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
        doc_id = str(doc_path.relative_to(self.project_path)).replace("\\", "/")
        try:
            with sqlite3.connect(self._vector_cache_db, timeout=10) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS doc_vector_cache ("
                    "doc_id TEXT PRIMARY KEY, content_hash TEXT NOT NULL, "
                    "embedding_json TEXT NOT NULL, model TEXT NOT NULL)"
                )
                cur = conn.execute(
                    "SELECT content_hash, embedding_json FROM doc_vector_cache WHERE doc_id = ?",
                    (doc_id,),
                )
                row = cur.fetchone()
                if row and row[0] == content_hash:
                    # Cache positif ET négatif : une entrée avec embedding vide "[]"
                    # signifie que ce contenu n'est pas embeddable (ex: dépassement de
                    # fenêtre). On évite ainsi de le ré-essayer à chaque requête.
                    return json.loads(row[1])

                vec = get_embedding(text)
                # On persiste systématiquement le résultat, y compris l'échec (vec vide),
                # pour ne pas relancer un appel réseau coûteux et voué à échouer.
                conn.execute(
                    "INSERT INTO doc_vector_cache (doc_id, content_hash, embedding_json, model) "
                    "VALUES (?, ?, ?, ?) ON CONFLICT(doc_id) DO UPDATE SET "
                    "content_hash=excluded.content_hash, embedding_json=excluded.embedding_json, "
                    "model=excluded.model",
                    (doc_id, content_hash, json.dumps(vec), OLLAMA_EMBED_MODEL),
                )
                return vec
        except Exception as exc:
            logger.debug(f"Cache vectoriel indisponible pour {doc_id}: {exc}", exc_info=True)
            return get_embedding(text)

    def _stream_graph(self, query: str) -> List[Dict[str, Any]]:
        results = []
        q_lower = query.lower()
        candidates = [self.graph_file, self.graphify_file]
        for g_file in candidates:
            if g_file.exists():
                try:
                    data = json.loads(g_file.read_text(encoding="utf-8"))
                    nodes = data.get("nodes", [])
                    if isinstance(nodes, list):
                        for n in nodes:
                            name = str(n.get("name") or n.get("id") or "").lower()
                            if q_lower in name:
                                doc_id = f"graph://{n.get('id', name)}"
                                results.append(
                                    {
                                        "id": doc_id,
                                        "title": n.get("name", name),
                                        "score_raw": 1.0,
                                        "is_superseded": False,
                                        "stream": "graph",
                                    }
                                )
                except Exception as exc:
                    logger.debug(f"Erreur lecture graphe {g_file}: {exc}", exc_info=True)
        results.sort(key=lambda x: x["score_raw"], reverse=True)
        return results

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        t0 = time.perf_counter()
        if not query or not query.strip():
            return {"results": [], "latency_ms": 0.0, "total": 0}

        text_res = self._stream_text(query)
        vector_res = self._stream_vector(query)
        graph_res = self._stream_graph(query)

        # Fusion RRF (Reciprocal Rank Fusion k=60)
        rrf_scores: Dict[str, float] = {}
        matched_streams: Dict[str, set] = {}
        meta_map: Dict[str, Dict[str, Any]] = {}

        streams = [text_res, vector_res, graph_res]
        for s_idx, stream_items in enumerate(streams):
            for rank, item in enumerate(stream_items, 1):
                doc_id = item["id"]
                rrf_increment = 1.0 / (RRF_K + rank)
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_increment
                matched_streams.setdefault(doc_id, set()).add(item["stream"])
                if doc_id not in meta_map:
                    meta_map[doc_id] = item

        # Calcul du score de confiance et pénalisation des supplantés
        final_list = []
        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0
        for doc_id, rrf_val in rrf_scores.items():
            meta = meta_map[doc_id]
            stream_count = len(matched_streams[doc_id])
            # Confiance = corroboration (60%) + intensité RRF (40%)
            confidence = min(1.0, (stream_count / 3.0) * 0.6 + (rrf_val / max_rrf) * 0.4)
            # Règle Métier : Dépriorisation des assertions supplantées (déclassement par facteur 0.1)
            if meta.get("is_superseded"):
                confidence = confidence * 0.1
                rrf_val = rrf_val * 0.1

            final_list.append(
                {
                    "id": doc_id,
                    "title": meta.get("title", doc_id),
                    "confidence": round(confidence, 4),
                    "rrf_score": round(rrf_val, 6),
                    "streams": list(matched_streams[doc_id]),
                    "is_superseded": meta.get("is_superseded", False),
                }
            )

        final_list.sort(
            key=lambda x: (not x["is_superseded"], x["confidence"], x["rrf_score"]), reverse=True
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "results": final_list[:top_k],
            "latency_ms": latency_ms,
            "total": len(final_list),
        }
