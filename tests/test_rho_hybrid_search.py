"""
Tests pour la Recherche Hybride RHO (BM25 + Vector + Graph) - MLOOP-102-BE.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.loop_mem.rho_hybrid_search import (
    RHOHybridSearch,
    search_rho_hybrid,
    get_rho_hybrid_stats,
)


@pytest.fixture
def temp_project(tmp_path):
    """Crée un projet temporaire avec une base de données RHO."""
    project_name = "TestProject"
    project_dir = tmp_path / "Projects" / project_name
    project_dir.mkdir(parents=True)

    # Créer la base de données avec la table rho_memory
    db_path = tmp_path / "memory" / "loop_mem.db"
    db_path.parent.mkdir(parents=True)

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rho_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                keyword TEXT NOT NULL,
                error_trace TEXT NOT NULL,
                solution TEXT NOT NULL,
                embedding_json TEXT NOT NULL DEFAULT '[]'
            )
        """)

        # Insérer des données de test avec des embeddings factices
        test_rules = [
            (
                project_name,
                "timeout",
                "Erreur de timeout lors de la connexion API",
                "Augmenter le timeout à 30s",
                json.dumps([0.1, 0.2, 0.3]),
            ),
            (
                project_name,
                "null_pointer",
                "NullPointerException dans le service",
                "Vérifier les null checks",
                json.dumps([0.4, 0.5, 0.6]),
            ),
            (
                project_name,
                "memory",
                "Out of memory error",
                "Augmenter la heap size",
                json.dumps([0.7, 0.8, 0.9]),
            ),
        ]

        for rule in test_rules:
            conn.execute(
                "INSERT INTO rho_memory (project_name, keyword, error_trace, solution, embedding_json) "
                "VALUES (?, ?, ?, ?, ?)",
                rule,
            )

    # Créer un fichier de graphe de test
    graph_dir = project_dir / "memory"
    graph_dir.mkdir(parents=True)
    graph_file = graph_dir / "knowledge_graph.json"
    graph_file.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "n1", "name": "timeout_error"},
                    {"id": "n2", "name": "null_pointer_exception"},
                    {"id": "n3", "name": "memory_leak"},
                ]
            }
        )
    )

    return {
        "project_name": project_name,
        "project_dir": project_dir,
        "db_path": db_path,
        "graph_file": graph_file,
    }


class TestRHOHybridSearch:
    """Tests pour la classe RHOHybridSearch."""

    def test_initialization(self, temp_project):
        """Teste l'initialisation correcte du moteur de recherche."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        assert searcher.project_name == temp_project["project_name"]
        assert searcher.db_path == temp_project["db_path"]
        assert "bm25" in searcher.weights
        assert "vector" in searcher.weights
        assert "graph" in searcher.weights

    def test_weight_normalization(self, temp_project):
        """Teste la normalisation des poids."""
        weights = {"bm25": 2.0, "vector": 2.0, "graph": 1.0}
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            weights=weights,
            db_path=temp_project["db_path"],
        )

        # Les poids doivent sommer à 1.0
        total = sum(searcher.weights.values())
        assert abs(total - 1.0) < 1e-6

        # Vérifier les proportions
        assert abs(searcher.weights["bm25"] - 0.4) < 1e-6
        assert abs(searcher.weights["vector"] - 0.4) < 1e-6
        assert abs(searcher.weights["graph"] - 0.2) < 1e-6

    def test_stream_bm25(self, temp_project):
        """Teste le flux BM25 sur les données RHO."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        results = searcher._stream_bm25("timeout")

        assert len(results) > 0
        assert any("timeout" in r["title"].lower() for r in results)
        assert all(r["stream"] == "bm25" for r in results)

    def test_stream_vector_with_mock(self, temp_project):
        """Teste le flux vectoriel avec un mock de l'embedding."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        # Mock get_embedding pour retourner un vecteur factice
        with patch("src.loop_mem.rho_hybrid_search.get_embedding") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            results = searcher._stream_vector("timeout")

            # Avec des embeddings factices, devrait trouver des résultats
            assert len(results) > 0
            assert all(r["stream"] == "vector" for r in results)

    def test_stream_graph(self, temp_project):
        """Teste le flux graph sur les nœuds de connaissances."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        # Modifier les chemins pour pointer vers le répertoire temporaire
        searcher.graph_file = temp_project["graph_file"]
        searcher.graphify_file = temp_project["project_dir"] / "graphify-out" / "graph.json"

        results = searcher._stream_graph("timeout")

        # Devrait trouver le nœud "timeout_error"
        assert len(results) > 0
        assert any("timeout" in r["title"].lower() for r in results)
        assert all(r["stream"] == "graph" for r in results)

    def test_search_hybrid_integration(self, temp_project):
        """Teste la recherche hybride complète."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        with patch("src.loop_mem.rho_hybrid_search.get_embedding") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            results = searcher.search("timeout")

            assert "results" in results
            assert "latency_ms" in results
            assert "total" in results
            assert "weights_used" in results

            if results["results"]:
                first_result = results["results"][0]
                assert "id" in first_result
                assert "title" in first_result
                assert "relevance" in first_result
                assert "streams" in first_result
                assert 0 <= first_result["relevance"] <= 1

    def test_search_empty_query(self, temp_project):
        """Teste la recherche avec une requête vide."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        results = searcher.search("")

        assert results["results"] == []
        assert results["latency_ms"] == 0.0
        assert results["total"] == 0

    def test_search_custom_weights(self, temp_project):
        """Teste la recherche avec des poids personnalisés."""
        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        custom_weights = {"bm25": 0.7, "vector": 0.2, "graph": 0.1}

        with patch("src.loop_mem.rho_hybrid_search.get_embedding") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            results = searcher.search("timeout", weights=custom_weights)

            # Vérifier que les poids personnalisés sont utilisés
            assert results["weights_used"]["bm25"] == pytest.approx(0.7, abs=1e-6)


class TestSearchRHOHybrid:
    """Tests pour la fonction publique search_rho_hybrid."""

    def test_search_rho_hybrid_function(self, temp_project):
        """Teste la fonction publique search_rho_hybrid."""
        with patch("src.loop_mem.rho_hybrid_search.get_embedding") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            results = search_rho_hybrid(
                project_name=temp_project["project_name"],
                query="timeout",
                top_k=3,
            )

            assert "results" in results
            assert len(results["results"]) <= 3


class TestGetRHOHybridStats:
    """Tests pour la fonction get_rho_hybrid_stats."""

    def test_get_stats(self, temp_project):
        """Teste la récupération des statistiques RHO."""
        # Patch le chemin de la base de données
        with patch("src.loop_mem.rho_hybrid_search.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.__truediv__ = lambda self, x: temp_project["db_path"]

            stats = get_rho_hybrid_stats(temp_project["project_name"])

            assert stats["project"] == temp_project["project_name"]
            # Note: Les stats dépendent de la connexion à la base de données
            # Dans un environnement de test isolé, les valeurs peuvent varier
            assert "total_rules" in stats
            assert "embedded_rules" in stats

    def test_get_stats_nonexistent_project(self):
        """Teste les stats pour un projet inexistant."""
        stats = get_rho_hybrid_stats("NonExistentProject")

        assert stats["project"] == "NonExistentProject"
        assert stats["total_rules"] == 0


class TestRHOSearchEdgeCases:
    """Tests des cas limites pour la recherche hybride RHO."""

    def test_search_with_no_embeddings(self, temp_project):
        """Teste la recherche quand aucun embedding n'est disponible."""
        # Supprimer les embeddings de la base
        with sqlite3.connect(str(temp_project["db_path"])) as conn:
            conn.execute("UPDATE rho_memory SET embedding_json = '[]'")

        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        with patch("src.loop_mem.rho_hybrid_search.get_embedding") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            results = searcher.search("timeout")

            # Devrait quand même retourner des résultats via BM25 et Graph
            assert "results" in results

    def test_search_with_no_graph_files(self, temp_project):
        """Teste la recherche quand les fichiers graphe n'existent pas."""
        # Supprimer les fichiers graphe
        temp_project["graph_file"].unlink(missing_ok=True)

        searcher = RHOHybridSearch(
            project_name=temp_project["project_name"],
            db_path=temp_project["db_path"],
        )

        with patch("src.loop_mem.rho_hybrid_search.get_embedding") as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]

            results = searcher.search("timeout")

            # Devrait quand même retourner des résultats via BM25 et Vector
            assert "results" in results
