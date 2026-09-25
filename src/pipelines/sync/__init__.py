"""
src/pipelines/sync/__init__.py — Shim de ré-export du package sync.

Ce module garantit la rétrocompatibilité transparente des 10 callers existants
qui importaient depuis l'ancien monolithe src/pipelines/sync.py :

    from src.pipelines.sync import run_sync
    from src.pipelines.sync import sync_hypergraph
    from src.pipelines.sync import *

Aucun caller n'est modifié — le shim résout tout import historique (ADR-0202).
Le logger est ré-exposé ici pour maintenir la compatibilité avec les tests qui
patchent ``src.pipelines.sync.logger`` (test_sync_logging.py, MLOOP-141-BE).
Les agents WikiFixAgent et GraphifyAgent sont ré-exposés pour les mêmes raisons.

Modèle : package src/pipelines/db/ (MLOOP-178-BE).
"""

# Logger racine — importé depuis _sync_run pour garantir l'unicité de la référence.
# patch.object(sync, "logger") dans les tests cible le même objet que _sync_run.logger.
from src.pipelines.sync._sync_run import logger  # noqa: E402

# Agents — ré-exposés pour la patchabilité des tests (patch("src.pipelines.sync.WikiFixAgent"))
from src.pipelines.wikifix import WikiFixAgent
from src.pipelines.graphify.agent import GraphifyAgent

# Sous-modules docs
from src.pipelines.sync._sync_docs import (
    load_sync_cache,
    save_sync_cache,
    sync_project_directives,
    sync_open_questions,
    sync_sprint_backlog,
)
from src.pipelines.sync._sync_archive import auto_archive_completed_epics

# Sous-modules graph
from src.pipelines.sync._sync_graph import (
    sync_live_reference_wikis,
    sync_hypergraph,
)

# Orchestrateur
from src.pipelines.sync._sync_run import run_sync

__all__ = [
    # logger (compatibilité tests)
    "logger",
    # agents (compatibilité tests)
    "WikiFixAgent",
    "GraphifyAgent",
    # cache
    "load_sync_cache",
    "save_sync_cache",
    # docs
    "sync_project_directives",
    "sync_open_questions",
    "sync_sprint_backlog",
    "auto_archive_completed_epics",
    # graph
    "sync_live_reference_wikis",
    "sync_hypergraph",
    # orchestrateur
    "run_sync",
]

