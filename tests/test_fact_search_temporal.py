# -*- coding: utf-8 -*-
from pathlib import Path
import pytest

from src.engine.fact_search.retriever import FactSearchRetriever
from src.engine.fact_search.indexer import FactSearchIndexer


def test_calculate_temporal_boost_unit():
    # 1. Requête sans intention temporelle -> 1.0
    boost = FactSearchRetriever.calculate_temporal_boost(
        query="comment fonctionne l'authentification OAuth ?",
        content="Le système utilise OAuth 2.0 avec jetons JWT.",
    )
    assert boost == 1.0

    # 2. Requête avec intention décisionnelle + compte-rendu daté -> 1.30
    boost_decision = FactSearchRetriever.calculate_temporal_boost(
        query="quelles sont les décisions de la réunion sur l'architecture ?",
        content="Compte-rendu du 2025-01-15 : Décision validée d'utiliser PostgreSQL.",
        breadcrumb="Réunion Architecture",
    )
    assert boost_decision == 1.30

    # 3. Requête avec date exacte -> 1.35
    boost_date = FactSearchRetriever.calculate_temporal_boost(
        query="arbitrage du 2025-01-15",
        content="En date du 2025-01-15, l'arbitrage confirme la suppression du module legacy.",
    )
    assert boost_date == 1.35


def test_temporal_boost_in_search(tmp_path: Path):
    db_file = tmp_path / "test_loop_mem.db"
    docs_dir = tmp_path / "docs"
    arch_dir = docs_dir / "01-architecture"
    arch_dir.mkdir(parents=True)

    # Document A : Spécification statique sans date ni contexte de réunion
    file_a = arch_dir / "spec_auth.md"
    file_a.write_text(
        "# Spécification Authentification\n\n"
        "L'authentification utilise des identifiants standards et des sessions applicatives.\n",
        encoding="utf-8"
    )

    # Document B : Compte-rendu de réunion récent avec date et décision formelle
    file_b = arch_dir / "cr_reunion_auth.md"
    file_b.write_text(
        "# Compte-rendu Réunion Authentification\n\n"
        "Date : 2025-02-10.\n"
        "Décision validée : migration immédiate vers OpenID Connect et suppression des sessions.\n",
        encoding="utf-8"
    )

    FactSearchIndexer.index_project_docs(
        project_name="proj_temporal",
        docs_dir=docs_dir,
        db_path=db_file,
    )

    # Recherche orientée décision/réunion
    results = FactSearchRetriever.search(
        query="quelles décisions de réunion pour authentification ?",
        project_name="proj_temporal",
        db_path=db_file,
    )

    assert len(results) >= 2
    # Le premier résultat doit être le compte-rendu grâce au temporal_boost
    assert "cr_reunion_auth" in results[0]["doc_path"]
    assert results[0].get("temporal_boost", 1.0) >= 1.30
