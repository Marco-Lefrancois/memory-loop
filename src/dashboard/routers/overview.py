"""
src/dashboard/routers/overview.py — Routeur FastAPI pour la Vue d'Ensemble Cockpit (ADR-0369).

Agrège la télémétrie systémique globale : résilience, Dream RSI, essaim et cycle FSM.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Query

from src.dashboard.cache import get_cached_or_compute
from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path
from src.core.lifecycle import ProjectLifecycleManager, STAGE_NAMES
from src.pipelines.agent_resilience import ResilienceAudit
from src.pipelines.dream_rsi import (
    DreamExplorer,
    ModularHarnessIsolator,
    ReplaySimulator,
)
from src.pipelines.resilience.topology import AgentTopologyMapper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/overview", tags=["Cockpit Overview"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@router.get("/stats")
def get_cockpit_stats(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Retourne la télémétrie systémique consolidée pour le Cockpit Overview.
    """
    proj_name = resolve_project_canonical_name(project)
    proj_path = resolve_project_path(proj_name)

    def _compute() -> Dict[str, Any]:
        # 1. Résilience
        res_audit = ResilienceAudit.audit(proj_name, project_path=proj_path)

        # 2. Dream RSI
        episodes = ReplaySimulator.load_from_project(proj_path)
        diagnosis = ModularHarnessIsolator.analyze(episodes)
        best_res, _ = DreamExplorer.explore(episodes)

        # 3. Swarm
        topologies = AgentTopologyMapper.list_all_topologies()
        unattended_count = sum(1 for t in topologies if t.unattended_safe)

        # 4. Cycle FSM
        lc_state = ProjectLifecycleManager.get_state(proj_path)
        curr_stage = lc_state.current_stage

        return {
            "project_name": proj_name,
            "resilience": {
                "score": res_audit["resilience_index"],
                "status": res_audit["status"],
                "checkpoints_count": res_audit["checkpoints"]["count"],
                "evidence_valid": res_audit["evidence"]["valid"],
                "evidence_total": res_audit["evidence"]["total"],
                "memory_hygiene_ok": res_audit["memory_hygiene"]["ok"],
                "memory_lines": res_audit["memory_hygiene"]["lines"],
            },
            "dream_rsi": {
                "gain_vs_pi0": best_res.gain_vs_pi0,
                "best_policy": best_res.policy.name,
                "harness_score": diagnosis.isolated_harness_score,
                "bottleneck": diagnosis.primary_bottleneck,
                "episodes_count": len(episodes),
            },
            "swarm": {
                "total_roles": len(topologies),
                "unattended_safe": unattended_count,
                "hitl_required": len(topologies) - unattended_count,
            },
            "lifecycle": {
                "current_stage": curr_stage.value,
                "stage_label": STAGE_NAMES.get(curr_stage, curr_stage.value),
            },
        }

    cache_key = f"overview_stats_{proj_path.as_posix()}"
    return get_cached_or_compute(cache_key, proj_path / "memory", _compute, ttl_seconds=3.0)
