# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
import pytest

from src.engine.fact_search.indexer import FactSearchIndexer
from src.loop_mem.db import get_observation_db_session


def test_incremental_indexing_flow(tmp_path: Path):
    db_file = tmp_path / "test_loop_mem.db"
    docs_dir = tmp_path / "docs"
    arch_dir = docs_dir / "01-architecture"
    arch_dir.mkdir(parents=True)

    file_a = arch_dir / "ADR-001.md"
    file_a.write_text("# ADR-001 : Architecture Initiale\n\nContenu substantiel pour l'architecture.\n", encoding="utf-8")

    file_b = arch_dir / "ADR-002.md"
    file_b.write_text("# ADR-002 : Base de Données\n\nChoix de SQLite pour la mémoire locale.\n", encoding="utf-8")

    # 1. Première indexation complète
    count_1 = FactSearchIndexer.index_project_docs(
        project_name="test_proj",
        docs_dir=docs_dir,
        db_path=db_file,
    )
    assert count_1 >= 2

    # Vérifier que le cache de hachage existe
    hash_cache = tmp_path / ".fact_search_hashes_test_proj.json"
    assert hash_cache.exists()

    # 2. Deuxième indexation sans modification -> 0 insertion
    count_2 = FactSearchIndexer.index_project_docs(
        project_name="test_proj",
        docs_dir=docs_dir,
        db_path=db_file,
    )
    assert count_2 == 0

    # 3. Modification d'un seul fichier (file_a)
    file_a.write_text("# ADR-001 : Architecture Révisée\n\nMise à jour substantielle de l'architecture.\n", encoding="utf-8")
    count_3 = FactSearchIndexer.index_project_docs(
        project_name="test_proj",
        docs_dir=docs_dir,
        db_path=db_file,
    )
    assert count_3 >= 1

    with get_observation_db_session(db_path=db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM docs_chunks WHERE doc_path LIKE '%ADR-001%'")
        rows = cursor.fetchall()
        assert any("Révisée" in r[0] for r in rows)

    # 4. Suppression d'un fichier (file_b)
    file_b.unlink()
    count_4 = FactSearchIndexer.index_project_docs(
        project_name="test_proj",
        docs_dir=docs_dir,
        db_path=db_file,
    )
    # count_4 = 0 nouveaux chunks insérés, mais file_b a été purgé
    assert count_4 == 0

    with get_observation_db_session(db_path=db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM docs_chunks WHERE doc_path LIKE '%ADR-002%'")
        assert cursor.fetchone()[0] == 0

    # 5. Forcer la ré-indexation avec force=True
    count_5 = FactSearchIndexer.index_project_docs(
        project_name="test_proj",
        docs_dir=docs_dir,
        db_path=db_file,
        force=True,
    )
    assert count_5 >= 1
