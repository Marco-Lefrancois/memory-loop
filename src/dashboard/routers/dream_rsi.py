"""
src/dashboard/routers/dream_rsi.py — Routeur FastAPI pour Dream RSI & Auto-Amélioration (ADR-0372).

Expose le diagnostic d'isolation du harnais (radar 4 pannes), les méta-politiques arborescentes,
la courbe de gain monotone et la télémétrie du simulateur de replay hors-ligne.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Query

from src.dashboard.cache import get_cached_or_compute
from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path
from src.pipelines.dream_rsi import (
    DreamExplorer,
    ModularHarnessIsolator,
    ReplaySimulator,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dream-rsi", tags=["Dream RSI Laboratory"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@router.get("/summary")
def get_dream_rsi_summary(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Retourne la synthèse complète Dream RSI : radar des 4 pannes, politiques et simulateur.
    """
    proj_name = resolve_project_canonical_name(project)
    proj_path = resolve_project_path(proj_name)

    def _compute() -> Dict[str, Any]:
        episodes = ReplaySimulator.load_from_project(proj_path)
        diagnosis = ModularHarnessIsolator.analyze(episodes)
        best_res, all_res = DreamExplorer.explore(episodes)

        # Vérification d'une politique appliquée sur disque
        policy_file = proj_path / ".mloop" / "dream_policy.json"
        is_applied = policy_file.exists()
        applied_data = {}
        if is_applied:
            try:
                with open(policy_file, "r", encoding="utf-8") as f:
                    applied_data = json.load(f)
            except Exception:
                pass

        # Calcul des tokens économisés par le simulateur offline
        total_steps_simulated = sum(len(ep) for ep in episodes) * 10
        tokens_saved = total_steps_simulated * 180

        # Sérialisation des candidats pour le graphique de frontière
        candidates_data = []
        for r in all_res:
            candidates_data.append(
                {
                    "name": r.policy.name,
                    "branching": r.policy.branching_factor,
                    "patience": r.policy.patience,
                    "threshold": r.policy.early_stopping_threshold,
                    "strategy": r.policy.strategy,
                    "success_rate": round(r.simulated_success_rate * 100.0, 1),
                    "efficiency": round(r.cost_efficiency_score, 3),
                    "gain_vs_pi0": r.gain_vs_pi0,
                }
            )

        return {
            "project_name": proj_name,
            "episodes_simulated": len(episodes),
            "tokens_saved_estimate": tokens_saved,
            "harness_diagnosis": {
                "primary_bottleneck": diagnosis.primary_bottleneck,
                "distribution": diagnosis.distribution,
                "score": diagnosis.isolated_harness_score,
                "recommendations": diagnosis.recommendations,
            },
            "selected_policy": {
                "name": best_res.policy.name,
                "branching_factor": best_res.policy.branching_factor,
                "patience": best_res.policy.patience,
                "early_stopping_threshold": best_res.policy.early_stopping_threshold,
                "strategy": best_res.policy.strategy,
                "success_rate": round(best_res.simulated_success_rate * 100.0, 1),
                "gain_vs_pi0": best_res.gain_vs_pi0,
            },
            "applied_on_disk": is_applied,
            "applied_policy": applied_data,
            "candidates_frontier": candidates_data,
        }

    cache_key = f"dream_rsi_summary_{proj_path.as_posix()}"
    return get_cached_or_compute(cache_key, proj_path / "memory", _compute, ttl_seconds=3.0)
