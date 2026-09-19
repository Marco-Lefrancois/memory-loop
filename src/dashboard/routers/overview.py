"""
src/dashboard/routers/overview.py — Routeur FastAPI pour la Vue d'Ensemble Cockpit (ADR-0369).

Agrège la télémétrie systémique globale : résilience, Dream RSI, essaim et cycle FSM.
Fournit le moteur de métrologie de la jauge contextuelle 3-zones (MLOOP-073-FE, ADR-0324).
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import json
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


class ContextGaugeEngine:
    """
    Moteur de diagnostic et métrologie de la charge contextuelle (ADR-0324 & ADR-0380).
    Évalue la saturation cognitive en 3 zones d'attention (Smart, Caution, Dumb Zone).
    """

    @classmethod
    def evaluate_context(
        cls, tokens_used: int, window_size: int = 128000
    ) -> Dict[str, Any]:
        """
        Calcule les ratios et assigne la zone cognitive d'après la charge en tokens.
        """
        w_size = max(1, window_size)
        used = max(0, tokens_used)
        ratio = used / w_size
        percentage = round(ratio * 100)

        if ratio < 0.40:
            zone = "SMART"
            zone_label = "SMART ZONE"
            zone_color = "emerald"
            badge_text = f"🟢 SMART ZONE : {percentage}%"
            recommendation = "Attention cognitive optimale. Aucune action requise."
            is_critical = False
        elif ratio <= 0.60:
            zone = "CAUTION"
            zone_label = "CAUTION ZONE"
            zone_color = "amber"
            badge_text = f"🟡 CAUTION ZONE : {percentage}%"
            recommendation = "Zone de vigilance (40-60%). Un compactage préventif est recommandé."
            is_critical = False
        else:
            zone = "DUMB"
            zone_label = "DUMB ZONE"
            zone_color = "rose"
            badge_text = f"🔴 DUMB ZONE : {percentage}%"
            recommendation = "Zone critique (>60%). Scission recommandée vers un worker clean-slate."
            is_critical = True

        return {
            "tokens_used": used,
            "window_size": w_size,
            "ratio": ratio,
            "percentage": percentage,
            "zone": zone,
            "zone_label": zone_label,
            "zone_color": zone_color,
            "badge_text": badge_text,
            "recommendation": recommendation,
            "is_critical": is_critical,
        }

    @classmethod
    def get_project_context_usage(cls, proj_path: Path) -> int:
        """
        Extrait l'empreinte de contexte active pour le projet cible.
        Consulte memory/token_ledger.jsonl ou memory/events.jsonl avec context manager.
        """
        ledger_file = proj_path / "memory" / "token_ledger.jsonl"
        events_file = proj_path / "memory" / "events.jsonl"

        # 1. Inspection de token_ledger.jsonl (dernières entrées de session)
        if ledger_file.exists():
            try:
                tokens_acc = 0
                with open(ledger_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines[-10:]:
                    try:
                        entry = json.loads(line)
                        tokens_acc += entry.get("prompt_tokens_est", 0) + entry.get("completion_tokens_est", 0)
                    except json.JSONDecodeError:
                        continue
                if tokens_acc > 0:
                    return min(tokens_acc, 128000)
            except Exception as e:
                logger.debug(f"[CONTEXT_GAUGE] Lecture ledger ignorée : {e}", exc_info=True)

        # 2. Inspection fallback dans events.jsonl
        if events_file.exists():
            try:
                tokens_acc = 0
                with open(events_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines[-10:]:
                    try:
                        entry = json.loads(line)
                        usage = entry.get("gen_ai.usage", {})
                        if isinstance(usage, dict):
                            tokens_acc += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
                        elif "tokens" in entry:
                            tokens_acc += entry.get("tokens", 0)
                    except json.JSONDecodeError:
                        continue
                if tokens_acc > 0:
                    return min(tokens_acc, 128000)
            except Exception as e:
                logger.debug(f"[CONTEXT_GAUGE] Lecture events ignorée : {e}", exc_info=True)

        # Valeur nominale pour session active sans historique lourd
        return 12500


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


@router.get("/context-health")
def get_context_health(
    project: Optional[str] = Query(None),
    tokens: Optional[int] = Query(None),
    window: int = Query(128000),
) -> Dict[str, Any]:
    """
    Retourne l'état d'encombrement contextuel de la session active (ADR-0324 & ADR-0380).
    """
    proj_name = resolve_project_canonical_name(project)
    proj_path = resolve_project_path(proj_name)

    if tokens is not None:
        tokens_used = tokens
    else:
        tokens_used = ContextGaugeEngine.get_project_context_usage(proj_path)

    metrics = ContextGaugeEngine.evaluate_context(tokens_used=tokens_used, window_size=window)
    metrics["project_name"] = proj_name
    return metrics
