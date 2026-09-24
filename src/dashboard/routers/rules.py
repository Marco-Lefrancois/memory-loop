# -*- coding: utf-8 -*-
"""
src/dashboard/routers/rules.py — Routeur FastAPI pour les règles RHO sémantiques et d'auto-amélioration.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter

from src.dashboard.project_utils import (
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.rules")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Règles RHO"])


def _parse_yaml_file(path: Path) -> List[Dict[str, Any]]:
    """Parse un fichier YAML de façon sécurisée (ADR-0369)."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("rules", [data])
        return []
    except Exception as e:
        logger.debug(
            "Parsing YAML échoué pour rho_rules",
            exc_info=True,
            extra={
                "component": "dashboard.routers.rules",
                "operation": "_parse_yaml_file",
                "path": str(path),
                "error": str(e),
            },
        )
        return []


@router.get("/api/rho-rules")
def get_rho_rules(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Retourne l'inventaire des règles d'auto-amélioration et d'exclusion sémantiques RHO (ST-104).
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    global_rules_file = REPO_ROOT / "standards" / "rho_rules.yaml"
    if not global_rules_file.exists():
        global_rules_file = REPO_ROOT / "rho_rules.yaml"

    local_candidates = [
        p_root / "memory" / "rho_rules.yaml",
        p_root / "rho_rules.yaml",
        REPO_ROOT / "memory" / "rho_rules.yaml",
    ]

    global_rules = _parse_yaml_file(global_rules_file)
    local_rules = []
    for lc in local_candidates:
        if lc.exists() and lc != global_rules_file:
            local_rules = _parse_yaml_file(lc)
            if local_rules:
                break

    return {
        "project": target_project,
        "global_rules_count": len(global_rules),
        "local_rules_count": len(local_rules),
        "global_rules": global_rules,
        "local_rules": local_rules,
    }
