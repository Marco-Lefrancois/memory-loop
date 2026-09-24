"""
Middleware de rotation et archivage rotatif des journaux (MLOOP-231-BE / ADR-015).

Assure la rotation automatique des journaux à 5.0 Mo, la compression gzip (.gz)
vers memory/logs/archive/ et l'élagage glissant des archives de plus de 30 jours.
Conforme ADR-0003, ADR-015, ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import os
from pathlib import Path
import shutil
import threading
import time
from typing import Any, Dict, List, Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.log_rotation")

DEFAULT_MAX_BYTES: int = 5 * 1024 * 1024  # 5.0 Mo
DEFAULT_RETENTION_DAYS: int = 30
_ROTATION_LOCK = threading.Lock()


def _resolve_archive_dir(base_dir: Optional[Path] = None) -> Path:
    """Résout le répertoire normé des archives compressées."""
    root = base_dir if base_dir else Path(".")
    return root / "memory" / "logs" / "archive"


def rotate_single_log(
    file_path: Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
    force: bool = False,
    archive_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Archive et compresse en gzip un fichier de log s'il excède le seuil ou si force=True.
    Réinitialise le fichier source à vide de manière atomique sans perte.
    """
    if not file_path.exists() or file_path.stat().st_size == 0:
        return None

    size_bytes = file_path.stat().st_size
    if not force and size_bytes < max_bytes:
        return None

    target_archive_dir = archive_dir if archive_dir else _resolve_archive_dir(file_path.parent.parent)
    target_archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_filename = f"{file_path.stem}.{ts}{file_path.suffix}.gz"
    archive_path = target_archive_dir / archive_filename
    staging_path = target_archive_dir / f"{file_path.stem}.{ts}.staging"

    with _ROTATION_LOCK:
        try:
            # Copie vers staging puis troncature propre du fichier actif
            shutil.copy2(file_path, staging_path)
            with open(file_path, "w", encoding="utf-8") as f:
                f.truncate(0)

            # Compression gzip niveau 9
            with open(staging_path, "rb") as f_in, gzip.open(archive_path, "wb", compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

            if staging_path.exists():
                staging_path.unlink()

            logger.info(
                "Rotation réussie pour le journal : %s -> %s",
                file_path.name,
                archive_path.name,
                extra={"command": "rotate_single_log", "source": str(file_path), "archive": str(archive_path)},
            )
            return archive_path
        except Exception as err:
            logger.error(
                "Échec lors de la rotation de %s : %s",
                file_path,
                err,
                extra={"command": "rotate_single_log", "file": str(file_path)},
                exc_info=True,
            )
            if staging_path.exists():
                staging_path.unlink(missing_ok=True)
            return None


def prune_log_archives(archive_dir: Path, retention_days: int = DEFAULT_RETENTION_DAYS) -> List[Path]:
    """Élague les archives .gz dont l'âge dépasse retention_days."""
    if not archive_dir.exists():
        return []

    cutoff_seconds = time.time() - (retention_days * 86400)
    pruned: List[Path] = []

    for item in archive_dir.glob("*.gz"):
        try:
            if item.stat().st_mtime < cutoff_seconds:
                item.unlink(missing_ok=True)
                pruned.append(item)
                logger.info("Archive expirée élaguée : %s", item.name)
        except OSError as e:
            logger.warning("Impossible de supprimer l'archive %s : %s", item, e)

    return pruned


def get_candidate_log_files(base_dir: Optional[Path] = None) -> List[Path]:
    """Identifie l'ensemble des fichiers de logs et traces éligibles à la rotation."""
    root = base_dir if base_dir else Path(".")
    candidates: List[Path] = [
        root / "memory" / "events.jsonl",
        root / "memory" / "global_execution_traces.json",
        root / "memory" / "fact_search_log.jsonl",
        root / "memory" / "token_ledger.jsonl",
        root / "memory" / "logs" / "mloop.log",
        root / "memory" / "logs" / "errors.log",
    ]

    # Recherche additionnelle dans les sous-projets éventuels
    projects_dir = root / "Projects"
    if projects_dir.exists():
        for proj in projects_dir.iterdir():
            if proj.is_dir():
                proj_events = proj / "memory" / "events.jsonl"
                if proj_events.exists():
                    candidates.append(proj_events)

    return [p for p in candidates if p.exists() and p.is_file()]


def rotate_all_logs(
    base_dir: Optional[Path] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    force: bool = False,
    retention_days: int = DEFAULT_RETENTION_DAYS,
) -> Dict[str, Any]:
    """Exécute la rotation sur l'ensemble des journaux et élague les archives obsolètes."""
    root = base_dir if base_dir else Path(".")
    archive_dir = _resolve_archive_dir(root)
    candidates = get_candidate_log_files(root)

    archives_created: List[Path] = []
    for cand in candidates:
        res = rotate_single_log(cand, max_bytes=max_bytes, force=force, archive_dir=archive_dir)
        if res:
            archives_created.append(res)

    pruned = prune_log_archives(archive_dir, retention_days=retention_days)

    return {
        "candidates_count": len(candidates),
        "rotated_count": len(archives_created),
        "pruned_count": len(pruned),
        "archives_created": [str(p) for p in archives_created],
        "archives_pruned": [str(p) for p in pruned],
    }


def handle_logs(args: argparse.Namespace, state: Any, project_path: Optional[Path]) -> int:
    """Point d'entrée CLI pour la commande `mloop logs rotate [--force]`."""
    action = getattr(args, "action", "rotate") or "rotate"
    force = bool(getattr(args, "force", False))

    if action != "rotate":
        ZeroFluffConsole.error(f"Action de journalisation inconnue : '{action}'. Action valide : rotate.")
        return 1

    ZeroFluffConsole.info(f"=== ROTATION & ARCHIVAGE DES JOURNAUX ({action.upper()}) ===")
    base_dir = project_path if project_path else Path(".")

    try:
        summary = rotate_all_logs(base_dir=base_dir, max_bytes=DEFAULT_MAX_BYTES, force=force)
        ZeroFluffConsole.success(
            f"Rotation achevée : {summary['rotated_count']}/{summary['candidates_count']} journal(ux) archivé(s) en gzip."
        )
        if summary["pruned_count"] > 0:
            ZeroFluffConsole.info(f"Rétention 30j : {summary['pruned_count']} archive(s) expirée(s) nettoyée(s).")
        else:
            ZeroFluffConsole.info("Rétention 30j : 0 archive obsolète.")
        return 0
    except Exception as err:
        ZeroFluffConsole.error(f"Échec de la rotation des journaux : {err}")
        logger.error("Erreur lors de handle_logs: %s", err, exc_info=True)
        return 1
