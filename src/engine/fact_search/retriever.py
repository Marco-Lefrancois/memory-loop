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
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "du",
    "de",
    "d",
    "en",
    "dans",
    "pour",
    "par",
    "sur",
    "avec",
    "sans",
    "est",
    "sont",
    "ete",
    "etre",
    "avoir",
    "fait",
    "qui",
    "que",
    "quoi",
    "dont",
    "ou",
    "mais",
    "donc",
    "or",
    "ni",
    "car",
    "ce",
    "cet",
    "cette",
    "ces",
    "mon",
    "ton",
    "son",
    "notre",
    "votre",
    "leur",
    "nous",
    "vous",
    "ils",
    "elles",
    "au",
    "aux",
    "tout",
    "tous",
    "toute",
    "toutes",
}

TEMPORAL_KEYWORDS = {
    "date",
    "dates",
    "récent",
    "récente",
    "récents",
    "récentes",
    "dernier",
    "dernière",
    "derniers",
    "dernières",
    "chronologie",
    "historique",
    "évolution",
    "recent",
    "latest",
    "timeline",
    "décision",
    "décisions",
    "arbitrage",
    "arbitrages",
    "réunion",
    "réunions",
    "meeting",
    "compte-rendu",
    "cr",
    "atelier",
    "statut",
    "validé",
    "approuvé",
    "accord",
    "revue",
    "sprint",
    "jalon",
    "milestone",
    "decision",
    "review",
    "kickoff",
    "échéance",
    "echeance",
}

MONTH_NAMES_FR_EN = {
    "janvier",
    "fevrier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
    "décembre",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}

_DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(
        r"\b\d{1,2}\s+(?:" + "|".join(MONTH_NAMES_FR_EN) + r")(?:\s+\d{4})?\b", re.IGNORECASE
    ),
]


class FactSearchRetriever:
    """Moteur de recherche et d'extraction KWIC Fact-Search."""

    _last_flight_record: Optional[Dict[str, Any]] = None

    @classmethod
    def get_last_flight_record(cls) -> Optional[Dict[str, Any]]:
        """Retourne le dernier enregistrement de vol (Flight Recorder) généré."""
        return cls._last_flight_record

    @classmethod
    def is_substantive_snippet(cls, snippet: str) -> bool:
        """
        Vérifie si un extrait contient une densité sémantique suffisante (anti-slop).
        Élimine les sommaires vides, en-têtes isolés, et fragments de moins de 6 mots substantifs.
        """
        if not snippet:
            return False
        cleaned = re.sub(r"[#*\-_`|\[\]()]+", " ", snippet)
        cleaned = cleaned.replace("...", " ").strip()
        words = [
            w
            for w in re.findall(r"\b\w+\b", cleaned.lower())
            if len(w) > 2 and w not in FRENCH_STOPWORDS and not w.isdigit()
        ]
        if len(words) < 6:
            return False
        lower_cleaned = cleaned.lower()
        if (
            "table des matieres" in lower_cleaned
            or "sommaire" in lower_cleaned
            or "table of contents" in lower_cleaned
        ) and len(words) < 12:
            return False
        return True

    @classmethod
    def check_supersession(
        cls,
        doc_path: str,
        breadcrumb: str,
        project_name: Optional[str] = None,
        content: str = "",
        db_path: Optional[Path] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie si un document ou une règle est obsolète/remplacée (ADR-0353).
        Consulte le registre de supersession et les métadonnées de frontmatter.
        """
        # 1. Vérification directe dans le contenu / frontmatter
        if re.search(r"(?i)\bstatus\s*:\s*(SUPERSEDED|DEPRECATED)\b", content):
            rep_match = re.search(
                r"(?i)(?:superseded by|remplacé par)\s*:?\s*\[?([A-Z0-9_\-]+)\]?", content
            )
            return {
                "target_id": Path(doc_path).stem,
                "superseded_by": rep_match.group(1) if rep_match else "DOCUMENT_CADUC",
                "reason": "Statut SUPERSEDED ou DEPRECATED explicite dans l'en-tête du document",
            }

        # 2. Extraction des identifiants (ADR-XXX, RM-XXX)
        combined = f"{doc_path} {breadcrumb}"
        identifiers = set(re.findall(r"\b(ADR-\d+|RM-\d+)\b", combined, re.IGNORECASE))
        filename = Path(doc_path).name
        m = re.search(r"(\d{4})", filename)
        if m:
            identifiers.add(f"ADR-{m.group(1)}")
            identifiers.add(f"ADR-{int(m.group(1))}")

        ledgers = []
        if db_path:
            db_path_obj = Path(db_path)
            if project_name:
                ledgers.append(
                    db_path_obj.parent.parent
                    / "Projects"
                    / project_name
                    / "memory"
                    / "supersession_ledger.json"
                )
            ledgers.append(db_path_obj.parent / "supersession_ledger.json")

        if project_name and (Path("Projects") / project_name).exists():
            ledgers.append(Path("Projects") / project_name / "memory" / "supersession_ledger.json")
        ledgers.append(Path("memory/supersession_ledger.json"))

        for ledger_file in ledgers:
            if ledger_file.exists():
                try:
                    data = json.loads(ledger_file.read_text(encoding="utf-8"))
                    items = data.get("superseded_items", {})
                    for ident in identifiers:
                        norm_id = ident.upper()
                        if norm_id in items:
                            return items[norm_id]
                except Exception as e:
                    logger.debug(
                        "Lecture d'un ledger de supersession échouée, ledger suivant essayé",
                        exc_info=True,
                        extra={
                            "component": "fact_search.retriever",
                            "operation": "_lookup_supersession",
                            "ledger_file": str(ledger_file),
                            "error": str(e),
                        },
                    )
        return None

    @classmethod
    def calculate_temporal_boost(
        cls,
        query: str,
        content: str,
        breadcrumb: str = "",
        section_h1: str = "",
        doc_path: str = "",
    ) -> float:
        """
        Calcule un boost de pertinence temporel et décisionnel (ADR-0326 / Quick Win Kwipu).
        Si la requête recherche une date, un compte-rendu, une décision ou un arbitrage récent,
        et que le document/chunk correspond, applique jusqu'à +30% (+35% sur date exacte).
        """
        q_lower = query.lower()
        q_tokens = set(re.findall(r"\b\w+\b", q_lower))

        # 1. Extraire les dates explicites de la requête
        query_dates = []
        for pat in _DATE_PATTERNS:
            query_dates.extend(pat.findall(q_lower))

        has_temporal_intent = bool(query_dates) or bool(TEMPORAL_KEYWORDS.intersection(q_tokens))
        if not has_temporal_intent:
            return 1.0

        target_context = f"{doc_path} {breadcrumb} {section_h1} {content}".lower()

        # 2. Correspondance exacte de date (+35%)
        for dt in query_dates:
            if dt in target_context:
                return 1.35

        # 3. Correspondance d'événements décisionnels récents (+30%)
        is_meeting_or_decision_doc = any(
            k in target_context
            for k in (
                "compte-rendu",
                "réunion",
                "reunion",
                "meeting",
                "atelier",
                "décision",
                "decision",
                "arbitrage",
                "sprint review",
                "kickoff",
            )
        )
        has_dates_in_chunk = any(pat.search(target_context) for pat in _DATE_PATTERNS)

        if is_meeting_or_decision_doc and has_dates_in_chunk:
            return 1.30
        elif is_meeting_or_decision_doc or has_dates_in_chunk:
            return 1.15

        return 1.0

    @classmethod
    def search(
        cls,
        query: str,
        project_name: Optional[str] = None,
        expand_synonyms: bool = True,
        limit: int = 10,
        log_audit: bool = True,
        db_path: Optional[Path] = None,
        layer: Optional[str] = None,
        include_superseded: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Exécute une recherche factuelle avec expansion, scoring BM25 pondéré,
        filtrage de supersession (Option A) et enregistreur de vol (ADR-0353).
        """
        clean_words = [
            w for w in re.findall(r"\w+", query.lower()) if len(w) > 2 and w not in FRENCH_STOPWORDS
        ]
        if not clean_words:
            # Fallback si tous les mots étaient filtrés
            clean_words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 1]
            if not clean_words:
                return []

        # 1. Expansion lexicale contextuelle
        expanded_terms = set(clean_words)
        if expand_synonyms:
            for w in clean_words:
                try:
                    lex_matches = search_lexicon_terms(w, project_name=project_name, limit=3)
                    for m in lex_matches:
                        term_words = re.findall(r"\w+", m.get("term", "").lower())
                        expanded_terms.update(
                            [tw for tw in term_words if len(tw) > 2 and tw not in FRENCH_STOPWORDS]
                        )
                        for alias in m.get("aliases", []):
                            alias_words = re.findall(r"\w+", alias.lower())
                            expanded_terms.update(
                                [
                                    aw
                                    for aw in alias_words
                                    if len(aw) > 2 and aw not in FRENCH_STOPWORDS
                                ]
                            )
                except Exception as e:
                    logger.debug(f"Erreur expansion synonymique pour '{w}': {e}")

        fts_expression = cls._build_fts_query(clean_words, expanded_terms)

        results: List[Dict[str, Any]] = []
        rejected_candidates: List[Dict[str, Any]] = []
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
            params: list = [fts_expression]
            if project_name:
                sql += " AND f.project_name = ?"
                params.append(project_name)
            if layer:
                sql += " AND c.ssot_layer = ?"
                params.append(layer)

            sql += " ORDER BY rank ASC LIMIT ?"
            params.append(limit * 3)

            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                fallback_expr = " OR ".join([f"{t}*" for t in list(expanded_terms)[:6]])
                params[0] = fallback_expr
                try:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                except Exception:
                    rows = []

            for row in rows:
                row_layer = row["ssot_layer"]
                weight = LAYER_WEIGHTS.get(row_layer, 0.7)
                raw_bm25 = float(row["rank"]) if row["rank"] is not None else 1.0
                bm25_magnitude = abs(raw_bm25) if abs(raw_bm25) > 0.05 else 1.0

                content_text = row["content"] or ""

                # 2. Filtrage de Supersession (ADR-0353 - Option A Fail-Safe)
                superseded_info = cls.check_supersession(
                    doc_path=row["doc_path"] or "",
                    breadcrumb=row["breadcrumb"] or "",
                    project_name=project_name,
                    content=content_text,
                    db_path=db_path,
                )

                if superseded_info and not include_superseded:
                    superseded_by = superseded_info.get("superseded_by", "inconnu")
                    rejected_candidates.append(
                        {
                            "chunk_id": row["id"],
                            "breadcrumb": row["breadcrumb"],
                            "doc_path": row["doc_path"],
                            "relevance_score": round(bm25_magnitude * weight, 3),
                            "reason": f"REJECTED_SUPERSEDED: Document caduc, remplacé par {superseded_by}",
                        }
                    )
                    continue

                supersession_penalty = 0.2 if (superseded_info and include_superseded) else 1.0

                # 3. Multiplicateur d'autorité pour les sources maîtresses actives
                is_authoritative = (
                    row_layer in ("01-architecture", "02-business-rules") and not superseded_info
                )
                authority_boost = 1.25 if is_authoritative else 1.0

                # Génération du snippet KWIC centré sur le terme trouvé
                kwic_snippet, match_line_offset = cls.generate_kwic_snippet(
                    content_text, list(expanded_terms)
                )

                # Boost Titre & Breadcrumb (+35%)
                header_context = f"{row['breadcrumb'] or ''} {row['section_h1'] or ''} {row['section_h2'] or ''}".lower()
                has_title_match = any(w.lower() in header_context for w in clean_words)
                title_boost = 1.35 if has_title_match else 1.0

                # Anti-slop : qualification de substance du snippet
                is_sub = cls.is_substantive_snippet(kwic_snippet)
                substance_factor = 1.0 if is_sub else 0.5

                # Boost Temporel & Décisionnel (+30% max - Quick Win Kwipu)
                temporal_boost = cls.calculate_temporal_boost(
                    query=query,
                    content=content_text,
                    breadcrumb=row["breadcrumb"] or "",
                    section_h1=row["section_h1"] or "",
                    doc_path=row["doc_path"] or "",
                )

                normalized_relevance = round(
                    bm25_magnitude
                    * weight
                    * title_boost
                    * substance_factor
                    * supersession_penalty
                    * authority_boost
                    * temporal_boost,
                    3,
                )

                actual_start = row["line_start"] + match_line_offset if row["line_start"] else 1
                actual_end = min(actual_start + 10, row["line_end"] or actual_start + 10)

                breadcrumb_display = row["breadcrumb"] or ""
                if superseded_info and include_superseded:
                    breadcrumb_display += f" [SUPERSEDED by {superseded_info.get('superseded_by')}]"

                results.append(
                    {
                        "chunk_id": row["id"],
                        "project_name": row["project_name"],
                        "doc_path": row["doc_path"],
                        "ssot_layer": row_layer,
                        "breadcrumb": breadcrumb_display,
                        "section_h1": row["section_h1"],
                        "section_h2": row["section_h2"],
                        "line_start": actual_start,
                        "line_end": actual_end,
                        "snippet": kwic_snippet,
                        "is_substantive": is_sub,
                        "superseded_info": superseded_info,
                        "temporal_boost": temporal_boost,
                        "relevance_score": normalized_relevance,
                    }
                )

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        substantive_results = [r for r in results if r.get("is_substantive", True)]

        if substantive_results:
            for r in results:
                if not r.get("is_substantive", True):
                    rejected_candidates.append(
                        {
                            "chunk_id": r["chunk_id"],
                            "breadcrumb": r["breadcrumb"],
                            "doc_path": r["doc_path"],
                            "relevance_score": r["relevance_score"],
                            "reason": "REJECTED_LOW_SUBSTANCE: Densité sémantique insuffisante (< 6 mots ou en-tête seul)",
                        }
                    )
            accepted_pool = substantive_results
        else:
            accepted_pool = results

        final_results = accepted_pool[:limit]

        for r in accepted_pool[limit:]:
            rejected_candidates.append(
                {
                    "chunk_id": r["chunk_id"],
                    "breadcrumb": r["breadcrumb"],
                    "doc_path": r["doc_path"],
                    "relevance_score": r["relevance_score"],
                    "reason": "REJECTED_RANKING_LIMIT: Score inférieur au seuil top-k",
                }
            )

        # 4. Décision d'Enregistreur de Vol & Aveu des Limites (ADR-0353)
        if len(final_results) >= 2 and any(r["relevance_score"] >= 2.0 for r in final_results):
            decision = "SUFFICIENT_EVIDENCE"
            admission_of_limits = f"Preuves suffisantes : {len(final_results)} fait(s) substantif(s) recoupé(s) dans le SSOT documentaire."
        elif len(final_results) > 0:
            decision = "PARTIAL_EVIDENCE"
            admission_of_limits = f"Preuves partielles : {len(final_results)} fait(s) trouvé(s), mais certains aspects demeurent incertains et nécessitent validation HITL."
        else:
            decision = "UNVERIFIED"
            admission_of_limits = f"Non vérifié : Aucun fait probant trouvé dans le SSOT documentaire pour la requête '{query}'. Confirmation humaine requise."

        flight_record = {
            "timestamp": datetime.now().isoformat(),
            "request": query,
            "clean_words": clean_words,
            "expanded_terms": list(expanded_terms),
            "project_name": project_name or "global",
            "layer_filter": layer,
            "accepted": [
                {
                    "chunk_id": r["chunk_id"],
                    "breadcrumb": r["breadcrumb"],
                    "doc_path": r["doc_path"],
                    "score": r["relevance_score"],
                    "layer": r["ssot_layer"],
                    "line_range": f"L{r['line_start']}-L{r['line_end']}",
                }
                for r in final_results
            ],
            "rejected": rejected_candidates,
            "decision": decision,
            "admission_of_limits": admission_of_limits,
        }

        cls._last_flight_record = flight_record

        # 5. Journalisation d'audit append-only
        if log_audit:
            cls._log_search_audit(flight_record, project_name)

        return final_results

    @classmethod
    def _build_fts_query(cls, clean_words: List[str], expanded_terms: set) -> str:
        """Construit une expression FTS5 équilibrée entre précision et rappel."""
        if len(clean_words) >= 2:
            near_clause = f"NEAR({' '.join(clean_words[:3])}, 15)"
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
        Extrait un snippet Keyword-In-Context (KWIC) centré sur l'occurrence la plus informative.
        Retourne (snippet_text, approx_line_offset).
        """
        if not text:
            return ("", 0)

        lines = text.splitlines()
        if not lines:
            return ("", 0)

        pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in target_words if len(w) > 1) + r")",
            re.IGNORECASE,
        )

        # Chercher les indices des lignes qui matchent
        candidate_indices = [idx for idx, line in enumerate(lines) if pattern.search(line)]
        if not candidate_indices:
            candidate_indices = [0]

        # Préférer une ligne avec du contenu narratif plutôt qu'uniquement un titre ou une puce
        best_idx = candidate_indices[0]
        for idx in candidate_indices:
            l = lines[idx].strip()
            if (
                not l.startswith("#")
                and not re.match(r"^[*-]\s+\[.*?\]\(.*?\)", l)
                and len(l.split()) >= 4
            ):
                best_idx = idx
                break

        start_idx = max(0, best_idx - 2)
        end_idx = min(len(lines), best_idx + 4)
        snippet_lines = lines[start_idx:end_idx]

        snippet_text = "\n".join(snippet_lines).strip()
        if start_idx > 0:
            snippet_text = "... " + snippet_text
        if end_idx < len(lines):
            snippet_text = snippet_text + " ..."

        return (snippet_text[:350], start_idx)

    @classmethod
    def _log_search_audit(cls, flight_record: Dict[str, Any], project_name: Optional[str] = None):
        """Écrit l'enregistrement de vol structuré (Flight Recorder) dans fact_search_log.jsonl."""
        log_paths = [Path("memory/fact_search_log.jsonl")]
        if project_name and (Path("Projects") / project_name).exists():
            log_paths.append(Path("Projects") / project_name / "memory" / "fact_search_log.jsonl")

        for lp in log_paths:
            try:
                lp.parent.mkdir(parents=True, exist_ok=True)
                with open(lp, "a", encoding="utf-8") as f:
                    f.write(json.dumps(flight_record, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.warning(
                    "Écriture du Flight Recorder échouée, traçabilité fact-search partielle",
                    exc_info=True,
                    extra={
                        "component": "fact_search.retriever",
                        "operation": "record_flight",
                        "log_path": str(lp),
                        "error": str(e),
                    },
                )
