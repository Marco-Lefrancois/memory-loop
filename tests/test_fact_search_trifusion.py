# -*- coding: utf-8 -*-
"""
Tests unitaires pour le Moteur Fact-Search 2.0 Tri-Fusion (DocETL + Anthropic + Late Chunking).
"""

import pytest
import tempfile
from pathlib import Path

from src.engine.fact_search.contextualizer import DocumentContextualizer
from src.engine.fact_search.chunker import TriFusionChunker, TriFusionChunk
from src.engine.fact_search.indexer import FactSearchIndexer
from src.engine.fact_search.retriever import FactSearchRetriever
from src.engine.fact_search.coverage import FactSearchCoverageEvaluator


def test_contextualizer_prefix_generation():
    """Vérifie la génération du préfixe contextuel Anthropic."""
    prefix = DocumentContextualizer.generate_context_prefix(
        doc_path="docs/02-business-rules/RM-042_Cart_Timeout.md",
        h1_title="RM-042 : Règle d'Expiration des Paniers",
        h2_title="Spécification de la Durée",
        summary="Règle régissant l'expiration automatique des paniers d'achat après 15 minutes."
    )
    assert "[CONTEXT:" in prefix
    assert "Doc=RM-042_Cart_Timeout.md" in prefix
    assert "Couche=Règles Métier" in prefix
    assert "Section=" in prefix
    assert "Synthèse=" in prefix


def test_trifusion_chunker_preserves_tables_and_code():
    """Vérifie que TriFusionChunker préserve l'atomicité des tableaux et blocs de code Markdown."""
    doc_content = """# Architecture Système

Introduction générale au système de commande.

## Matrice des Devises
| Code | Nom Devise | Symbole | Taux Actif |
|---|---|---|---|
| CAD | Dollar Canadien | $ | Oui |
| USD | Dollar US | $ | Oui |
| EUR | Euro | € | Non |

## Bloc de Configuration
```json
{
  "cart_timeout_seconds": 900,
  "retry_attempts": 3
}
```

Fin de la spécification.
"""
    chunker = TriFusionChunker()
    chunks = chunker.chunk_document(
        doc_path="docs/01-architecture/specs.md",
        content=doc_content,
        ssot_layer="01-architecture",
    )

    assert len(chunks) >= 2
    
    # Vérifier la présence d'un chunk de type table
    table_chunks = [c for c in chunks if c.chunk_type == "table"]
    assert len(table_chunks) == 1
    assert "| CAD | Dollar Canadien |" in table_chunks[0].content
    assert "| EUR | Euro |" in table_chunks[0].content

    # Vérifier la présence d'un chunk de type code
    code_chunks = [c for c in chunks if c.chunk_type == "code"]
    assert len(code_chunks) == 1
    assert "cart_timeout_seconds" in code_chunks[0].content

    # Vérifier l'injection du préfixe Anthropic sur chaque chunk
    for c in chunks:
        assert c.contextual_content.startswith("[CONTEXT:")


def test_kwic_snippet_centering():
    """Vérifie que la fonction KWIC extrait un extrait centré sur le terme cible."""
    long_text = """Ligne 1 : Préambule d'introduction.
Ligne 2 : Détail mineur sur le système.
Ligne 3 : Informations complémentaires.
Ligne 4 : Le panier d'achat expire impérativement après 15 minutes d'inactivité.
Ligne 5 : Les stocks sont alors immédiatement libérés.
Ligne 6 : Notification envoyée au client.
Ligne 7 : Conclusion et archivage de session."""

    snippet, offset = FactSearchRetriever.generate_kwic_snippet(
        text=long_text,
        target_words=["expire", "15", "minutes"],
    )

    assert "expire impérativement après 15 minutes" in snippet
    assert offset >= 1


def test_fact_search_e2e_lifecycle(tmp_path):
    """Test de cycle de vie complet : Indexation Tri-Fusion -> Recherche KWIC -> Couverture Story."""
    test_db = tmp_path / "test_fact_search.db"
    project_name = "TestProject_TriFusion"
    docs_dir = tmp_path / "Projects" / project_name / "docs"
    
    # Créer documents
    rm_dir = docs_dir / "02-business-rules"
    rm_dir.mkdir(parents=True, exist_ok=True)
    
    (rm_dir / "RM-099_Discount.md").write_text(
        "# RM-099 : Règle de Rabais Fidélité\n\n"
        "## Seuil d'Application\n"
        "Tout client possédant plus de 500 points fidélité bénéficie d'un rabais automatique de 10% sur sa commande.\n"
        "Le rabais s'applique exclusivement aux articles non promotionnels.\n",
        encoding="utf-8"
    )

    # 1. Indexation
    indexed = FactSearchIndexer.index_project_docs(
        project_name=project_name,
        docs_dir=docs_dir,
        db_path=test_db,
    )
    assert indexed > 0

    # 2. Recherche
    results = FactSearchRetriever.search(
        query="rabais fidélité 500 points",
        project_name=project_name,
        db_path=test_db,
        log_audit=False,
    )
    assert len(results) > 0
    assert "RM-099" in results[0]["breadcrumb"]
    assert "500 points" in results[0]["snippet"]
    assert results[0]["relevance_score"] > 0.5

    # 3. Couverture de Story
    story_file = tmp_path / "US-099.md"
    story_file.write_text(
        "---\nid: US-099\ntitle: Application du rabais fidélité\n---\n\n"
        "# Application du rabais fidélité\n\n"
        "## Scénarios de test\n"
        "- Un client avec 500 points obtient un rabais de 10% selon RM-099.\n"
        "- Une commande sans points fidélité ne reçoit aucun rabais.\n",
        encoding="utf-8"
    )

    coverage = FactSearchCoverageEvaluator.evaluate_story_coverage(
        story_path=story_file,
        project_name=project_name,
        db_path=test_db,
    )

    assert coverage["total_criteria"] == 2
    assert coverage["coverage_ratio"] >= 0.5
    assert len(coverage["proofs"]) == 2
    assert coverage["proofs"][0]["status"] == "COVERED"
    assert coverage["proofs"][0]["line_range"] is not None
