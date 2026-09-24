"""
src/core/lifecycle/__init__.py — Package de gouvernance du cycle de vie mLoop
SSOT Normatif : ADR-0339 / ADR-0375

Ré-exporte tous les symboles publics pour garantir la rétrocompatibilité
des 10 callers sans aucune modification de leur côté.

Symboles garantis :
  - ProjectLifecycleStage, ProjectLifecycleState, GateApprovalRecord
  - STAGE_ORDER, STAGE_NAMES, GATE_DEFINITIONS
  - COMMAND_MIN_STAGE, WORKER_TASK_TYPE_MIN_STAGE
  - ProjectLifecycleManager
  - logger  (exposé pour la rétrocompatibilité des tests de patching)
"""

from src.utils.logger import get_logger

# Logger exposé au niveau du package pour rétrocompatibilité avec patch.object(lifecycle, "logger")
# Les sous-modules utilisent _lc_logger.logger (proxy qui délègue ici dynamiquement)
logger = get_logger("core.lifecycle")

from ._lc_models import (  # noqa: E402
    COMMAND_MIN_STAGE,
    GATE_DEFINITIONS,
    STAGE_NAMES,
    STAGE_ORDER,
    WORKER_TASK_TYPE_MIN_STAGE,
    GateApprovalRecord,
    ProjectLifecycleStage,
    ProjectLifecycleState,
)
from ._lc_manager import ProjectLifecycleManager  # noqa: E402

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
    "logger",
]
