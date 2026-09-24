"""
tools/drawdb/_discovery.py — Découverte récursive DBML (MLOOP-152-BE)

Sous-module de runner.py pour respecter ADR-0202 (≤300 lignes / module).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("drawdb.runner.discovery")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def find_dbml_files(project_name: Optional[str] = None) -> List[Path]:
    """
    Découverte récursive des *.dbml sous Projects/<projet actif>/.
    Retourne une liste triée de chemins absolus.
    Si aucun projet actif, parcourt tous les sous-dossiers de Projects/.
    """
    search_roots: List[Path] = []

    if project_name:
        candidate = REPO_ROOT / "Projects" / project_name
        if candidate.exists():
            search_roots.append(candidate)

    if not search_roots:
        projects_dir = REPO_ROOT / "Projects"
        if projects_dir.exists():
            search_roots = [
                p for p in projects_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
            ]

    found: List[Path] = []
    for root in search_roots:
        try:
            found.extend(sorted(root.rglob("*.dbml")))
        except Exception as exc:
            logger.debug(
                "Erreur lors du scan DBML",
                exc_info=True,
                extra={
                    "component": "drawdb",
                    "operation": "find_dbml_files",
                    "root": str(root),
                    "error": str(exc),
                },
            )

    # Déduplication en préservant l'ordre
    seen: set = set()
    unique: List[Path] = []
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def read_active_project() -> Optional[str]:
    """Lit le projet actif depuis memory/active_project.json."""
    active_json = REPO_ROOT / "memory" / "active_project.json"
    if not active_json.exists():
        return None
    try:
        with open(active_json, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("active_project") or None
    except Exception as exc:
        logger.debug(
            "Lecture de active_project.json échouée, projet actif inconnu",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "read_active_project",
                "path": str(active_json),
                "error": str(exc),
            },
        )
        return None
