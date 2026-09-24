"""
src/dashboard/routers/tooling.py — Routeur FastAPI pour la Santé de l'Écosystème Tooling (MLOOP-223-FE).

Supervise la disponibilité des runtimes développeur :
  - OpenCode CLI
  - Plannotator
  - LiteLLM Local Proxy (port 4000)
  - Graphify Knowledge Engine
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from src.commands.handlers.opencode import check_litellm_connectivity, is_opencode_available
from src.commands.handlers.plannotator import _get_plannotator_binary
from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path

logger = logging.getLogger("dashboard.routers.tooling")
router = APIRouter(prefix="/api/tooling", tags=["Developer Tooling"])


def _check_graphify() -> Dict[str, Any]:
    """Vérifie la disponibilité de l'outil Graphify."""
    bin_path = shutil.which("graphify")
    has_out = (Path("graphify-out").exists() and Path("graphify-out").is_dir())
    return {
        "name": "Graphify Knowledge Graph",
        "available": bin_path is not None,
        "binary": bin_path or "npx graphify",
        "has_knowledge_base": has_out,
        "status": "healthy" if (bin_path or has_out) else "unavailable",
    }


def _check_plannotator(project_path: Optional[Path]) -> Dict[str, Any]:
    """Vérifie l'état de Plannotator et dénombre les plans archivés."""
    bin_path = _get_plannotator_binary()
    plans_count = 0
    plans_list: List[Dict[str, Any]] = []

    if project_path and (project_path / "memory" / "plan").exists():
        plan_dir = project_path / "memory" / "plan"
        for p in plan_dir.glob("*.md"):
            plans_count += 1
            plans_list.append(
                {
                    "name": p.name,
                    "annotated": ".annotated." in p.name,
                    "modified_at": p.stat().st_mtime,
                }
            )

    return {
        "name": "Plannotator",
        "available": bin_path is not None,
        "binary": bin_path,
        "plans_count": plans_count,
        "recent_plans": sorted(plans_list, key=lambda x: x["modified_at"], reverse=True)[:5],
        "status": "healthy" if bin_path else "missing_binary",
    }


def _check_opencode(project_path: Optional[Path]) -> Dict[str, Any]:
    """Vérifie le runtime OpenCode et sa configuration projet."""
    bin_avail = is_opencode_available()
    bin_path = shutil.which("opencode")
    has_cfg = (
        (project_path / ".opencode" / "opencode.json").exists()
        if project_path
        else False
    )
    return {
        "name": "OpenCode CLI",
        "available": bin_avail,
        "binary": bin_path,
        "configured": has_cfg,
        "status": "healthy" if bin_avail else "missing_binary",
    }


def _check_litellm() -> Dict[str, Any]:
    """Vérifie la joignabilité du proxy LiteLLM local."""
    connected = check_litellm_connectivity(port=4000, timeout=0.8)
    return {
        "name": "LiteLLM Local Proxy (port 4000)",
        "available": connected,
        "endpoint": "http://localhost:4000",
        "status": "healthy" if connected else "offline",
    }


@router.get("/status")
def get_tooling_status(
    project: Optional[str] = Query(None, description="Nom du projet cible")
) -> Dict[str, Any]:
    """Retourne la télémétrie de santé de l'ensemble de l'écosystème d'outillage."""
    canonical = resolve_project_canonical_name(project) if project else None
    proj_path = resolve_project_path(canonical) if canonical else None

    opencode_info = _check_opencode(proj_path)
    plannotator_info = _check_plannotator(proj_path)
    litellm_info = _check_litellm()
    graphify_info = _check_graphify()

    all_tools = [opencode_info, plannotator_info, litellm_info, graphify_info]
    healthy_count = sum(1 for t in all_tools if t["status"] == "healthy")

    return {
        "status": "ok",
        "project": canonical or "global",
        "healthy_count": healthy_count,
        "total_tools": len(all_tools),
        "tools": {
            "opencode": opencode_info,
            "plannotator": plannotator_info,
            "litellm": litellm_info,
            "graphify": graphify_info,
        },
    }
