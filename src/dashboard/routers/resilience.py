"""
src/dashboard/routers/resilience.py — Routeur FastAPI pour la Cyber-Résilience & PITR (ADR-0371).

Expose la posture de résilience, la timeline des checkpoints SHA-256,
l'intégrité des EvidencePacks et le déclenchement de rollback.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.dashboard.cache import get_cached_or_compute
from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path
from src.pipelines.agent_resilience import (
    AgentStateRollbackEngine,
    ResilienceAudit,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resilience", tags=["Cyber-Résilience & PITR"])
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class RollbackRequest(BaseModel):
    project: Optional[str] = "mLoop"
    step: int = 1
    target_partition: Optional[str] = None


@router.get("/posture")
def get_resilience_posture(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Retourne la posture globale de cyber-résilience (score, checkpoints SHA-256, EvidencePacks).
    """
    proj_name = resolve_project_canonical_name(project)
    proj_path = resolve_project_path(proj_name)

    def _compute() -> Dict[str, Any]:
        audit_res = ResilienceAudit.audit(proj_name, project_path=proj_path)
        points = AgentStateRollbackEngine.list_restore_points(proj_path)

        # Enrichissement des points de restauration
        formatted_points = []
        for pt in points:
            formatted_points.append(
                {
                    "step": pt["step"],
                    "filename": pt["filename"],
                    "phase": pt.get("phase", "spec"),
                    "datetime_utc": pt.get("datetime_utc", ""),
                    "sha256": pt.get("sha256", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
                    "size_bytes": pt.get("size_bytes", 0),
                }
            )

        audit_res["detailed_checkpoints"] = formatted_points
        return audit_res

    cache_key = f"resilience_posture_{proj_path.as_posix()}"
    return get_cached_or_compute(cache_key, proj_path / "memory", _compute, ttl_seconds=3.0)


@router.post("/rollback")
def execute_rollback(req: RollbackRequest) -> Dict[str, Any]:
    """
    Exécute ou simule une restauration déterministe point-in-time vers un checkpoint.
    """
    proj_path = resolve_project_path(req.project)
    result = AgentStateRollbackEngine.rollback_to_checkpoint(
        project_path=proj_path,
        step_number=req.step,
        target_partition=req.target_partition,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Échec du rollback"))
    return result
