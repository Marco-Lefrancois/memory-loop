# -*- coding: utf-8 -*-
"""
src/dashboard/routers/system.py — Routeur FastAPI pour la santé, l'état FSM et la sélection de projet.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.dashboard.module_utils import (
    discover_project_modules,
    get_all_projects_modules,
)
from src.dashboard.project_utils import (
    get_friendly_project_label,
    list_available_projects as _list_available_projects,
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.system")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Système & État"])


def get_active_project() -> str:
    """Résout le nom du projet actif."""
    env_proj = os.getenv("MLOOP_ACTIVE_PROJECT")
    if env_proj:
        return _resolve_project_canonical_name(env_proj)

    active_json = REPO_ROOT / "memory" / "active_project.json"
    if active_json.exists():
        try:
            with open(active_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("active_project"):
                val = data["active_project"]
                if str(val).lower() == "default":
                    return "Memory Loop"
                return _resolve_project_canonical_name(val)
        except Exception as e:
            logger.debug(
                "Lecture de memory/active_project.json échouée, fallback sur projet par défaut",
                exc_info=True,
                extra={
                    "component": "dashboard.routers.system",
                    "operation": "get_active_project",
                    "path": str(active_json),
                    "error": str(e),
                },
            )

    return "Memory Loop"


def set_active_project(project_name: str) -> str:
    """Met à jour et persiste le projet actif dans memory/active_project.json et os.environ."""
    canon = _resolve_project_canonical_name(project_name)
    os.environ["MLOOP_ACTIVE_PROJECT"] = canon
    active_json = REPO_ROOT / "memory" / "active_project.json"
    try:
        active_json.parent.mkdir(parents=True, exist_ok=True)
        with open(active_json, "w", encoding="utf-8") as f:
            json.dump({"active_project": canon}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(
            "Persistance du projet actif échouée (memory/active_project.json)",
            exc_info=True,
            extra={
                "component": "dashboard.routers.system",
                "operation": "set_active_project",
                "path": str(active_json),
                "error": str(e),
            },
        )
    return canon


# Alias pour rétrocompatibilité interne
_get_active_project = get_active_project
_set_active_project = set_active_project


@router.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Vérification de l'état de santé du serveur d'observabilité."""
    active_p = get_active_project()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": "Memory Loop (mLoop)",
        "version": "1.0.0",
        "mode": "sovereign-local",
        "docker_free": True,
        "active_project": active_p,
    }


@router.get("/api/projects")
def get_projects() -> Dict[str, Any]:
    """Liste tous les projets connus et identifie le projet actif."""
    projs = _list_available_projects()
    formatted = [{"id": p, "name": get_friendly_project_label(p)} for p in projs]
    modules_map = get_all_projects_modules()
    return {
        "active_project": get_active_project(),
        "projects": projs,
        "projects_formatted": formatted,
        "modules_by_project": modules_map,
    }


@router.get("/api/modules")
def get_modules(project: Optional[str] = None) -> Dict[str, Any]:
    """Liste tous les modules/initiatives/epics du projet spécifié ou actif."""
    target_project = _resolve_project_canonical_name(project or get_active_project())
    modules = discover_project_modules(target_project)
    return {
        "project": target_project,
        "modules": modules,
        "total_modules": len(modules),
    }


@router.post("/api/project/select")
def select_project(
    payload: Optional[Dict[str, Any]] = None, project: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Persiste le projet actif sélectionné par l'utilisateur."""
    target = project or (payload.get("project") if payload else None)
    if not target:
        raise HTTPException(status_code=400, detail="Paramètre 'project' manquant.")
    canon = set_active_project(target)
    return {
        "status": "ok",
        "active_project": canon,
        "message": f"Projet actif persisté : {canon}",
    }


@router.get("/api/state")
def get_cycle_state(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Retourne l'état d'avancement des 6 phases du cycle de vie logiciel mLoop pour le projet ciblé.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    # 1. SOW : Présence de documents ingérés ou cadrage
    has_ingested = (p_root / "docs" / "00-ingested").exists() and any(
        (p_root / "docs" / "00-ingested").iterdir()
    )
    has_sow = has_ingested or (p_root / "docs" / "00-sow.md").exists()

    # 2. SPEC : Stories dans le backlog
    backlog_dir = p_root / "backlog"
    stories_list = list(backlog_dir.rglob("*.md")) if backlog_dir.exists() else []
    stories_count = len(
        [s for s in stories_list if s.name.lower() not in ("sprint_backlog.md", "readme.md")]
    )

    # 3. PLAN : Récits prêts au dev ou architecture définie
    has_arch = (p_root / "docs" / "01-architecture").exists()
    has_ready_stories = (p_root / "backlog" / "sprint_backlog.md").exists() or (stories_count > 0)

    # 5. VALIDATE : Présence de preuves d'EvidencePacks
    evidence_dir = p_root / "memory" / "evidence"
    has_validate = evidence_dir.exists() and any(evidence_dir.rglob("*.json"))

    phases = [
        {
            "key": "sow",
            "name": "1. SOW & Cadrage",
            "status": "COMPLETED" if has_sow else "PENDING",
            "details": f"{len(list((p_root / 'docs' / '00-ingested').glob('*.md')))} document(s) SSOT ingéré(s)"
            if has_ingested
            else "",
        },
        {
            "key": "spec",
            "name": "2. Spécification (Gherkin)",
            "status": "COMPLETED" if stories_count > 0 else "IN_PROGRESS",
            "details": f"{stories_count} User Story(ies) formalisée(s)",
        },
        {
            "key": "plan",
            "name": "3. Architecture & Contrats",
            "status": "COMPLETED"
            if (has_arch and has_ready_stories)
            else ("IN_PROGRESS" if has_ready_stories else "NOT_STARTED"),
            "details": "Récits cadrés et validés en Sprint Backlog" if has_ready_stories else "",
        },
        {
            "key": "build",
            "name": "4. Implémentation Isolée",
            "status": "NOT_STARTED",
            "details": "Handoff dev en cours",
        },
        {
            "key": "validate",
            "name": "5. Validation & EvidencePack",
            "status": "COMPLETED" if has_validate else "PENDING",
            "details": f"{len(list(evidence_dir.rglob('*.json')))} EvidencePack(s) certifié(s)"
            if has_validate
            else "",
        },
        {
            "key": "ship",
            "name": "6. Universal Dev Handoff",
            "status": "COMPLETED" if (has_validate and stories_count > 0) else "PENDING",
            "details": "Ready for Dev",
        },
    ]

    return {
        "project": target_project,
        "phases": phases,
        "pipeline": "SOW -> SPEC -> PLAN -> BUILD -> VALIDATE -> SHIP",
    }
