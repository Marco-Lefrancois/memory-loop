# -*- coding: utf-8 -*-
"""
src/dashboard/routers/metrics.py — Routeur FastAPI pour l'agrégation des métriques de tokens et coûts.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from src.dashboard.project_utils import (
    match_project_alias as _match_project_alias,
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.metrics")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Métriques & Consommation"])


@router.get("/api/metrics")
def get_metrics(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Agrège les métriques de consommation de jetons et de coûts depuis token_ledger.jsonl.
    """
    # Auto-synchronisation des sessions OpenCode Desktop
    try:
        from src.utils.opencode_meter import OpenCodeMeter

        OpenCodeMeter.sync()
    except Exception as e:
        logger.warning(
            "Auto-sync OpenCode Desktop ignorée pour /api/metrics, métriques potentiellement incomplètes",
            exc_info=True,
            extra={"component": "dashboard.routers.metrics", "operation": "get_metrics", "error": str(e)},
        )

    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    ledger_files: List[tuple[Path, bool]] = []  # (chemin, est_fichier_dédié_au_projet)

    # 1. Fichier spécifique projet si existant
    if p_root != REPO_ROOT:
        proj_ledger = p_root / "memory" / "token_ledger.jsonl"
        if proj_ledger.exists():
            ledger_files.append((proj_ledger, True))

    # 2. Fichier global racine
    global_ledger = REPO_ROOT / "memory" / "token_ledger.jsonl"
    if global_ledger.exists():
        ledger_files.append((global_ledger, False))

    entries = []
    seen_fingerprints = set()

    for l_path, is_dedicated in ledger_files:
        try:
            with open(l_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_proj = entry.get("project", "")

                        # Si le fichier provient directement du dossier du projet cible, tout appartient au projet !
                        if not is_dedicated and target_project not in (
                            "Memory Loop",
                            "mLoop",
                            "global",
                            "All",
                            "ALL",
                            "*",
                        ):
                            # Filtre tolérant pour le fichier global
                            if not _match_project_alias(entry_proj, target_project, entry):
                                continue

                        # Déduplication par empreinte timestamp + action + tokens
                        fp = f"{entry.get('timestamp')}_{entry.get('action')}_{entry.get('total_tokens_est')}_{entry.get('model')}"
                        if fp in seen_fingerprints:
                            continue
                        seen_fingerprints.add(fp)
                        entries.append(entry)
                    except Exception as e:
                        logger.debug(
                            "Ligne JSONL illisible dans token_ledger (/api/metrics), ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "dashboard.routers.metrics",
                                "operation": "get_metrics",
                                "ledger_path": str(l_path),
                                "error": str(e),
                            },
                        )
                        continue
        except Exception as e:
            logger.warning(
                "Lecture du token_ledger échouée, métriques incomplètes",
                exc_info=True,
                extra={
                    "component": "dashboard.routers.metrics",
                    "operation": "get_metrics",
                    "ledger_path": str(l_path),
                    "error": str(e),
                },
            )

    # Calculs agrégés
    total_prompt_tokens = sum(e.get("prompt_tokens_est", 0) for e in entries)
    total_completion_tokens = sum(e.get("completion_tokens_est", 0) for e in entries)
    total_tokens = total_prompt_tokens + total_completion_tokens
    total_cost_usd = sum(e.get("cost_usd_est", 0.0) for e in entries)

    # Ventilation par modèle
    models_stats: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        m_name = e.get("model", "unknown")
        if m_name not in models_stats:
            models_stats[m_name] = {
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
            }
        models_stats[m_name]["calls"] += 1
        models_stats[m_name]["prompt_tokens"] += e.get("prompt_tokens_est", 0)
        models_stats[m_name]["completion_tokens"] += e.get("completion_tokens_est", 0)
        models_stats[m_name]["total_tokens"] += e.get("total_tokens_est", 0)
        models_stats[m_name]["cost_usd"] += e.get("cost_usd_est", 0.0)

    for m in models_stats.values():
        m["cost_usd"] = round(m["cost_usd"], 4)

    # Ventilation par action
    actions_stats: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        act = e.get("action", "unknown")
        if act not in actions_stats:
            actions_stats[act] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        actions_stats[act]["calls"] += 1
        actions_stats[act]["tokens"] += e.get("total_tokens_est", 0)
        actions_stats[act]["cost_usd"] += e.get("cost_usd_est", 0.0)

    for a in actions_stats.values():
        a["cost_usd"] = round(a["cost_usd"], 4)

    # Ventilation tri-source (llm_nmedia_cloud vs antigravity-chat vs opencode-desktop)
    sources_stats: Dict[str, Dict[str, Any]] = {
        "llm_nmedia_cloud": {"calls": 0, "tokens": 0, "cost_usd": 0.0},
        "antigravity-chat": {"calls": 0, "tokens": 0, "cost_usd": 0.0},
        "opencode-desktop": {"calls": 0, "tokens": 0, "cost_usd": 0.0},
    }
    for e in entries:
        s_raw = (e.get("source") or "").strip()
        if s_raw in ("opencode-desktop", "opencode"):
            s_name = "opencode-desktop"
        elif s_raw in ("antigravity-chat", "Google", "antigravity") or (
            e.get("key_label") == "Google Workspace / Enterprise"
        ):
            s_name = "antigravity-chat"
        else:
            s_name = "llm_nmedia_cloud"

        if s_name not in sources_stats:
            sources_stats[s_name] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        sources_stats[s_name]["calls"] += 1
        sources_stats[s_name]["tokens"] += e.get("total_tokens_est", 0)
        sources_stats[s_name]["cost_usd"] += e.get("cost_usd_est", 0.0)

    for s in sources_stats.values():
        s["cost_usd"] = round(s["cost_usd"], 4)

    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    recent_interactions = entries[:30]

    return {
        "project": target_project,
        "total_calls": len(entries),
        "total_tokens": total_tokens,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_cost_usd": round(total_cost_usd, 4),
        "models_breakdown": models_stats,
        "top_actions": sorted(actions_stats.items(), key=lambda x: x[1]["tokens"], reverse=True)[
            :8
        ],
        "sources_breakdown": sources_stats,
        "recent_interactions": recent_interactions,
    }
