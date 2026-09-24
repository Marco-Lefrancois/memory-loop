"""
mcp_recall.py — Auto-Recall Sémantique Passif & cache de préchargement (ADR-0308).

Extraction du socle de mémoire du pont MCP ``mcp_loop_mem`` afin de préserver le
plafond modulaire ADR-0202 (≤ 300 lignes) : ces fonctions ne dépendent d'aucun
protocole MCP, uniquement de la mémoire SQLite / du graphe de connaissance.

``_PRELOAD_CACHE`` reste la source partagée (même objet dict) consommée par les
tests, le SDK client et le pipeline d'unlearning — aucune reconnexion.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from pathlib import Path

# Activer l'import depuis la racine du projet (bridges lancés en script direct)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logger = logging.getLogger(__name__)

_PRELOAD_CACHE: dict = {}


def log_error(msg: str) -> None:
    """Journalise une erreur sur la sortie standard d'erreur du pont MCP."""
    sys.stderr.write(f"[MCP LOOP-MEM] {msg}\n")
    sys.stderr.flush()


def _session_project() -> str | None:
    """Projet porté par la session courante (lecture différée, anti-cycle)."""
    from src.bridges.mcp_loop_mem import _SESSION_PROJECT

    return _SESSION_PROJECT


def auto_recall_passive_memory(
    story_id: str | None = None, query: str | None = None, project: str | None = None
) -> list:
    """
    Axe 1 jcode (ADR-0308) : Auto-Recall Sémantique Passif.
    """
    from src.loop_mem.db import search_observations, get_active_project

    proj = project or _session_project() or get_active_project() or "mLoop"
    recalled_items = []

    if story_id and story_id in _PRELOAD_CACHE:
        cached_data = _PRELOAD_CACHE[story_id]
        nodes = cached_data.get("nodes", [])[:3]
        for n in nodes:
            name = n.get("name") if isinstance(n, dict) else str(n)
            recalled_items.append(
                {
                    "source": "RAM_Cache",
                    "type": "engramme_graphe",
                    "summary": f"Nœud sémantique: {name}",
                }
            )

    search_term = query or story_id or "architecture"
    try:
        obs_matches = search_observations(query=search_term, project_name=proj) or []
        for obs in obs_matches[:3]:
            recalled_items.append(
                {
                    "source": "Memory_SQLite",
                    "type": obs.get("type", "observation"),
                    "id": obs.get("id"),
                    "summary": obs.get("content", "")[:120] + "...",
                }
            )
    except Exception as exc:
        logger.debug(f"Erreur Auto-Recall sémantique passif: {exc}", exc_info=True)
        log_error(f"Erreur lors de l'Auto-Recall sémantique passif: {exc}")

    return recalled_items[:5]


def preload_story_context(story_id: str, project: str | None = None) -> dict:
    from src.loop_mem.db import get_active_project

    proj = project or _session_project() or get_active_project() or "mLoop"
    graph_path = Path("Projects") / proj / "memory" / "knowledge_graph.json"

    nodes_cached = 0
    if graph_path.exists():
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

            relevant_nodes = [n for n in nodes if story_id.lower() in str(n).lower()]
            if not relevant_nodes:
                relevant_nodes = nodes[:10]

            _PRELOAD_CACHE[story_id] = {
                "story_id": story_id,
                "project": proj,
                "nodes": relevant_nodes,
                "edges": edges,
                "timestamp": str(uuid.uuid4()),
            }
            nodes_cached = len(relevant_nodes)
        except Exception as exc:
            logger.debug(f"Erreur lors du préchargement de {story_id}: {exc}", exc_info=True)
            log_error(f"Erreur lors du préchargement de {story_id}: {exc}")

    passive_engrams = auto_recall_passive_memory(story_id=story_id, project=proj)

    return {
        "status": "preloaded",
        "story_id": story_id,
        "nodes_cached": nodes_cached,
        "auto_recall_engrams": len(passive_engrams),
        "memory_used_kb": len(json.dumps(_PRELOAD_CACHE.get(story_id, {}))) // 1024,
    }


def clear_preloaded_context(story_id: str | None = None) -> dict:
    if story_id:
        _PRELOAD_CACHE.pop(story_id, None)
    else:
        _PRELOAD_CACHE.clear()
    return {"status": "cleared", "remaining_keys": list(_PRELOAD_CACHE.keys())}
