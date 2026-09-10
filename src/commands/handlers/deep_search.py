# -*- coding: utf-8 -*-
"""
CLI Handler for 'deep-search' command (mLoop Core - ADR-0335 / ADR-0345).

Orchestre une session de recherche approfondie combinant Fact-Search local,
recherche web multi-fournisseur et aspiration ciblée via WebCrawlerAgent.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Any

from src.cli import ZeroFluffConsole
from src.engine.deep_search.pipeline import run_deep_search
from src.utils.lexicon_resolver import SemanticLexiconResolver


def handle_deep_search(
    args: argparse.Namespace,
    state: Optional[Any] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Handler CLI pour la commande 'deep-search'."""
    query = getattr(args, "query", None)
    if not query or not query.strip():
        ZeroFluffConsole.error("La requête (--query) est obligatoire pour Deep Search.")
        return 1

    project_name = getattr(args, "project", None) or (state.project_name if state else "mLoop")
    canonical_project = SemanticLexiconResolver.resolve_project_alias(project_name) or project_name

    if project_path is None:
        project_path = Path("Projects") / canonical_project

    max_sources = getattr(args, "max_sources", 5) or 5
    depth = getattr(args, "depth", 0) or 0
    render_js = getattr(args, "render_js", False)
    include_superseded = getattr(args, "include_superseded", False)

    try:
        run_deep_search(
            query=query.strip(),
            project_name=canonical_project,
            state=state,
            project_path=project_path,
            max_sources=max_sources,
            depth=depth,
            render_js=render_js,
            include_superseded=include_superseded,
        )
        return 0
    except Exception as e:
        ZeroFluffConsole.error(f"Échec de la session Deep Search: {e}")
        return 1
