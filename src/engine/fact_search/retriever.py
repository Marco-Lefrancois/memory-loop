# -*- coding: utf-8 -*-
"""
Fact-Search Retriever Engine (mLoop Core - ADR-0326).

Recherche hybride plein texte FTS5 avec :
1. Expansion synonymique automatique via project_lexicon.
2. Requêtes structurées par proximité (NEAR) et dé-bruitage.
3. Scoring BM25 pondéré par couche SSOT.
4. Génération de snippets KWIC (Keyword-In-Context) centrés sur les faits.
5. Journalisation d'audit append-only.
"""

from __future__ import annotations

import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.loop_mem.db import get_observation_db_session, search_lexicon_terms
from src.utils.logger import get_logger

logger = get_logger("fact_search.retriever")

LAYER_WEIGHTS = {
    "02-business-rules": 1.3,
    "01-architecture": 1.2,
    "03-models": 1.1,
    "06-knowledge": 1.0,
    "00-ingested": 0.9,
    "05-assets": 0.8,
}

FRENCH_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "en", "dans", "pour",
    "par", "sur", "avec", "sans", "est", "sont", "ete", "etre", "avoir", "fait",
    "qui", "que", "quoi", "dont", "ou", "mais", "donc", "or", "ni", "car",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
    "nous", "vous", "ils", "elles", "au", "aux", "tout", "tous", "toute", "toutes"
}


class FactSearchRetriever:
    """Moteur de recherche et d'extraction KWIC Fact-Search."""

    @classmethod
    def search(
        cls,
        query: str,
        project_name: Optional[str] = None,
        expand_synonyms: bool = True,
        limit: int = 10,
        log_audit: bool = True,
        db_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Exécute une recherche factuelle avec expansion et scoring BM25."""
        clean_words = [
            w for w in re.findall(r'\w+', query.lower())
            if len(w) > 2 and w not in FRENCH_STOPWORDS
        ]
        if not clean_words:
            # Fallback si tous les mots étaient filtrés
            clean_words = [w for w in re.findall(r'\w+', query.lower()) if len(w) > 1]
            if not clean_words:
                return []

        # 1. Expansion lexicale contextuelle
        expanded_terms = set(clean_words)
        if expand_synonyms:
            for w in clean_words:
                try:
                    lex_matches = search_lexicon_terms(w, project_name=project_name, limit=3)
                    for m in lex_matches:
                        term_words = re.findall(r'\w+', m.get("term", "").lower())
                        expanded_terms.update([tw for tw in term_words if len(tw) > 2 and tw not in FRENCH_STOPWORDS])
                        for alias in m.get("aliases", []):
                            alias_words = re.findall(r'\w+', alias.lower())
                            expanded_terms.update([aw for aw in alias_words if len(aw) > 2 and aw not in FRENCH_STOPWORDS])
                except Exception as e:
                    logger.debug(f"Erreur expansion synonymique pour '{w}': {e}")

        fts_expression = cls._build_fts_query(clean_words, expanded_terms)

        results: List[Dict[str, Any]] = []
        session_kwargs = {"db_path": db_path} if db_path else {}
        
        with get_observation_db_session(**session_kwargs) as conn:
            cursor = conn.cursor()

            sql = """
                SELECT c.id, c.project_name, c.doc_path, c.ssot_layer, c.section_h1, c.section_h2,
                       c.breadcrumb, c.line_start, c.line_end, c.content,
                       bm25(docs_chunks_fts) as rank
                FROM docs_chunks_fts f
                JOIN docs_chunks c ON c.id = CAST(f.chunk_id AS INTEGER)
                WHERE docs_chunks_fts MATCH ?
            """
            params = [fts_expression]
            if project_name:
                sql += " AND f.project_name = ?"
                params.append(project_name)

            sql += " ORDER BY rank ASC LIMIT ?"
            params.append(limit * 3)

            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                # Fallback FTS5 si la requête structurée échoue
                fallback_expr = " OR ".join([f"{t}*" for t in list(expanded_terms)[:6]])
                params[0] = fallback_expr
                try:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                except Exception:
                    rows = []

            for row in rows:
                layer = row["ssot_layer"]
                weight = LAYER_WEIGHTS.get(layer, 0.7)
                raw_bm25 = float(row["rank"]) if row["rank"] is not None else 1.0
                bm25_magnitude = abs(raw_bm25) if abs(raw_bm25) > 0.05 else 1.0
                normalized_relevance = round(bm25_magnitude * weight, 3)

                content_text = row["content"] or ""
                # Génération du snippet KWIC centré sur le terme trouvé
                kwic_snippet, match_line_offset = cls.generate_kwic_snippet(content_text, list(expanded_terms))

                actual_start = row["line_start"] + match_line_offset if row["line_start"] else 1
                actual_end = min(actual_start + 10, row["line_end"] or actual_start + 10)

                results.append({
                    "chunk_id": row["id"],
                    "project_name": row["project_name"],
                    "doc_path": row["doc_path"],
                    "ssot_layer": layer,
                    "breadcrumb": row["breadcrumb"],
                    "line_start": actual_start,
                    "line_end": actual_end,
                    "snippet": kwic_snippet,
                    "relevance_score": normalized_relevance,
                })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        final_results = results[:limit]

        # 3. Journalisation d'audit append-only
        if log_audit:
            cls._log_search_audit(query, expanded_terms, project_name, final_results)

        return final_results

    @classmethod
    def _build_fts_query(cls, clean_words: List[str], expanded_terms: set) -> str:
        """Construit une expression FTS5 équilibrée entre précision et rappel."""
        if len(clean_words) >= 2:
            near_clause = f'NEAR({" ".join(clean_words[:3])}, 15)'
            or_terms = " OR ".join([f"{t}*" for t in list(expanded_terms)[:8]])
            return f"({near_clause}) OR ({or_terms})"
        return " OR ".join([f"{t}*" for t in list(expanded_terms)[:10]])

    @classmethod
    def generate_kwic_snippet(
        cls,
        text: str,
        target_words: List[str],
        window_words: int = 35,
    ) -> tuple[str, int]:
        """
        Extrait un snippet Keyword-In-Context (KWIC) centré sur la première occurrence.
        Retourne (snippet_text, approx_line_offset).
        """
        if not text:
            return ("", 0)

        lines = text.splitlines()
        # Chercher la première ligne contenant l'un des mots-clés
        matched_line_idx = 0
        pattern = re.compile(r'\b(' + '|'.join(re.escape(w) for w in target_words if len(w) > 1) + r')', re.IGNORECASE)

        for idx, line in enumerate(lines):
            if pattern.search(line):
                matched_line_idx = idx
                break

        # Extraire le contexte autour de la ligne matchée
        start_idx = max(0, matched_line_idx - 2)
        end_idx = min(len(lines), matched_line_idx + 4)
        snippet_lines = lines[start_idx:end_idx]

        snippet_text = "\n".join(snippet_lines).strip()
        if start_idx > 0:
            snippet_text = "... " + snippet_text
        if end_idx < len(lines):
            snippet_text = snippet_text + " ..."

        return (snippet_text[:350], start_idx)

    @classmethod
    def _log_search_audit(cls, query: str, expanded_terms: set, project_name: Optional[str], results: List[Dict]):
        """Écrit un événement d'audit dans fact_search_log.jsonl."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "expanded_terms": list(expanded_terms),
            "project_name": project_name or "global",
            "matches_count": len(results),
            "top_match": results[0]["breadcrumb"] if results else None,
        }
        log_paths = [Path("memory/fact_search_log.jsonl")]
        if project_name and (Path("Projects") / project_name).exists():
            log_paths.append(Path("Projects") / project_name / "memory" / "fact_search_log.jsonl")

        for lp in log_paths:
            try:
                lp.parent.mkdir(parents=True, exist_ok=True)
                with open(lp, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            except Exception:
                pass
