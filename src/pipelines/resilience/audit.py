"""
Audit de cyber-résilience et étape composable PipelineStage (ADR-0202, ADR-0369 & ADR-0371).
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.cli import ZeroFluffConsole
from src.pipelines.base import PipelineStage
from src.pipelines.resilience.rollback import AgentStateRollbackEngine
from src.pipelines.resilience.topology import AgentTopologyMapper
from src.state import LoopState


class ResilienceAudit:
    """
    Auditeur de la posture globale de résilience agentique (ADR-0371).
    """

    @classmethod
    def audit(
        cls, project_name: str, project_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        target_path = project_path or (Path("Projects") / project_name)

        points = AgentStateRollbackEngine.list_restore_points(target_path)
        cp_count = len(points)
        cp_score = min(100, cp_count * 34)

        evidence_audit = AgentStateRollbackEngine.verify_evidence_integrity(target_path)
        ev_total = evidence_audit["total"]
        ev_valid = evidence_audit["valid"]
        ev_score = int((ev_valid / ev_total * 100)) if ev_total > 0 else 100

        health_file = target_path / "memory" / "SESSION_MEMORY_HEALTH.md"
        memory_hygiene_ok = True
        health_lines = 0
        health_bytes = 0
        if health_file.exists():
            health_bytes = health_file.stat().st_size
            health_lines = len(health_file.read_text(encoding="utf-8", errors="ignore").splitlines())
            if health_lines > 200 or health_bytes > 25600:
                memory_hygiene_ok = False

        topologies = AgentTopologyMapper.list_all_topologies()

        weights = [cp_score * 0.35, ev_score * 0.35, (100 if memory_hygiene_ok else 40) * 0.30]
        resilience_index = int(sum(weights))

        status = "EXCELLENT" if resilience_index >= 85 else ("STABLE" if resilience_index >= 65 else "AT_RISK")

        return {
            "project_name": project_name,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "resilience_index": resilience_index,
            "status": status,
            "checkpoints": {
                "count": cp_count,
                "score": cp_score,
                "latest": points[0]["filename"] if points else None,
            },
            "evidence": {
                "total": ev_total,
                "valid": ev_valid,
                "score": ev_score,
            },
            "memory_hygiene": {
                "ok": memory_hygiene_ok,
                "lines": health_lines,
                "bytes": health_bytes,
                "limit_lines": 200,
            },
            "topologies_mapped": len(topologies),
        }


class AgentResilienceStage(PipelineStage):
    """
    Étape de pipeline mLoop composable (src/pipelines/base.py)
    permettant l'audit de résilience automatique au sein de la composition :
        pipeline = IngestStage() | AgentResilienceStage() | WikiFixStage()
    """

    def __init__(self, name: str = "AgentResilienceStage"):
        super().__init__(name=name)

    def execute(self, state: LoopState) -> LoopState:
        proj_name = state.project_name or "mLoop"
        proj_path = Path("Projects") / proj_name if state.project_name else Path(".")
        audit_res = ResilienceAudit.audit(proj_name, project_path=proj_path)
        score = audit_res["resilience_index"]
        status = audit_res["status"]
        ZeroFluffConsole.step_s1(self.name, f"Posture de résilience : {status} ({score}/100)")
        return state
