# src/state/__init__.py — Package d'état mLoop (MLOOP-173-BE)
# Règle §3.2 : instance LoopState créée UNE SEULE FOIS ici.
# Tous les callers importent depuis ce module — API publique gelée.
# Rétrocompatibilité ADR-0202 : même surface que l'ancien src/state.py

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import time

from pydantic import BaseModel, Field

# ─── Sous-modules (ordre : core → accesseurs → serializer) ───────────────────
from src.state._state_core import (  # noqa: F401
    AnalysisResult,
    Clarification,
    Directives,
    IntegrityError,
    JournalEntry,
    KnowledgeGraph,
    LoopPhase,
    LoopStateError,
    MaxRevisionsReached,
    PlanResult,
    PlanStep,
    ProjectLayout,
    ProjectMode,
    QAReport,
    SavepointManager,
    SprintBacklogItem,
    StoryStatus,
    StoryType,
    TokenBudget,
    _load_adr_contracts,
    logger,
)
from src.state._state_accessors import StateAccessorsMixin  # noqa: F401
from src.state._state_serializer import StateSerializerMixin  # noqa: F401


# ─── Classe LoopState assemblée (Q2 Mixin Option A) ─────────────────────────


class LoopState(StateAccessorsMixin, StateSerializerMixin, BaseModel):
    """
    État partagé du cycle de vie mLoop.
    Assemblée à partir de :
      - StateAccessorsMixin : transitions FSM, query_graph, search_nodes
      - StateSerializerMixin : checkpoint, save_to_graph, load_from_graph, audit, journal
      - BaseModel (Pydantic) : sérialisation, validation, model_fields
    Instance unique créée dans ce module (règle §3.2).
    """

    project_name: str
    project_mode: ProjectMode = ProjectMode.CLIENT
    current_phase: LoopPhase = LoopPhase.SPEC
    previous_phase: Optional[LoopPhase] = None
    current_state_id: Optional[str] = None
    session_start_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ─── IN-FLIGHT CHECKPOINTING (ADR-0352 / HARNESSDEV) ───
    last_checkpoint_timestamp: float = Field(default_factory=lambda: time.time())
    checkpoint_interval_seconds: int = 60  # Intervalle temporel configurable (60 à 90 secondes)

    # ─── ARTEFACTS FSM ───
    analysis: Optional[AnalysisResult] = None
    plan: Optional[PlanResult] = None
    qa_report: Optional[QAReport] = None

    directives: Directives = Field(default_factory=Directives)
    knowledge_graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    clarifications: List[Clarification] = Field(default_factory=list)
    sprint_backlog: List[SprintBacklogItem] = Field(default_factory=list)

    # ─── ONTOLOGIE COWORKER (L1) ───
    journal: List[JournalEntry] = Field(default_factory=list)

    # ─── NOUVEAUX CHAMPS D'INTÉGRATION ───
    jira_project_key: Optional[str] = None
    jira_epic_key: Optional[str] = None
    jira_default_component_id: Optional[str] = None
    jira_default_billing_id: Optional[str] = None
    jira_default_subtasks: List[str] = Field(default_factory=list)
    jira_subtask_mapping: Dict[str, str] = Field(default_factory=dict)
    ingested_sources: List[Dict[str, Any]] = Field(default_factory=list)

    # ─── INGESTION PAR INITIATIVE / MODULE (Voie B — routage scopé) ───
    # Quand renseigné, l'ingestion scanne uniquement reference/<initiative>/
    # et écrit sous docs/<initiative>/00-ingested/ (projets à structure par module,
    # ex: Metro_FOOD → OneTrust, RBC_Avion, PAPERCUTS). Sinon: comportement ADR-0102 plat.
    ingest_initiative: Optional[str] = None

    token_budget: TokenBudget = Field(default_factory=TokenBudget)
    hitl_required: bool = Field(default=False)

    # ─── GRAPHIFY INTEGRATION (ADR-0018) ─────────────────────────
    graph_path: str = "graphify-out/graph.json"


# ─── Surface publique (__all__) ──────────────────────────────────────────────

__all__ = [
    # Classe principale
    "LoopState",
    # Mixins (exposés pour import direct si besoin)
    "StateAccessorsMixin",
    "StateSerializerMixin",
    # Exceptions
    "LoopStateError",
    "IntegrityError",
    "MaxRevisionsReached",
    # Enums
    "LoopPhase",
    "ProjectMode",
    "StoryType",
    "StoryStatus",
    # Modèles Pydantic
    "TokenBudget",
    "Directives",
    "KnowledgeGraph",
    "Clarification",
    "SprintBacklogItem",
    "AnalysisResult",
    "PlanStep",
    "PlanResult",
    "QAReport",
    "JournalEntry",
    # Utilitaires
    "SavepointManager",
    "ProjectLayout",
    "_load_adr_contracts",
    "logger",
]
