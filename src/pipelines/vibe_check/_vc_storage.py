"""
Sous-module vibe_check/_vc_storage.py
Check lié à la santé et au volume de la mémoire persistante (MLOOP-234-FULL / ADR-015).

Checks inclus :
  - check_24_storage_hygiene : Hygiène & Plafond de Stockage Mémoire (Check 24)
"""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional

from src.commands.handlers.crawler_prune import _load_known_manifest_sources
from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_storage")

SQLITE_TIMEOUT: float = 15.0
MAX_MEMORY_MB_WARNING: float = 500.0
MAX_FRAGMENTATION_PCT_WARNING: float = 20.0
MAX_LOG_FILE_MB_WARNING: float = 10.0


def _get_dir_size_mb(path: Path) -> float:
    """Calcule récursivement la taille d'un dossier en mégaoctets de manière rapide."""
    if not path.exists():
        return 0.0
    total_bytes = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total_bytes += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total_bytes += int(_get_dir_size_mb(Path(entry.path)) * 1024 * 1024)
            except OSError as err:
                logger.debug("Erreur accès fichier %s : %s", entry.path, err, exc_info=True)
    except OSError as err:
        logger.debug("Erreur ouverture dossier %s : %s", path, err, exc_info=True)
    return round(total_bytes / (1024 * 1024), 2)


def check_24_storage_hygiene(
    project_dir: Path,
    project_name: str,
    lifecycle_mode: str,
    stage_label: str,
) -> dict:
    """
    Check 24 (ADR-015 — Hygiène & Plafond de Stockage Mémoire) :
    Contrôle l'intégrité de loop_mem.db, la fragmentation, les logs excessifs,
    la volumétrie globale de memory/ et les dépôts orphelins.

    Sévérité :
      - FAIL : corruption SQLite physique détectée.
      - WARNING : memory > 500 Mo, fragmentation > 20%, log actif > 10 Mo, ou dépôts orphelins.
      - PASS : nominal.
    """
    t0 = time.perf_counter()
    warnings: List[str] = []
    fails: List[str] = []

    # 1. Résolution de memory/
    root_mem = Path("memory")
    proj_mem = project_dir / "memory" if project_dir.exists() else None
    mem_dir = proj_mem if (proj_mem and proj_mem.exists()) else root_mem

    if not mem_dir.exists():
        return {
            "check": "Check 24 : Hygiène & Plafond de Stockage Mémoire (ADR-015)",
            "status": "PASS",
            "message": "Répertoire memory/ non initialisé.",
            "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        }

    # 2. Contrôle intégrité et fragmentation SQLite
    db_candidates = [mem_dir / "loop_mem.db", root_mem / "loop_mem.db"]
    target_db = next((p for p in db_candidates if p.exists()), None)

    if target_db:
        try:
            with sqlite3.connect(str(target_db), timeout=SQLITE_TIMEOUT) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA quick_check(1)")
                quick_res = cursor.fetchone()
                if not quick_res or quick_res[0].lower() != "ok":
                    fails.append(f"Corruption SQLite détectée sur {target_db.name} : {quick_res}")

                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0] or 0
                cursor.execute("PRAGMA freelist_count")
                freelist_count = cursor.fetchone()[0] or 0

                if page_count > 0:
                    frag_pct = round((freelist_count / page_count) * 100.0, 2)
                    if frag_pct > MAX_FRAGMENTATION_PCT_WARNING:
                        warnings.append(
                            f"Fragmentation SQLite élevée sur {target_db.name} : {frag_pct}% "
                            f"(seuil: {MAX_FRAGMENTATION_PCT_WARNING}%, exécutez 'mloop memory vacuum')"
                        )
        except Exception as exc:
            logger.error("Erreur audit SQLite Check 24 sur %s : %s", target_db, exc, exc_info=True)
            fails.append(f"Échec de connexion SQLite sur {target_db.name} : {exc}")

    # 3. Surveillance du volume global de memory/
    total_mem_mb = _get_dir_size_mb(mem_dir)
    if total_mem_mb > MAX_MEMORY_MB_WARNING:
        warnings.append(
            f"Volume global memory/ excessif : {total_mem_mb} Mo "
            f"(seuil: {MAX_MEMORY_MB_WARNING} Mo, exécutez 'mloop crawler prune' / 'mloop logs rotate')"
        )

    # 4. Détection de logs actifs non rotatés > 10 Mo
    for log_cand in [
        mem_dir / "events.jsonl",
        mem_dir / "global_execution_traces.json",
        mem_dir / "fact_search_log.jsonl",
        mem_dir / "logs" / "mloop.log",
        mem_dir / "logs" / "errors.log",
    ]:
        if log_cand.exists():
            try:
                sz_mb = round(log_cand.stat().st_size / (1024 * 1024), 2)
                if sz_mb > MAX_LOG_FILE_MB_WARNING:
                    warnings.append(
                        f"Journal actif volumineux : {log_cand.name} ({sz_mb} Mo > {MAX_LOG_FILE_MB_WARNING} Mo, "
                        f"exécutez 'mloop logs rotate')"
                    )
            except OSError as exc:
                logger.debug("Erreur lecture taille log %s : %s", log_cand, exc, exc_info=True)

    # 5. Détection de dépôts orphelins sous memory/crawler/repos/
    repos_dir = mem_dir / "crawler" / "repos"
    if repos_dir.exists():
        try:
            known_sources = _load_known_manifest_sources(Path("."))
            orphan_repos = [
                d.name for d in repos_dir.iterdir()
                if d.is_dir() and d.name.lower() not in known_sources
            ]
            if orphan_repos:
                warnings.append(
                    f"Dépôt(s) cloné(s) orphelin(s) détecté(s) sous {repos_dir.name}/ : {orphan_repos} "
                    f"(exécutez 'mloop crawler prune')"
                )
        except Exception as exc:
            logger.debug("Erreur scan repos orphelins : %s", exc, exc_info=True)

    # Verdict
    status = "FAIL" if fails else ("WARNING" if warnings else "PASS")
    details = fails + warnings
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "check": "Check 24 : Hygiène & Plafond de Stockage Mémoire (ADR-015)",
        "status": status,
        "details": details,
        "total_memory_mb": total_mem_mb,
        "warnings_count": len(warnings),
        "fails_count": len(fails),
        "duration_ms": duration_ms,
    }
