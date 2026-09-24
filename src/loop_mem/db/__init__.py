"""
Package src/loop_mem/db/__init__.py — Shim de ré-export de la couche SQLite mLoop
(MLOOP-178-BE · extraction modulaire ADR-0202 · ADR-0369 · BR=20).

Ce package remplace l'ancien module monolithique src/loop_mem/db.py (956 L).
La surface publique est strictement inchangée : les ~20 callers existants
`from src.loop_mem.db import ...` résolvent sans aucune modification de caller.

Sous-modules (décision Grill Q1-A — Option 4 modules) :
  - _db_connection  : session context manager + DDL lazy (schéma)
  - _db_observations: CRUD observations + mémoire RHO
  - _db_lexicon     : persistance lexique métier (upsert + sync disque)
  - _db_search      : helpers JSON, recherche FTS lexique & fact-search 2.0

Legacy Q5-A : `_get_observation_conn` (connexion nue dépréciée) SUPPRIMÉ
définitivement — 0 caller production, interdit par ADR-0369 L47.
"""

from src.loop_mem.db._db_connection import (
    _INITIALIZED_DBS,
    _OBSERVATION_DB_PATH,
    _init_observation_db,
    get_observation_db_session,
)
from src.loop_mem.db._db_observations import (
    add_observation,
    add_rho_rule,
    get_observation_by_id,
    get_session_timeline,
    search_observations,
    search_rho_hybrid_solution,
    search_rho_solution,
)
from src.loop_mem.db._db_lexicon import (
    sync_project_lexicon_from_disk,
    upsert_lexicon_term,
)
from src.loop_mem.db._db_search import (
    LAYER_WEIGHTS,
    _determine_ssot_layer,
    calculate_story_fact_coverage,
    fact_search_query,
    get_active_project,
    index_project_docs_to_fts5,
    search_in_memory,
    search_lexicon_terms,
)

__all__ = [
    "get_observation_db_session",
    "add_observation",
    "search_observations",
    "get_session_timeline",
    "get_observation_by_id",
    "add_rho_rule",
    "search_rho_solution",
    "search_rho_hybrid_solution",
    "upsert_lexicon_term",
    "search_lexicon_terms",
    "sync_project_lexicon_from_disk",
    "get_active_project",
    "search_in_memory",
    "LAYER_WEIGHTS",
    "index_project_docs_to_fts5",
    "fact_search_query",
    "calculate_story_fact_coverage",
]
