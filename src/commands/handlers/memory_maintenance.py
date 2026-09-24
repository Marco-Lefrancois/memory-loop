"""
Module de maintenance et défragmentation SQLite (MLOOP-230-BE / ADR-015).

Fournit les routines d'audit de santé (PRAGMA integrity_check, freelist, orphelins FTS5)
et de compactage sécurisé (VACUUM atomique avec copie de secours temporaire .bak).
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (SQLite timeout 15s).
"""

from __future__ import annotations

import argparse
from contextlib import closing
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Dict, List, Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.memory_maintenance")

SQLITE_TIMEOUT = 15.0
FRAGMENTATION_THRESHOLD_PCT = 15.0


def _resolve_db_path(project_path: Optional[Path]) -> Path:
    """Résout le chemin canonique de loop_mem.db (projet ou racine)."""
    if project_path:
        proj_db = project_path / "memory" / "loop_mem.db"
        if proj_db.exists():
            return proj_db
    root_db = Path("memory") / "loop_mem.db"
    return root_db


def check_memory_health(db_path: Path) -> Dict[str, Any]:
    """Audit d'intégrité, de fragmentation et d'orphelins FTS5 sans verrouillage prolongé."""
    if not db_path.exists():
        return {
            "healthy": False,
            "error": f"Base SQLite introuvable : {db_path}",
            "db_path": str(db_path),
            "size_bytes": 0,
            "size_mb": 0.0,
            "page_count": 0,
            "freelist_count": 0,
            "fragmentation_pct": 0.0,
            "orphan_chunks_count": 0,
            "orphan_chunk_ids": [],
            "integrity_check": "not_found",
            "quick_check": "not_found",
        }

    size_bytes = db_path.stat().st_size
    size_mb = round(size_bytes / (1024 * 1024), 2)

    with sqlite3.connect(str(db_path), timeout=SQLITE_TIMEOUT) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. Vérification intégrité
        quick = cur.execute("PRAGMA quick_check;").fetchone()[0]
        integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]

        # 2. Métriques de fragmentation
        page_count = cur.execute("PRAGMA page_count;").fetchone()[0]
        freelist_count = cur.execute("PRAGMA freelist_count;").fetchone()[0]
        frag_pct = round((freelist_count / page_count * 100.0), 2) if page_count > 0 else 0.0

        # 3. Détection orphelins FTS5
        orphan_ids: List[int] = []
        try:
            # Vérifier si la table docs_chunks existe
            has_table = cur.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='docs_chunks';"
            ).fetchone()[0]
            if has_table:
                rows = cur.execute("SELECT id, doc_path FROM docs_chunks;").fetchall()
                for r in rows:
                    p = Path(r["doc_path"])
                    if not p.exists():
                        orphan_ids.append(r["id"])
        except Exception as exc:
            logger.warning("Échec inspection orphelins FTS5 : %s", exc, exc_info=True)

    healthy = quick == "ok" and integrity == "ok"
    return {
        "healthy": healthy,
        "db_path": str(db_path),
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "page_count": page_count,
        "freelist_count": freelist_count,
        "fragmentation_pct": frag_pct,
        "orphan_chunks_count": len(orphan_ids),
        "orphan_chunk_ids": orphan_ids,
        "integrity_check": integrity,
        "quick_check": quick,
    }


def execute_memory_vacuum(db_path: Path, force: bool = False) -> Dict[str, Any]:
    """
    Exécute le compactage VACUUM et la purge des chunks orphelins avec backup atomique.
    Rollback automatique vers le backup en cas d'incident.
    """
    health = check_memory_health(db_path)
    if not health.get("healthy"):
        return {
            "vacuum_executed": False,
            "reason": "unhealthy_or_missing",
            "details": health,
        }

    frag_pct = health["fragmentation_pct"]
    if frag_pct < FRAGMENTATION_THRESHOLD_PCT and not force:
        return {
            "vacuum_executed": False,
            "reason": "fragmentation_below_threshold",
            "fragmentation_pct": frag_pct,
            "threshold_pct": FRAGMENTATION_THRESHOLD_PCT,
            "details": health,
        }

    bak_path = db_path.with_suffix(".db.bak")
    shutil.copy2(db_path, bak_path)
    old_size = health["size_bytes"]
    purged_count = 0

    try:
        with sqlite3.connect(str(db_path), timeout=SQLITE_TIMEOUT) as conn:
            cur = conn.cursor()
            # 1. Purge des chunks orphelins si identifiés
            orphan_ids = health.get("orphan_chunk_ids", [])
            if orphan_ids:
                placeholders = ",".join("?" * len(orphan_ids))
                cur.execute(f"DELETE FROM docs_chunks WHERE id IN ({placeholders})", orphan_ids)
                # Purge de la table virtuelle FTS5 correspondante si existante
                has_fts = cur.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='docs_chunks_fts';"
                ).fetchone()[0]
                if has_fts:
                    cur.execute(
                        f"DELETE FROM docs_chunks_fts WHERE chunk_id IN ({placeholders})",
                        orphan_ids,
                    )
                conn.commit()
                purged_count = len(orphan_ids)

            # 2. VACUUM et PRAGMA optimize
            conn.execute("VACUUM;")
            conn.execute("PRAGMA optimize;")

        # 3. Validation de l'intégrité post-vacuum
        post_health = check_memory_health(db_path)
        if not post_health.get("healthy"):
            raise sqlite3.DatabaseError("Post-vacuum integrity check failed")

        new_size = db_path.stat().st_size
        reclaimed_bytes = max(0, old_size - new_size)
        reclaimed_mb = round(reclaimed_bytes / (1024 * 1024), 2)

        # Nettoyage du fichier de sauvegarde en cas de succès certifié
        if bak_path.exists():
            bak_path.unlink()

        return {
            "vacuum_executed": True,
            "old_size_mb": health["size_mb"],
            "new_size_mb": post_health["size_mb"],
            "reclaimed_mb": reclaimed_mb,
            "purged_orphans": purged_count,
            "post_fragmentation_pct": post_health["fragmentation_pct"],
        }
    except Exception as exc:
        logger.error("Échec de l'opération VACUUM sur %s : %s", db_path, exc, exc_info=True)
        # Rollback atomique depuis la sauvegarde
        if bak_path.exists():
            shutil.copy2(bak_path, db_path)
            bak_path.unlink()
        raise


def handle_memory(args: argparse.Namespace, state: Any, project_path: Optional[Path]) -> int:
    """Point d'entrée CLI pour la commande `mloop memory [health|vacuum]`."""
    action = getattr(args, "action", "health") or "health"
    force = bool(getattr(args, "force", False))
    db_path = _resolve_db_path(project_path)

    ZeroFluffConsole.info(f"=== MAINTENANCE MÉMOIRE SQLITE ({action.upper()}) ===")
    ZeroFluffConsole.info(f"Cible : {db_path}")

    if action == "health":
        health = check_memory_health(db_path)
        if not health.get("healthy"):
            ZeroFluffConsole.error(f"Santé compromise : {health.get('error') or health.get('integrity_check')}")
            return 1

        ZeroFluffConsole.success(f"Intégrité SQLite : PASS ({health['integrity_check']})")
        ZeroFluffConsole.info(
            f"Taille : {health['size_mb']} Mo | Pages : {health['page_count']} | "
            f"Pages Libres : {health['freelist_count']} ({health['fragmentation_pct']}%)"
        )
        if health["orphan_chunks_count"] > 0:
            ZeroFluffConsole.warning(
                f"Fragments FTS5 orphelins détectés : {health['orphan_chunks_count']} chunk(s) éligible(s) à la purge"
            )
        else:
            ZeroFluffConsole.success("Index FTS5 : 0 chunk orphelin détecté")
        return 0

    if action == "vacuum":
        try:
            res = execute_memory_vacuum(db_path, force=force)
            if not res.get("vacuum_executed"):
                reason = res.get("reason")
                if reason == "fragmentation_below_threshold":
                    ZeroFluffConsole.info(
                        f"Compactage ignoré : fragmentation de {res['fragmentation_pct']}% "
                        f"inférieure au seuil de {res['threshold_pct']}% (utilisez --force pour outrepasser)."
                    )
                    return 0
                ZeroFluffConsole.warning(f"Opération non exécutée : {reason}")
                return 0

            ZeroFluffConsole.success("Compactage VACUUM terminé avec succès !")
            ZeroFluffConsole.info(
                f"Gain d'espace : {res['reclaimed_mb']} Mo libérés "
                f"({res['old_size_mb']} Mo -> {res['new_size_mb']} Mo)"
            )
            if res.get("purged_orphans", 0) > 0:
                ZeroFluffConsole.info(f"Chunks orphelins purgés : {res['purged_orphans']}")
            return 0
        except Exception as err:
            ZeroFluffConsole.error(f"Échec critique du compactage : {err}")
            return 1

    ZeroFluffConsole.error(f"Action memory inconnue : '{action}'. Actions valides : health, vacuum.")
    return 1
