"""
src/dashboard/routers/swarm.py — Routeur FastAPI pour la Topologie de l'Essaim (ADR-0371).

Expose la cartographie des 6 rôles d'agents, leurs périmètres de sécurité,
les scores de Blast Radius et les autorisations Unattended.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from src.dashboard.cache import get_cached_or_compute
from src.pipelines.resilience.topology import AgentTopologyMapper

router = APIRouter(prefix="/api/swarm", tags=["Swarm & Agents"])


@router.get("/topology")
def get_swarm_topology(project: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Retourne la cartographie topologique de l'essaim multi-agents et la matrice de Blast Radius.
    """
    def _compute() -> Dict[str, Any]:
        topologies = AgentTopologyMapper.list_all_topologies()
        agents_data: List[Dict[str, Any]] = []
        unattended_count = 0

        for top in topologies:
            calc = AgentTopologyMapper.compute_blast_radius(top.role)
            if top.unattended_safe:
                unattended_count += 1

            agents_data.append(
                {
                    "role": top.role,
                    "name": top.role.capitalize(),
                    "description": top.description,
                    "blast_radius_level": top.blast_radius_level.value,
                    "blast_score": calc["blast_score"],
                    "unattended_authorized": top.unattended_safe,
                    "authorized_write_paths": top.authorized_write_paths,
                    "forbidden_paths": top.forbidden_paths,
                    "allowed_tools": top.allowed_tools,
                    "connected_partitions": top.connected_memory_partitions,
                    "status": "ACTIVE" if top.role in ("orchestrator", "worker", "sentinel") else "READY",
                }
            )

        return {
            "project": project or "Global",
            "total_agents": len(topologies),
            "unattended_safe_count": unattended_count,
            "hitl_required_count": len(topologies) - unattended_count,
            "agents": agents_data,
        }

    return get_cached_or_compute("swarm_topology", None, _compute, ttl_seconds=10.0)
