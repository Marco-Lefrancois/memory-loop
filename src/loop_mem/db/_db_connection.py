"""
_db_connection.py — Session context manager & DDL lazy de la couche SQLite mLoop.

Extraction MLOOP-178-BE (BR=20) depuis src/loop_mem/db.py monolithique (956 L).
Famille Q1-A : session CM + schéma DDL lazy (zéro _db_init.py — Q2 pré-résolu).

Contrat ADR-0369 :
  - 100% des accès `sqlite3.connect` encapsulés dans un bloc `with`
    (contextlib.closing) — zéro connexion nue retournée à l'appelant.
  - timeout=15.0 explicite, PRAGMA WAL + busy_timeout, auto-commit/rollback.
  - Le legacy `_get_observation_conn` (connexion nue) est SUPPRIMÉ (Q5-A).

Base dédiée : memory/loop_mem.db — observations de session indexées FTS5.
"""

import logging
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

_OBSERVATION_DB_PATH = Path("memory/loop_mem.db")


@contextmanager
def get_observation_db_session(db_path: Path = _OBSERVATION_DB_PATH):
    """
    Context Manager pour la base de données des observations mLoop.
    Garantit l'auto-commit des transactions, le rollback en cas d'erreur
    et la fermeture systématique de la connexion (Zero DB Lock avec WAL mode).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(db_path), timeout=15.0)) as conn:  # noqa: RULE-AST-02 (connect en context_expr de closing() — lifecycle @contextmanager : commit/rollback/close garantis, ADR-0369)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=20000;")
        except Exception as e:
            logger.warning(
                "Configuration des PRAGMA WAL/busy_timeout échouée (mode SQLite dégradé)",
                exc_info=True,
                extra={
                    "component": "loop_mem.db",
                    "operation": "get_observation_db_session",
                    "db_path": str(db_path),
                    "error": str(e),
                },
            )
        _init_observation_db(conn, db_path)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"[DB ERROR] Transaction annulée sur {db_path} : {e}") from e


_INITIALIZED_DBS = set()


def _init_observation_db(conn: sqlite3.Connection, db_path: Path):
    """Crée les tables si elles n'existent pas (exécuté une seule fois par base)."""
    canon = str(db_path)
    if canon in _INITIALIZED_DBS:
        return
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('decision', 'bugfix', 'feature', 'discovery')),
            file_scope TEXT,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    # Table FTS5 : le contenu est stocké dans le FTS5 et on référence l'id
    # de la table observations via observation_id (UNINDEXED = stocké sans indexation full-text)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
            observation_id UNINDEXED,
            project_name UNINDEXED,
            type UNINDEXED,
            content
        )
    """)
    # Table pour le RHO (Chaos Testing / Auto-Healing sémantique)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rho_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            keyword TEXT NOT NULL,
            error_trace TEXT NOT NULL,
            solution TEXT NOT NULL,
            embedding_json TEXT
        )
    """)
    # Table Lexique Métier Dynamique par Projet (ADR-0327)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            term TEXT NOT NULL,
            aliases_json TEXT,
            category TEXT,
            definition TEXT,
            target_type TEXT,
            target_id TEXT,
            source_file TEXT,
            last_updated TEXT NOT NULL,
            UNIQUE(project_name, term)
        )
    """)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS project_lexicon_fts USING fts5(
            lexicon_id UNINDEXED,
            project_name UNINDEXED,
            term,
            aliases,
            category UNINDEXED,
            definition,
            target_id
        )
    """)
    # Table Chunks Documentaires SSOT & Fact-Search 2.0 (ADR-0326)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS docs_chunks (
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
            last_updated TEXT NOT NULL,
            UNIQUE(project_name, doc_path, line_start, line_end)
        )
    """)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_chunks_fts USING fts5(
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
    conn.commit()
