"""
src/dashboard/routers/_drawdb_core.py — Constantes & utilitaires DrawDB (MLOOP-152-BE)

Sous-module de drawdb.py pour respecter ADR-0202 (≤300 lignes / module).
Contient les constantes, le verrou anti-rebond et les helpers de sonde/découverte.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List
from urllib import error as urllib_error
from urllib import request as urllib_request

from src.dashboard.project_utils import resolve_project_path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DRAWDB_DEFAULT_PORT: int = 8081
SPAWN_TIMEOUT_S: int = 15  # Délai max d'attente du subprocess avant re-sonde
HEALTH_CHECK_TIMEOUT_S: float = 2.0  # Timeout sonde HTTP locale

# ── Verrou anti-rebond spawn (ADR-0369 / Pilier 3) ───────────────────────────
_spawn_lock = threading.Lock()
_spawn_in_progress: bool = False


def find_dbml_files(project_name: str) -> List[Dict[str, Any]]:
    """
    Découverte récursive des *.dbml sous Projects/<projet>/.
    Retourne une liste de dicts {index, name, parent, path, size_bytes}.
    """
    proj_root = resolve_project_path(project_name)
    found: List[Dict[str, Any]] = []
    if not proj_root.exists():
        return found

    seen: set = set()
    idx = 0
    try:
        for fp in sorted(proj_root.rglob("*.dbml")):
            real = fp.resolve()
            if real in seen:
                continue
            seen.add(real)
            try:
                rel = fp.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = fp.name
            found.append(
                {
                    "index": idx,
                    "name": fp.name,
                    "parent": fp.parent.name,
                    "path": rel,
                    "size_bytes": fp.stat().st_size,
                }
            )
            idx += 1
    except Exception as exc:
        logger.debug(
            "Erreur lors du scan récursif DBML",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "find_dbml_files",
                "project": project_name,
                "error": str(exc),
            },
        )
    return found


def check_drawdb_health(port: int = DRAWDB_DEFAULT_PORT) -> bool:
    """
    Sonde HTTP GET http://localhost:<port>/ avec timeout explicite.
    Retourne True si le serveur répond, False sinon.
    """
    url = f"http://localhost:{port}/"
    try:
        with urllib_request.urlopen(url, timeout=HEALTH_CHECK_TIMEOUT_S) as resp:
            return resp.status == 200
    except (urllib_error.URLError, OSError, TimeoutError):
        return False
    except Exception as exc:
        logger.debug(
            "Sonde DrawDB health inattendue",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "check_drawdb_health",
                "port": port,
                "error": str(exc),
            },
        )
        return False
