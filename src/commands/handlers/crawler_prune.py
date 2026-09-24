"""
Gestionnaire de cycle de vie et TTL du cache crawler (MLOOP-232-BE / ADR-015).

Assure l'invalidation temporelle (TTL 60 jours) des Markdown Twins,
la sanctuarisation absolue des pages 'pinned: true' ou 'source: permanent',
le support du mode simulation --dry-run, et la purge des dépôts orphelins hors manifest.
Conforme ADR-0003, ADR-015, ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import threading
import time
from typing import Any, Dict, List, Optional, Set

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.crawler_prune")

DEFAULT_TTL_DAYS: int = 60
_PRUNE_LOCK = threading.Lock()


def is_pinned_or_permanent(file_path: Path) -> bool:
    """Détecte si un document bénéficie d'une immunité absolue via son frontmatter."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(2048).lower()
        if "pinned: true" in head or "pinned: 'true'" in head or 'pinned: "true"' in head:
            return True
        if "source: permanent" in head or "source: 'permanent'" in head or 'source: "permanent"' in head:
            return True
        return False
    except Exception as exc:
        logger.debug("Erreur lecture frontmatter %s : %s", file_path, exc)
        return False


def _load_known_manifest_sources(base_dir: Path) -> Set[str]:
    """Extrait tous les noms de dépôts et chemins répertoriés dans les manifests sources."""
    known: Set[str] = set()

    manifest_candidates: List[Path] = [
        base_dir / "docs" / "00-ingested" / "source_manifest.json",
    ]

    projects_dir = base_dir / "Projects"
    if projects_dir.exists():
        for p in projects_dir.rglob("source_manifest.json"):
            manifest_candidates.append(p)

    for manifest_path in manifest_candidates:
        if not manifest_path.exists():
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sources = data.get("sources", [])
            for s in sources:
                if isinstance(s, dict):
                    for k in ("repo", "repository", "url", "filename", "filepath"):
                        val = s.get(k)
                        if val and isinstance(val, str):
                            known.add(val.lower())
                            known.add(Path(val).name.lower())
                elif isinstance(s, str):
                    known.add(s.lower())
                    known.add(Path(s).name.lower())
        except Exception as exc:
            logger.debug("Échec lecture manifest %s : %s", manifest_path, exc)

    return known


def _calc_dir_size(dir_path: Path) -> int:
    """Calcule récursivement la taille d'un répertoire en octets."""
    total = 0
    try:
        for entry in os.scandir(dir_path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += _calc_dir_size(Path(entry.path))
    except (OSError, PermissionError) as exc:
        logger.debug("Erreur accès répertoire dans _calc_dir_size %s : %s", dir_path, exc, exc_info=True)
    return total


def prune_crawler_cache(
    base_dir: Optional[Path] = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Exécute l'invalidation TTL du cache crawler et la purge des dépôts orphelins."""
    if ttl_days <= 0:
        raise ValueError(f"Le TTL en jours doit être strictement positif (reçu: {ttl_days})")

    root = base_dir if base_dir else Path(".")
    crawler_dir = root / "memory" / "crawler"
    cache_dir = crawler_dir / "cache"
    repos_dir = crawler_dir / "repos"

    cutoff_seconds = time.time() - (ttl_days * 86400)
    pruned_cache_files: List[Path] = []
    pinned_protected: List[Path] = []
    pruned_repos: List[Path] = []
    reclaimed_bytes = 0

    with _PRUNE_LOCK:
        # 1. Élagage sélectif des fichiers du cache web
        if cache_dir.exists():
            for item in cache_dir.rglob("*"):
                if not item.is_file():
                    continue
                if is_pinned_or_permanent(item):
                    pinned_protected.append(item)
                    continue

                try:
                    if item.stat().st_mtime < cutoff_seconds:
                        file_size = item.stat().st_size
                        pruned_cache_files.append(item)
                        reclaimed_bytes += file_size
                        if not dry_run:
                            item.unlink(missing_ok=True)
                except OSError as exc:
                    logger.warning("Échec accès fichier cache %s : %s", item, exc)

        # 2. Détection et purge des dépôts Git clonés orphelins
        if repos_dir.exists():
            known_sources = _load_known_manifest_sources(root)
            for repo_sub in repos_dir.iterdir():
                if not repo_sub.is_dir():
                    continue
                repo_name = repo_sub.name.lower()
                if repo_name not in known_sources:
                    repo_size = _calc_dir_size(repo_sub)
                    pruned_repos.append(repo_sub)
                    reclaimed_bytes += repo_size
                    if not dry_run:
                        shutil.rmtree(repo_sub, ignore_errors=True)

    reclaimed_mb = round(reclaimed_bytes / (1024 * 1024), 2)
    return {
        "dry_run": dry_run,
        "ttl_days": ttl_days,
        "pruned_cache_files_count": len(pruned_cache_files),
        "pinned_protected_count": len(pinned_protected),
        "pruned_repos_count": len(pruned_repos),
        "reclaimed_bytes": reclaimed_bytes,
        "reclaimed_mb": reclaimed_mb,
        "pruned_cache_files": [str(p) for p in pruned_cache_files],
        "pruned_repos": [str(p) for p in pruned_repos],
    }


def handle_crawler(args: argparse.Namespace, state: Any, project_path: Optional[Path]) -> int:
    """Point d'entrée CLI pour la commande `mloop crawler prune`."""
    action = getattr(args, "action", "prune") or "prune"
    dry_run = bool(getattr(args, "dry_run", False))
    ttl_days = getattr(args, "ttl_days", DEFAULT_TTL_DAYS)

    if action != "prune":
        ZeroFluffConsole.error(f"Action crawler inconnue : '{action}'. Action valide : prune.")
        return 1

    try:
        ttl_val = int(ttl_days)
        if ttl_val <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        ZeroFluffConsole.error(f"Paramètre --ttl-days invalide : '{ttl_days}'. Doit être un entier > 0.")
        return 1

    prefix = "[SIMULATION DRY-RUN] " if dry_run else ""
    ZeroFluffConsole.info(f"=== {prefix}ÉLAGAGE DU CACHE CRAWLER (TTL: {ttl_val}j) ===")
    base_dir = project_path if project_path else Path(".")

    try:
        res = prune_crawler_cache(base_dir=base_dir, ttl_days=ttl_val, dry_run=dry_run)
        ZeroFluffConsole.success(
            f"{prefix}Élagage terminé : {res['pruned_cache_files_count']} fichier(s) cache et "
            f"{res['pruned_repos_count']} dépôt(s) orphelin(s)."
        )
        ZeroFluffConsole.info(
            f"Gain d'espace : {res['reclaimed_mb']} Mo libérés | "
            f"Pages protégées (pinned/permanent) : {res['pinned_protected_count']}"
        )
        return 0
    except Exception as err:
        ZeroFluffConsole.error(f"Échec de l'élagage crawler : {err}")
        logger.error("Erreur lors de handle_crawler: %s", err, exc_info=True)
        return 1
