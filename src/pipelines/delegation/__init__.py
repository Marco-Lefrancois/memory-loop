"""
src/pipelines/delegation - Specialized Worker Delegation Pipelines for mLoop Engine
Propelled by Herdr Runtime v0.8.2+
"""

from .handoff_simulator import run_handoff_simulator
from .legacy_miner import run_legacy_miner
from .shadow_estimator import run_shadow_estimator
from .visual_dissector import run_visual_dissector
from .semantic_janitor import run_semantic_janitor, SemanticJanitorWatcher

__all__ = [
    "run_handoff_simulator",
    "run_legacy_miner",
    "run_shadow_estimator",
    "run_visual_dissector",
    "run_semantic_janitor",
    "SemanticJanitorWatcher",
]
