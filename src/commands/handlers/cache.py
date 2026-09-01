"""Handlers Cache : cache-stats, cache-clear (ADR-0336)."""

import argparse
from pathlib import Path
from src.state import LoopState
from src.cli import ZeroFluffConsole
from src.core.semantic_cache import SemanticCache


def handle_cache_stats(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Afficher les statistiques du cache sémantique LLM."""
    cache = SemanticCache()
    stats = cache.stats()
    ZeroFluffConsole.step_s1("Semantic Cache", "Statistiques du Cache Déterministe LLM")
    print(f"  • Entrées en cache : {stats['total_entries']}")
    print(f"  • Requêtes servies (Hits) : {stats['total_hits']}")
    print(f"  • Tokens économisés (est.) : {stats['saved_tokens_est']}")
    print(f"  • Base de données : {stats['db_path']}")
    return 0


def handle_cache_clear(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Effacer le cache sémantique LLM."""
    cache = SemanticCache()
    deleted = cache.clear(model=getattr(args, "model", None))
    ZeroFluffConsole.success(f"Cache sémantique effacé ({deleted} entrées supprimées).")
    return 0
