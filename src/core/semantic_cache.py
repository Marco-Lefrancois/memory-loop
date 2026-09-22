"""
Semantic Cache Déterministe pour Memory Loop (mLoop).
Permet de cacher localement et de manière transparente les réponses LLM
sur la base d'un hash SHA256 invariant (modèle, prompts, format, température).
Élimine les coûts et la latence lors de ré-exécutions ou audits QA identiques.
"""

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger("core.semantic_cache")


class SemanticCache:
    """
    Gestionnaire de cache déterministe SQLite thread-safe pour les interactions LLM.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_dir = Path("memory") / "cache"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "llm_cache.sqlite"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
        self._init_db()

    from contextlib import contextmanager

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=10000;")
        except Exception as e:
            logger.warning(
                "PRAGMA WAL/busy_timeout du cache semantique echoues (mode degrade)",
                exc_info=True,
                extra={
                    "component": "core.semantic_cache",
                    "operation": "semantic_cache_connection",
                    "error": str(e),
                },
            )
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    cache_key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    system_prompt_preview TEXT,
                    user_prompt_preview TEXT,
                    response_text TEXT NOT NULL,
                    response_json TEXT,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    hit_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_model ON semantic_cache(model)")
            conn.commit()

    @staticmethod
    def compute_key(
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        extra_context: Optional[str] = None
    ) -> str:
        """
        Calcule une clé de hachage SHA-256 canonique pour la requête LLM.
        """
        hasher = hashlib.sha256()
        hasher.update(model.strip().lower().encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(system_prompt.strip().encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(user_prompt.strip().encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(str(round(temperature, 2)).encode("utf-8"))
        hasher.update(b"\x00")
        
        if response_schema:
            schema_str = json.dumps(response_schema, sort_keys=True)
            hasher.update(schema_str.encode("utf-8"))
        hasher.update(b"\x00")
        
        if extra_context:
            hasher.update(extra_context.strip().encode("utf-8"))
            
        return hasher.hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une réponse en cache par sa clé. Incrémente le hit_count.
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM semantic_cache WHERE cache_key = ?",
                (cache_key,)
            ).fetchone()
            
            if row:
                conn.execute(
                    "UPDATE semantic_cache SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE cache_key = ?",
                    (cache_key,)
                )
                conn.commit()
                
                parsed_json = None
                if row["response_json"]:
                    try:
                        parsed_json = json.loads(row["response_json"])
                    except Exception as e:
                        logger.debug(
                            "response_json du cache semantique illisible, retour sans parsing",
                            exc_info=True,
                            extra={
                                "component": "core.semantic_cache",
                                "operation": "get_cached_response",
                                "error": str(e),
                            },
                        )
                        
                return {
                    "cache_key": row["cache_key"],
                    "model": row["model"],
                    "response_text": row["response_text"],
                    "response_json": parsed_json,
                    "prompt_tokens": row["prompt_tokens"],
                    "completion_tokens": row["completion_tokens"],
                    "hit_count": row["hit_count"] + 1,
                    "created_at": row["created_at"]
                }
        return None

    def set(
        self,
        cache_key: str,
        model: str,
        response_text: str,
        system_prompt: str = "",
        user_prompt: str = "",
        response_json: Optional[Dict[str, Any]] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ) -> None:
        """
        Enregistre une réponse dans le cache SQLite.
        """
        json_str = json.dumps(response_json, ensure_ascii=False) if response_json is not None else None
        sys_preview = system_prompt[:150] if system_prompt else ""
        user_preview = user_prompt[:150] if user_prompt else ""
        
        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO semantic_cache (
                    cache_key, model, system_prompt_preview, user_prompt_preview,
                    response_text, response_json, prompt_tokens, completion_tokens,
                    hit_count, created_at, last_accessed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                cache_key,
                model,
                sys_preview,
                user_preview,
                response_text,
                json_str,
                prompt_tokens,
                completion_tokens
            ))
            conn.commit()

    def clear(self, model: Optional[str] = None) -> int:
        """Efface tout ou partie du cache."""
        with self._connection() as conn:
            if model:
                cur = conn.execute("DELETE FROM semantic_cache WHERE model = ?", (model,))
            else:
                cur = conn.execute("DELETE FROM semantic_cache")
            conn.commit()
            return cur.rowcount

    def stats(self) -> Dict[str, Any]:
        """Retourne des métriques d'utilisation du cache."""
        with self._connection() as conn:
            total_entries = conn.execute("SELECT COUNT(*) FROM semantic_cache").fetchone()[0]
            total_hits = conn.execute("SELECT SUM(hit_count) FROM semantic_cache").fetchone()[0] or 0
            saved_tokens = conn.execute(
                "SELECT SUM((prompt_tokens + completion_tokens) * hit_count) FROM semantic_cache"
            ).fetchone()[0] or 0
            
            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "saved_tokens_est": saved_tokens,
                "db_path": str(self.db_path)
            }
