"""
src/dashboard/cache.py — Cache Mémoire Léger avec Invalidation mtime (ADR-0369).

Évite les I/O disque répétitifs lors des requêtes fréquentes du Dashboard (polling 2-5s).
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

_CACHE_STORE: Dict[str, Tuple[float, float, Any]] = {}  # key -> (mtime, cached_at, data)


def get_cached_or_compute(
    key: str,
    file_path: Optional[Path],
    compute_fn: Callable[[], Any],
    ttl_seconds: float = 3.0,
) -> Any:
    """
    Récupère la valeur en cache si valide par rapport au mtime du fichier cible et au TTL.
    """
    now = time.time()
    current_mtime = 0.0

    if file_path and file_path.exists():
        try:
            current_mtime = file_path.stat().st_mtime
        except OSError:
            current_mtime = 0.0

    if key in _CACHE_STORE:
        last_mtime, cached_at, data = _CACHE_STORE[key]
        # Invalidation si le fichier a changé ou si le TTL est expiré
        if file_path and file_path.exists():
            if last_mtime == current_mtime and (now - cached_at) < ttl_seconds:
                return data
        else:
            if (now - cached_at) < ttl_seconds:
                return data

    # Calcul et mise en cache
    result = compute_fn()
    _CACHE_STORE[key] = (current_mtime, now, result)
    return result


def clear_dashboard_cache() -> None:
    """Vide l'ensemble du cache mémoire du dashboard."""
    _CACHE_STORE.clear()
