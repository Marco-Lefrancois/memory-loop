"""
src/dashboard/routers/governance.py — Routeur FastAPI pour les Portes FSM & Gouvernance (ADR-0339).

Expose l'avancement séquentiel des 6 Portes de Gouvernance (Gate 0 à 5),
l'état de conformité DoR/DoD et permet l'approbation interactive.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.dashboard.cache import get_cached_or_compute
from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path
from src.core.lifecycle import (
    GATE_DEFINITIONS,
    STAGE_NAMES,
    ProjectLifecycleManager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/governance", tags=["Gouvernance & Portes FSM"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class GateApprovalRequest(BaseModel):
    project: Optional[str] = "mLoop"
    gate: int
    approver: Optional[str] = "TechLead (Dashboard)"
    notes: Optional[str] = "Validation manuelle via le Dashboard Agentique mLoop"


@router.get("/gates")
def get_governance_gates(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Retourne l'état des 6 Portes de Gouvernance (Gate 0 à 5) et l'étape FSM active.
    """
    proj_name = resolve_project_canonical_name(project)
    proj_path = resolve_project_path(proj_name)

    def _compute() -> Dict[str, Any]:
        lc_state = ProjectLifecycleManager.get_state(proj_path)
        current_stage = lc_state.current_stage
        approved_set = {int(k) for k in lc_state.gates.keys()}

        gates_list: List[Dict[str, Any]] = []
        for g_num in range(6):
            g_def = GATE_DEFINITIONS.get(g_num, {})
            is_approved = g_num in approved_set
            # Détection de la porte active
            is_current = False
            if g_def.get("from_stage") == current_stage and not is_approved:
                is_current = True

            gates_list.append(
                {
                    "gate_number": g_num,
                    "name": g_def.get("name", f"Gate {g_num}"),
                    "from_stage": g_def.get("from_stage", "").value if hasattr(g_def.get("from_stage"), "value") else str(g_def.get("from_stage")),
                    "to_stage": g_def.get("to_stage", "").value if hasattr(g_def.get("to_stage"), "value") else str(g_def.get("to_stage")),
                    "description": g_def.get("description", ""),
                    "is_approved": is_approved,
                    "is_active_target": is_current,
                }
            )

        return {
            "project_name": proj_name,
            "current_stage": current_stage.value,
            "current_stage_label": STAGE_NAMES.get(current_stage, current_stage.value),
            "gates": gates_list,
            "total_approved": len(approved_set),
            "history_entries": len(lc_state.gates),
        }

    cache_key = f"governance_gates_{proj_path.as_posix()}"
    return get_cached_or_compute(cache_key, proj_path / "memory", _compute, ttl_seconds=3.0)


@router.post("/approve")
def approve_gate(req: GateApprovalRequest) -> Dict[str, Any]:
    """
    Valide formellement une porte de gouvernance pour le projet.
    """
    proj_path = resolve_project_path(req.project)
    try:
        updated_state = ProjectLifecycleManager.approve_gate(
            project_path=proj_path,
            gate_number=req.gate,
            approver=req.approver or "Dashboard HITL",
            notes=req.notes or "",
        )
        return {
            "success": True,
            "gate_approved": req.gate,
            "new_stage": updated_state.current_stage.value,
            "message": f"Porte {req.gate} approuvée avec succès.",
        }
    except Exception as e:
        logger.error("Échec de validation de la porte", exc_info=True, extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))
