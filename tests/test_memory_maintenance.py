"""
Tests unitaires pour le moteur de maintenance et défragmentation SQLite (MLOOP-230-BE / EPIC-23).
"""

import argparse
import os
import shutil
import sqlite3
from pathlib import Path
import pytest

from src.commands.handlers.memory_maintenance import (
    check_memory_health,
    execute_memory_vacuum,
    handle_memory,
)


@pytest.fixture
def mock_db(tmp_path: Path):
    """Crée une base SQLite temporaire avec schéma minimal docs_chunks et FTS5."""
    db_path = tmp_path / "loop_mem.db"
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE docs_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            doc_path TEXT NOT NULL,
            ssot_layer TEXT NOT NULL,
            section_h1 TEXT,
            section_h2 TEXT,
            breadcrumb TEXT,
            line_start INTEGER,
            line_end INTEGER,
            content TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE VIRTUAL TABLE docs_chunks_fts USING fts5(
            chunk_id UNINDEXED,
            project_name UNINDEXED,
            ssot_layer UNINDEXED,
            doc_path UNINDEXED,
            breadcrumb,
            section_h1,
            section_h2,
            content
        )
    """)

    # Fichier existant sur disque
    real_file = tmp_path / "real_doc.md"
    real_file.write_text("# Doc Réel\nContenu valide.", encoding="utf-8")

    # Fichier orphelin (n'existe pas sur le disque)
    ghost_file = tmp_path / "ghost_doc.md"

    # Insertion chunks
    cursor.execute("""
        INSERT INTO docs_chunks (project_name, doc_path, ssot_layer, content, last_updated)
        VALUES ('test_proj', ?, '01-architecture', 'Chunk 1', '2026-09-24')
    """, (str(real_file),))
    cursor.execute("""
        INSERT INTO docs_chunks_fts (chunk_id, project_name, ssot_layer, doc_path, content)
        VALUES (1, 'test_proj', '01-architecture', ?, 'Chunk 1')
    """, (str(real_file),))

    cursor.execute("""
        INSERT INTO docs_chunks (project_name, doc_path, ssot_layer, content, last_updated)
        VALUES ('test_proj', ?, '01-architecture', 'Chunk 2 Orphelin', '2026-09-24')
    """, (str(ghost_file),))
    cursor.execute("""
        INSERT INTO docs_chunks_fts (chunk_id, project_name, ssot_layer, doc_path, content)
        VALUES (2, 'test_proj', '01-architecture', ?, 'Chunk 2 Orphelin')
    """, (str(ghost_file),))

    conn.commit()
    conn.close()
    return db_path


def test_memory_health_detects_orphan_chunks(mock_db: Path):
    """Vérifie la détection d'un chunk FTS5 orphelin sans bloquer la base."""
    health = check_memory_health(mock_db)
    assert health["healthy"] is True
    assert health["integrity_check"] == "ok"
    assert health["orphan_chunks_count"] == 1
    assert health["page_count"] > 0
    assert 0.0 <= health["fragmentation_pct"] <= 100.0


def test_memory_vacuum_skips_when_fragmentation_low(mock_db: Path):
    """Vérifie le refus de vacuum si le seuil de 15% n'est pas atteint sans force."""
    result = execute_memory_vacuum(mock_db, force=False)
    assert result["vacuum_executed"] is False
    assert result["reason"] == "fragmentation_below_threshold"
    assert not mock_db.with_suffix(".db.bak").exists()


def test_memory_vacuum_forces_and_purges_orphans(mock_db: Path):
    """Vérifie le compactage avec force et la purge des chunks orphelins."""
    result = execute_memory_vacuum(mock_db, force=True)
    assert result["vacuum_executed"] is True
    assert result["purged_orphans"] == 1
    assert not mock_db.with_suffix(".db.bak").exists()

    # Vérification que le chunk orphelin a bien disparu
    conn = sqlite3.connect(str(mock_db))
    rows = conn.execute("SELECT count(*) FROM docs_chunks").fetchone()[0]
    fts_rows = conn.execute("SELECT count(*) FROM docs_chunks_fts").fetchone()[0]
    conn.close()
    assert rows == 1
    assert fts_rows == 1


def test_memory_vacuum_restores_on_failure(mock_db: Path, monkeypatch: pytest.MonkeyPatch):
    """Vérifie que le backup .bak est restauré si une exception survient pendant le VACUUM."""
    original_size = mock_db.stat().st_size
    orig_connect = sqlite3.connect

    class FaultyConnWrapper:
        def __init__(self, conn):
            self._conn = conn

        def cursor(self):
            return self._conn.cursor()

        def commit(self):
            return self._conn.commit()

        def execute(self, sql, *args, **kwargs):
            if "VACUUM" in str(sql).upper():
                raise sqlite3.OperationalError("Simulated disk I/O error during VACUUM")
            return self._conn.execute(sql, *args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def close(self):
            return self._conn.close()

    def faulty_connect(*args, **kwargs):
        conn = orig_connect(*args, **kwargs)
        return FaultyConnWrapper(conn)

    monkeypatch.setattr("src.commands.handlers.memory_maintenance.sqlite3.connect", faulty_connect)

    with pytest.raises(sqlite3.OperationalError, match="Simulated disk I/O error"):
        execute_memory_vacuum(mock_db, force=True)

    # La base originale doit être toujours présente et intacte
    assert mock_db.exists()
    assert mock_db.stat().st_size == original_size
    assert not mock_db.with_suffix(".db.bak").exists()


def test_handle_memory_cli_health(mock_db: Path, monkeypatch: pytest.MonkeyPatch):
    """Vérifie l'exécution in-process du handler CLI memory health."""
    args = argparse.Namespace(action="health", project="test", force=False)
    state = {}
    project_path = mock_db.parent

    # Simuler la présence de loop_mem.db sous project_path / memory
    mem_dir = project_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mock_db, mem_dir / "loop_mem.db")

    code = handle_memory(args, state, project_path)
    assert code == 0


def test_handle_memory_cli_vacuum(mock_db: Path):
    """Vérifie l'exécution in-process du handler CLI memory vacuum."""
    args = argparse.Namespace(action="vacuum", project="test", force=True)
    state = {}
    project_path = mock_db.parent
    mem_dir = project_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mock_db, mem_dir / "loop_mem.db")

    code = handle_memory(args, state, project_path)
    assert code == 0
