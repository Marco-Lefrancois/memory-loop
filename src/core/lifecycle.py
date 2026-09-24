"""
src/core/lifecycle.py — SHIM de ré-export (MLOOP-174-BE)

Ce fichier est MASQUÉ par le package src/core/lifecycle/ (Python privilégie
le package sur le module fichier). Il est conservé à titre de garde-fou
documentaire et de compatibilité filesystem.

⚠️  NE PAS MODIFIER — Toute la logique réside dans src/core/lifecycle/
    _lc_models.py / _lc_transitions.py / _lc_gates.py / _lc_manager.py

Rétrocompatibilité garantie via src/core/lifecycle/__init__.py
"""

# Ce module ne sera jamais importé tant que le package lifecycle/ existe.
# Fourni uniquement comme fallback de documentation.
from src.core.lifecycle import (  # noqa: F401  # type: ignore[no-redef]
    COMMAND_MIN_STAGE,
    GATE_DEFINITIONS,
    STAGE_NAMES,
    STAGE_ORDER,
    WORKER_TASK_TYPE_MIN_STAGE,
    GateApprovalRecord,
    ProjectLifecycleManager,
    ProjectLifecycleStage,
    ProjectLifecycleState,
)

__all__ = [
    "ProjectLifecycleStage",
    "ProjectLifecycleState",
    "GateApprovalRecord",
    "STAGE_ORDER",
    "STAGE_NAMES",
    "GATE_DEFINITIONS",
    "COMMAND_MIN_STAGE",
    "WORKER_TASK_TYPE_MIN_STAGE",
    "ProjectLifecycleManager",
]
