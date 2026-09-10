# -*- coding: utf-8 -*-
"""
CLI Handler for 'fact-search' command (mLoop Core - ADR-0326 / ADR-0352).

Exécute une recherche factuelle haute précision dans l'index FTS5 documentaire
avec détection anti-slop, boost de titre et affichage enrichi KWIC.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Any

from src.cli import ZeroFluffConsole
from src.engine.fact_search.retriever import FactSearchRetriever
from src.utils.lexicon_resolver import SemanticLexiconResolver


def handle_fact_search(
    args: argparse.Namespace,
    state: Optional[Any] = None,
    project_path: Optional[Path] = None
) -> int:
    """Handler CLI pour la commande 'fact-search'."""
    query = getattr(args, "query", None)
    if not query or not query.strip():
        ZeroFluffConsole.error("La requête (--query) est obligatoire et ne peut pas être vide.")
        return 1

    project_name = getattr(args, "project", None) or (state.project_name if state else None)
    limit = getattr(args, "limit", 5) or 5
    layer = getattr(args, "layer", None)
    expand_synonyms = not getattr(args, "no_synonyms", False)

    canonical_project = None
    if project_name:
        canonical_project = SemanticLexiconResolver.resolve_project_alias(project_name) or project_name

    include_superseded = getattr(args, "include_superseded", False)

    ZeroFluffConsole.section(f"FACT-SEARCH FTS5 — RECHERCHE FACTUELLE ({canonical_project or 'GLOBAL'})")
    ZeroFluffConsole.value("Requête", query)
    if layer:
        ZeroFluffConsole.value("Filtre Couche", layer)
    ZeroFluffConsole.value("Synonymes", "Activés" if expand_synonyms else "Désactivés")
    if include_superseded:
        ZeroFluffConsole.warning("Mode Superseded Actif : Les documents caducs sont inclus avec pénalité.")

    results = FactSearchRetriever.search(
        query=query,
        project_name=canonical_project,
        expand_synonyms=expand_synonyms,
        limit=limit,
        log_audit=True,
        layer=layer,
        include_superseded=include_superseded,
    )

    flight_record = FactSearchRetriever.get_last_flight_record() or {}
    admission = flight_record.get("admission_of_limits", "")
    rejected = flight_record.get("rejected", [])

    if not results:
        ZeroFluffConsole.warning(f"Aucun fait probant trouvé pour la requête '{query}'.")
        print("\n" + "─" * 65)
        print("⚠️  LIMITES DE PREUVE (ADMISSION OF LIMITS) :")
        print(f"   • {admission}")
        print("─" * 65 + "\n")
        return 0

    print(f"\n🔍 {len(results)} fait(s) probant(s) extrait(s) :")
    for idx, item in enumerate(results, 1):
        substantive_tag = " [Substantif]" if item.get("is_substantive", True) else " [Faible densité]"
        print(f"\n[{idx}] {item.get('breadcrumb', 'Document')}{substantive_tag}")
        print(f"    • Score FTS5 : {item.get('relevance_score', 0.0):.3f} | Couche : {item.get('ssot_layer', 'inconnue')}")
        print(f"    • Source    : {item.get('doc_path', '')} (L{item.get('line_start')}-L{item.get('line_end')})")
        
        snippet = item.get("snippet", "").strip()
        if snippet:
            indented = "\n".join(f"      │ {line}" for line in snippet.splitlines())
            print(f"    • Extrait KWIC :\n{indented}")

    # Section Admission of Limits (ADR-0353 - The New Stack)
    print("\n" + "─" * 65)
    print("⚠️  LIMITES DE PREUVE & CONFIANCE (ADMISSION OF LIMITS) :")
    print(f"   • Synthèse : {admission}")

    superseded_rejections = [r for r in rejected if "REJECTED_SUPERSEDED" in r.get("reason", "")]
    slop_rejections = [r for r in rejected if "REJECTED_LOW_SUBSTANCE" in r.get("reason", "")]

    if superseded_rejections:
        print(f"   • Documents caducs écartés (Option A Fail-Safe) : {len(superseded_rejections)}")
        for s in superseded_rejections[:3]:
            print(f"     ➔ {s.get('breadcrumb')} ({s.get('reason')})")
    if slop_rejections:
        print(f"   • Extraits à faible densité filtrés (Anti-Slop) : {len(slop_rejections)}")
    print("─" * 65 + "\n")

    ZeroFluffConsole.success(f"{len(results)} preuve(s) documentaire(s) récupérée(s).")
    return 0
