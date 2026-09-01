# -*- coding: utf-8 -*-
"""
Fact-Search 2.0 Engine (mLoop Core - Tri-Fusion Architecture).

Expose les interfaces publiques d'indexation, de recherche hybride KWIC
et d'évaluation de conformité factuelle des récits.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any

from src.engine.fact_search.contextualizer import DocumentContextualizer
from src.engine.fact_search.chunker import TriFusionChunker, TriFusionChunk
from src.engine.fact_search.indexer import FactSearchIndexer
from src.engine.fact_search.retriever import FactSearchRetriever
from src.engine.fact_search.coverage import FactSearchCoverageEvaluator


def index_project_docs_to_fts5(
    project_name: str,
    docs_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Interface canonique d'indexation documentaire dans SQLite FTS5."""
    return FactSearchIndexer.index_project_docs(
        project_name=project_name,
        docs_dir=docs_dir,
        db_path=db_path,
    )


def fact_search_query(
    query: str,
    project_name: Optional[str] = None,
    expand_synonyms: bool = True,
    limit: int = 10,
    log_audit: bool = True,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Interface canonique de recherche plein texte et d'extraction KWIC."""
    return FactSearchRetriever.search(
        query=query,
        project_name=project_name,
        expand_synonyms=expand_synonyms,
        limit=limit,
        log_audit=log_audit,
        db_path=db_path,
    )


def calculate_story_fact_coverage(
    story_path: Path | str,
    project_name: str,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Interface canonique d'évaluation de la couverture factuelle d'un récit."""
    return FactSearchCoverageEvaluator.evaluate_story_coverage(
        story_path=story_path,
        project_name=project_name,
        db_path=db_path,
    )


__all__ = [
    "index_project_docs_to_fts5",
    "fact_search_query",
    "calculate_story_fact_coverage",
    "FactSearchIndexer",
    "FactSearchRetriever",
    "FactSearchCoverageEvaluator",
    "TriFusionChunker",
    "TriFusionChunk",
    "DocumentContextualizer",
]
