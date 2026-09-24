"""
mLoop Agent DAG Graph Store.
Inspiré de l'agent-graph-store d'OpenAI Codex.

Gère la persistance transactionnelle des arêtes de délégation entre agents dans SQLite :
(parent_thread_id, child_thread_id, role, status, result_summary_hash)
avec statut d'arête ThreadSpawnEdgeStatus (OPEN, CLOSED).
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional
from dataclasses import dataclass
import time
from src.utils.logger import get_logger

logger = get_logger("engine.agent_graph")


class ThreadSpawnEdgeStatus:
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class AgentSpawnEdge:
    parent_thread_id: str
    child_thread_id: str
    role: str
    status: str
    created_at: float
    closed_at: Optional[float] = None
    result_summary: Optional[str] = None


class AgentGraphStore:
    """
    Store SQLite pour le graphe de dépendances et de sous-sessions agentiques.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("memory") / "agent_graph.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager SQLite pour le graphe d'agents (ADR-0369 Std 2)."""
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)  # noqa: RULE-AST-02 (géré via @contextmanager _get_connection)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=10000;")
        except Exception as e:
            logger.warning(
                "PRAGMA WAL/busy_timeout de l'agent graph échoués (mode dégradé)",
                exc_info=True,
                extra={
                    "component": "engine.agent_graph",
                    "operation": "get_connection",
                    "error": str(e),
                },
            )
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_spawn_edges (
                    parent_thread_id TEXT NOT NULL,
                    child_thread_id TEXT NOT NULL PRIMARY KEY,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    closed_at REAL,
                    result_summary TEXT
                )
            """)
            conn.commit()

    def record_spawn(
        self, parent_thread_id: str, child_thread_id: str, role: str
    ) -> AgentSpawnEdge:
        edge = AgentSpawnEdge(
            parent_thread_id=parent_thread_id,
            child_thread_id=child_thread_id,
            role=role,
            status=ThreadSpawnEdgeStatus.OPEN,
            created_at=time.time(),
        )
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_spawn_edges
                (parent_thread_id, child_thread_id, role, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    edge.parent_thread_id,
                    edge.child_thread_id,
                    edge.role,
                    edge.status,
                    edge.created_at,
                ),
            )
            conn.commit()
        return edge

    def close_edge(self, child_thread_id: str, result_summary: Optional[str] = None) -> bool:
        closed_at = time.time()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE agent_spawn_edges
                SET status = ?, closed_at = ?, result_summary = ?
                WHERE child_thread_id = ?
            """,
                (ThreadSpawnEdgeStatus.CLOSED, closed_at, result_summary, child_thread_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_children(self, parent_thread_id: str) -> List[AgentSpawnEdge]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT parent_thread_id, child_thread_id, role, status, created_at, closed_at, result_summary
                FROM agent_spawn_edges
                WHERE parent_thread_id = ?
                ORDER BY created_at ASC
            """,
                (parent_thread_id,),
            )
            rows = cursor.fetchall()
            return [
                AgentSpawnEdge(
                    parent_thread_id=r[0],
                    child_thread_id=r[1],
                    role=r[2],
                    status=r[3],
                    created_at=r[4],
                    closed_at=r[5],
                    result_summary=r[6],
                )
                for r in rows
            ]

    def list_open_edges(self) -> List[AgentSpawnEdge]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT parent_thread_id, child_thread_id, role, status, created_at, closed_at, result_summary
                FROM agent_spawn_edges
                WHERE status = ?
            """,
                (ThreadSpawnEdgeStatus.OPEN,),
            )
            rows = cursor.fetchall()
            return [
                AgentSpawnEdge(
                    parent_thread_id=r[0],
                    child_thread_id=r[1],
                    role=r[2],
                    status=r[3],
                    created_at=r[4],
                    closed_at=r[5],
                    result_summary=r[6],
                )
                for r in rows
            ]
