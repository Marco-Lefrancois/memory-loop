# -*- coding: utf-8 -*-
"""
src/dashboard/routers/ledger.py — Routeur FastAPI pour la consultation paginée du Token Ledger.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from src.dashboard.module_utils import (
    discover_project_modules,
    get_module_friendly_info,
    match_module_entry,
    normalize_module_id,
)
from src.dashboard.project_utils import (
    match_project_alias as _match_project_alias,
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.dashboard.routers._ledger_helpers import (
    collect_raw_ledger_entries,
    compute_global_summaries,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.ledger")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Token Ledger"])


@router.get("/api/ledger")
def get_ledger(
    project: Optional[str] = None,
    module: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    model: Optional[str] = None,
    action: Optional[str] = None,
    source: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne le journal détaillé de consommation de jetons (Token Ledger) avec pagination,
    recherche multi-critères, plage de dates, distinction multi-sources et synthèse globale.
    """
    try:
        from src.utils.antigravity_meter import AntigravityMeter

        AntigravityMeter.sync()
    except Exception as e:
        logger.warning(
            "Auto-sync Antigravity ignorée pour /api/ledger, journal potentiellement incomplet",
            exc_info=True,
            extra={"component": "dashboard.routers.ledger", "operation": "get_ledger", "error": str(e)},
        )
    try:
        from src.utils.opencode_meter import OpenCodeMeter

        OpenCodeMeter.sync()
    except Exception as e:
        logger.warning(
            "Auto-sync OpenCode Desktop ignorée pour /api/ledger, journal potentiellement incomplet",
            exc_info=True,
            extra={"component": "dashboard.routers.ledger", "operation": "get_ledger", "error": str(e)},
        )

    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    raw_entries = collect_raw_ledger_entries(target_project, p_root, REPO_ROOT)
    (
        all_models,
        all_actions,
        all_projects,
        all_sources,
        global_total_tokens,
        global_total_cost,
        by_project_summary,
        by_source_summary,
    ) = compute_global_summaries(raw_entries)

    filtered = []
    project_entries_for_module_breakdown = []

    for e in raw_entries:
        entry_proj = e.get("project") or "Memory Loop"

        if target_project not in ("ALL", "Memory Loop", "global", "All", "*"):
            if not _match_project_alias(entry_proj, target_project, e):
                continue

        project_entries_for_module_breakdown.append(e)

        if module and module.strip() and module.strip().upper() not in ("ALL", "*", "TOUS"):
            target_mod = module.strip()
            e_mod = e.get("module", "")
            if e_mod and (
                e_mod.lower() == target_mod.lower()
                or normalize_module_id(e_mod) == normalize_module_id(target_mod)
            ):
                pass
            elif not match_module_entry(
                e.get("target", ""),
                target_mod,
                (e.get("context_contributors", []) or []) + ([e_mod] if e_mod else []),
            ):
                continue

        if source and source.strip() and source.strip() not in ("ALL", "Tous", "*"):
            req_source = source.strip().lower()
            entry_source = (e.get("source") or "").lower()
            if req_source in ("antigravity-chat", "google", "antigravity"):
                if entry_source != "antigravity-chat":
                    continue
            elif req_source in ("opencode-desktop", "opencode"):
                if entry_source != "opencode-desktop":
                    continue
            elif req_source in ("llm_nmedia_cloud", "nmedia_cloud", "nmedia"):
                if entry_source != "llm_nmedia_cloud":
                    continue
            elif entry_source != req_source:
                continue

        if model and model.strip():
            if model.lower() not in (e.get("model") or "").lower():
                continue

        if action and action.strip():
            if action.lower() != (e.get("action") or "").lower():
                continue

        ts = e.get("timestamp", "")
        if start_date and start_date.strip():
            if ts < start_date.strip():
                continue

        if end_date and end_date.strip():
            e_clean = end_date.strip()
            if len(e_clean) == 10:
                e_clean = f"{e_clean}T23:59:59.999999"
            if ts > e_clean:
                continue

        if search and search.strip():
            s_term = search.strip().lower()
            haystack = (
                f"{e.get('target', '')} {e.get('action', '')} {e.get('model', '')} "
                f"{entry_proj} {e.get('key_label', '')} {e.get('source', '')} "
                f"{e.get('module', '')} {e.get('module_label', '')}"
            ).lower()
            if s_term not in haystack:
                continue

        filtered.append(e)

    filtered_tokens = sum(e.get("total_tokens_est", 0) for e in filtered)
    filtered_cost_usd = sum(e.get("cost_usd_est", 0.0) for e in filtered)
    filtered_prompt_tokens = sum(e.get("prompt_tokens_est", 0) for e in filtered)
    filtered_completion_tokens = sum(e.get("completion_tokens_est", 0) for e in filtered)

    models_summary: Dict[str, Dict[str, Any]] = {}
    for e in filtered:
        m_name = e.get("model") or "unknown"
        if m_name not in models_summary:
            models_summary[m_name] = {
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "tokens": 0,
                "cost_usd": 0.0,
            }
        models_summary[m_name]["calls"] += 1
        models_summary[m_name]["prompt_tokens"] += e.get("prompt_tokens_est", 0)
        models_summary[m_name]["completion_tokens"] += e.get("completion_tokens_est", 0)
        models_summary[m_name]["tokens"] += e.get("total_tokens_est", 0)
        models_summary[m_name]["cost_usd"] += e.get("cost_usd_est", 0.0)

    for ms in models_summary.values():
        ms["cost_usd"] = round(ms["cost_usd"], 4)

    by_module_summary: Dict[str, Dict[str, Any]] = {}
    for e in project_entries_for_module_breakdown:
        m_id = e.get("module") or "general"
        if m_id not in by_module_summary:
            m_info = get_module_friendly_info(m_id, target_project)
            by_module_summary[m_id] = {
                "id": m_id,
                "label": m_info.get("label", m_id),
                "description": m_info.get("description", ""),
                "category": m_info.get("category", "module"),
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "tokens": 0,
                "cost_usd": 0.0,
                "by_source": {},
            }
        by_module_summary[m_id]["calls"] += 1
        by_module_summary[m_id]["prompt_tokens"] += e.get("prompt_tokens_est", 0)
        by_module_summary[m_id]["completion_tokens"] += e.get("completion_tokens_est", 0)
        by_module_summary[m_id]["tokens"] += e.get("total_tokens_est", 0)
        by_module_summary[m_id]["cost_usd"] += e.get("cost_usd_est", 0.0)
        s_name = e.get("source", "unknown")
        by_module_summary[m_id]["by_source"][s_name] = by_module_summary[m_id]["by_source"].get(
            s_name, 0
        ) + e.get("total_tokens_est", 0)

    if target_project not in ("ALL", "Memory Loop", "global", "All", "*"):
        try:
            discovered = discover_project_modules(target_project)
            for dm in discovered:
                dm_id = dm["id"]
                if dm_id not in by_module_summary:
                    m_info = get_module_friendly_info(dm_id, target_project)
                    by_module_summary[dm_id] = {
                        "id": dm_id,
                        "label": dm.get("label") or m_info.get("label", dm_id),
                        "description": dm.get("description") or m_info.get("description", ""),
                        "category": dm.get("category") or m_info.get("category", "module"),
                        "calls": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "tokens": 0,
                        "cost_usd": 0.0,
                        "by_source": {},
                    }
        except Exception as e:
            logger.debug(
                "Découverte des modules du projet échouée, synthèse par module laissée vide",
                exc_info=True,
                extra={"component": "dashboard.routers.ledger", "operation": "get_ledger", "project": target_project, "error": str(e)},
            )

    for bm in by_module_summary.values():
        bm["cost_usd"] = round(bm["cost_usd"], 4)

    p_num = int(getattr(page, "default", page) or 1)
    p_size = int(getattr(page_size, "default", page_size) or 50)
    total_entries = len(filtered)
    total_pages = max(1, math.ceil(total_entries / p_size))
    current_page = max(1, min(p_num, total_pages))
    start_idx = (current_page - 1) * p_size
    end_idx = start_idx + p_size
    page_entries = filtered[start_idx:end_idx]

    return {
        "project": target_project,
        "filtered_module": module,
        "page": current_page,
        "page_size": p_size,
        "total_entries": total_entries,
        "total_pages": total_pages,
        "filtered_tokens": filtered_tokens,
        "filtered_prompt_tokens": filtered_prompt_tokens,
        "filtered_completion_tokens": filtered_completion_tokens,
        "filtered_cost_usd": round(filtered_cost_usd, 4),
        "by_model": models_summary,
        "by_module": sorted(
            list(by_module_summary.values()), key=lambda x: x["tokens"], reverse=True
        ),
        "summary": {
            "total_calls": total_entries,
            "total_tokens": filtered_tokens,
            "prompt_tokens": filtered_prompt_tokens,
            "completion_tokens": filtered_completion_tokens,
            "total_cost_usd": round(filtered_cost_usd, 4),
        },
        "global_summary": {
            "total_calls": len(raw_entries),
            "total_tokens": global_total_tokens,
            "total_cost_usd": round(global_total_cost, 4),
            "by_project": dict(
                sorted(by_project_summary.items(), key=lambda x: x[1]["tokens"], reverse=True)
            ),
            "by_source": by_source_summary,
        },
        "available_models": sorted(list(all_models)),
        "available_actions": sorted(list(all_actions)),
        "available_projects": sorted(list(all_projects)),
        "available_sources": sorted(list(all_sources)),
        "entries": page_entries,
    }
