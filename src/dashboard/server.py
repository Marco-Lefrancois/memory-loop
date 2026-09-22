# -*- coding: utf-8 -*-
"""
Serveur FastAPI pour le Dashboard d'Observabilité et Supervision Souverain mLoop.
Expose des endpoints REST pour les métriques de tokens, le flux d'événements,
la visualisation du backlog et l'intégrité de la mémoire (Zéro-Docker).
Supporte la résolution canonique des projets (ex: Boire & Frères) et la récursion des stories/preuves.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.dashboard.project_utils import (
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
    match_project_alias as _match_project_alias,
    list_available_projects as _list_available_projects,
    get_friendly_project_label,
)
from src.dashboard.module_utils import (
    discover_project_modules,
    get_all_projects_modules,
    get_module_friendly_info,
    get_story_module,
    match_module_entry,
    normalize_module_id,
)
from src.dashboard.routers.database import router as database_router
from src.dashboard.routers.dream_rsi import router as dream_rsi_router
from src.dashboard.routers.governance import router as governance_router
from src.dashboard.routers.overview import router as overview_router
from src.dashboard.routers.resilience import router as resilience_router
from src.dashboard.routers.swarm import router as swarm_router
from src.dashboard.routers.traces import router as traces_router
from src.utils.logger import get_logger

logger = get_logger("dashboard.server")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="mLoop Sovereign Observability Hub",
    description="Tableau de bord de supervision et métriques en temps réel pour Memory Loop",
    version="1.0.0",
)

# Configuration CORS pour requêtes locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Montage des Routeurs Modulaires Agentiques (Dashboard 2.0) ─────────────────
app.include_router(overview_router)
app.include_router(swarm_router)
app.include_router(traces_router)
app.include_router(resilience_router)
app.include_router(dream_rsi_router)
app.include_router(governance_router)
app.include_router(database_router)


def _get_active_project() -> str:
    """Résout le nom du projet actif."""
    env_proj = os.getenv("MLOOP_ACTIVE_PROJECT")
    if env_proj:
        return _resolve_project_canonical_name(env_proj)

    active_json = REPO_ROOT / "memory" / "active_project.json"
    if active_json.exists():
        try:
            data = json.loads(active_json.read_text(encoding="utf-8"))
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
                    "component": "dashboard.server",
                    "operation": "_get_active_project",
                    "path": str(active_json),
                    "error": str(e),
                },
            )

    return "Memory Loop"


def _set_active_project(project_name: str) -> str:
    """Met à jour et persiste le projet actif dans memory/active_project.json et os.environ."""
    canon = _resolve_project_canonical_name(project_name)
    os.environ["MLOOP_ACTIVE_PROJECT"] = canon
    active_json = REPO_ROOT / "memory" / "active_project.json"
    try:
        active_json.parent.mkdir(parents=True, exist_ok=True)
        active_json.write_text(
            json.dumps({"active_project": canon}, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        logger.warning(
            "Persistance du projet actif échouée (memory/active_project.json)",
            exc_info=True,
            extra={
                "component": "dashboard.server",
                "operation": "_set_active_project",
                "path": str(active_json),
                "error": str(e),
            },
        )
    return canon


# ── ENDPOINTS REST ─────────────────────────────────────────────────────────────


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Vérification de l'état de santé du serveur d'observabilité."""
    active_p = _get_active_project()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": "Memory Loop (mLoop)",
        "version": "1.0.0",
        "mode": "sovereign-local",
        "docker_free": True,
        "active_project": active_p,
    }


@app.get("/api/projects")
def get_projects() -> Dict[str, Any]:
    """Liste tous les projets connus et identifie le projet actif."""
    projs = _list_available_projects()
    formatted = [{"id": p, "name": get_friendly_project_label(p)} for p in projs]
    modules_map = get_all_projects_modules()
    return {
        "active_project": _get_active_project(),
        "projects": projs,
        "projects_formatted": formatted,
        "modules_by_project": modules_map,
    }


@app.get("/api/modules")
def get_modules(project: Optional[str] = None) -> Dict[str, Any]:
    """Liste tous les modules/initiatives/epics du projet spécifié ou actif."""
    target_project = _resolve_project_canonical_name(project or _get_active_project())
    modules = discover_project_modules(target_project)
    return {
        "project": target_project,
        "modules": modules,
        "total_modules": len(modules),
    }


@app.post("/api/project/select")
def select_project(
    payload: Optional[Dict[str, Any]] = None, project: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Persiste le projet actif sélectionné par l'utilisateur."""
    target = project or (payload.get("project") if payload else None)
    if not target:
        raise HTTPException(status_code=400, detail="Paramètre 'project' manquant.")
    canon = _set_active_project(target)
    return {
        "status": "ok",
        "active_project": canon,
        "message": f"Projet actif persisté : {canon}",
    }


@app.get("/api/metrics")
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
            extra={"component": "dashboard.server", "operation": "get_metrics", "error": str(e)},
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
                                "component": "dashboard.server",
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
                    "component": "dashboard.server",
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


@app.get("/api/ledger")
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
    recherche multi-critères, plage de dates, distinction bi-source (nmedia_cloud vs Google)
    et synthèse globale.
    """
    # Auto-synchronisation légère des sessions Antigravity et OpenCode Desktop
    try:
        from src.utils.antigravity_meter import AntigravityMeter

        AntigravityMeter.sync()
    except Exception as e:
        logger.warning(
            "Auto-sync Antigravity ignorée pour /api/ledger, journal potentiellement incomplet",
            exc_info=True,
            extra={"component": "dashboard.server", "operation": "get_ledger", "error": str(e)},
        )
    try:
        from src.utils.opencode_meter import OpenCodeMeter

        OpenCodeMeter.sync()
    except Exception as e:
        logger.warning(
            "Auto-sync OpenCode Desktop ignorée pour /api/ledger, journal potentiellement incomplet",
            exc_info=True,
            extra={"component": "dashboard.server", "operation": "get_ledger", "error": str(e)},
        )

    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    ledger_files: List[tuple[Path, bool]] = []

    # 1. Fichier spécifique projet si existant
    if p_root != REPO_ROOT and target_project != "ALL":
        proj_ledger = p_root / "memory" / "token_ledger.jsonl"
        if proj_ledger.exists():
            ledger_files.append((proj_ledger, True))

    # 2. Fichier global racine
    global_ledger = REPO_ROOT / "memory" / "token_ledger.jsonl"
    if global_ledger.exists():
        ledger_files.append((global_ledger, False))

    # Si ALL ou racine, scanner aussi les dossiers de projets pour exhaustivité
    if target_project in ("ALL", "Memory Loop"):
        projects_dir = REPO_ROOT / "Projects"
        if projects_dir.exists():
            for p in projects_dir.iterdir():
                if (
                    p.is_dir()
                    and not p.name.startswith(".")
                    and not p.name.startswith("_")
                    and p.name.lower() not in {"default", "cacheproj", "timeoutproj"}
                ):
                    pl = p / "memory" / "token_ledger.jsonl"
                    if (
                        pl.exists()
                        and (pl, False) not in ledger_files
                        and (pl, True) not in ledger_files
                    ):
                        ledger_files.append((pl, False))

    raw_entries = []
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
                        entry_proj = entry.get("project", "") or "Memory Loop"

                        fp = f"{entry.get('timestamp')}_{entry.get('action')}_{entry.get('total_tokens_est')}_{entry.get('model')}_{entry.get('target')}"
                        if fp in seen_fingerprints:
                            continue
                        seen_fingerprints.add(fp)

                        # Normalisation de la source (nmedia_cloud vs Google vs opencode-desktop)
                        src_val = entry.get("source")
                        if not src_val:
                            if (
                                "gemini" in (entry.get("model") or "").lower()
                                and entry.get("key_label") == "Google Workspace / Enterprise"
                            ):
                                src_val = "Google"
                            elif (entry.get("action") or "").startswith("antigravity-"):
                                src_val = "Google"
                            elif "opencode" in (entry.get("action") or "") or "opencode" in (
                                entry.get("target") or ""
                            ):
                                src_val = "opencode-desktop"
                            else:
                                src_val = "nmedia_cloud"
                        entry["source"] = src_val

                        # Attribution et normalisation du module
                        mod = entry.get("module")
                        if not mod:
                            for cand in (
                                "01-reception",
                                "02-incubation",
                                "03-ventes",
                                "PAPERCUTS",
                                "OneTrust_FOOD",
                                "OneTrust_COMMERCE",
                                "Metro_Food_Offers",
                                "RBC_Avion",
                                "OneTrust_SANTE",
                                "AccesDossier",
                            ):
                                if match_module_entry(
                                    entry.get("target", ""),
                                    cand,
                                    entry.get("context_contributors", []),
                                ):
                                    mod = cand
                                    break
                        mod = mod or "general"
                        entry["module"] = mod
                        entry["module_label"] = get_module_friendly_info(mod, entry_proj).get(
                            "label", mod
                        )

                        entry["project_display"] = entry_proj
                        raw_entries.append(entry)
                    except Exception as e:
                        logger.debug(
                            "Ligne JSONL illisible dans token_ledger (/api/ledger), ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "dashboard.server",
                                "operation": "get_ledger",
                                "ledger_path": str(l_path),
                                "error": str(e),
                            },
                        )
                        continue
        except Exception as e:
            logger.warning(
                "Lecture du token_ledger échouée, journal détaillé incomplet",
                exc_info=True,
                extra={
                    "component": "dashboard.server",
                    "operation": "get_ledger",
                    "ledger_path": str(l_path),
                    "error": str(e),
                },
            )

    # Trier par timestamp décroissant (plus récents en tête)
    raw_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    # Collecter les filtres disponibles et la synthèse globale (tous projets)
    all_models = set()
    all_actions = set()
    all_projects = set()
    all_sources = {"llm_nmedia_cloud", "antigravity-chat", "opencode-desktop"}
    global_total_tokens = 0
    global_total_cost = 0.0
    by_project_summary: Dict[str, Dict[str, Any]] = {}
    by_source_summary: Dict[str, Dict[str, Any]] = {
        "llm_nmedia_cloud": {"calls": 0, "tokens": 0, "cost_usd": 0.0},
        "antigravity-chat": {"calls": 0, "tokens": 0, "cost_usd": 0.0},
        "opencode-desktop": {"calls": 0, "tokens": 0, "cost_usd": 0.0},
    }

    for e in raw_entries:
        p_name = e.get("project") or "Memory Loop"
        is_tmp = p_name.startswith("tmp") or p_name.lower() in (
            "default",
            "cacheproj",
            "timeoutproj",
        )
        summary_key = "🧪 Tests & Éphémères" if is_tmp else p_name

        if not is_tmp:
            all_projects.add(p_name)
        else:
            all_projects.add("🧪 Tests & Éphémères")

        m_name = e.get("model") or "unknown"
        all_models.add(m_name)
        act_name = e.get("action") or "chat_turn"
        all_actions.add(act_name)

        s_raw = (e.get("source") or "").strip()
        if s_raw in ("opencode-desktop", "opencode"):
            s_name = "opencode-desktop"
        elif s_raw in ("antigravity-chat", "Google", "antigravity") or (
            e.get("key_label") == "Google Workspace / Enterprise"
        ):
            s_name = "antigravity-chat"
        else:
            s_name = "llm_nmedia_cloud"
        e["source"] = s_name
        all_sources.add(s_name)

        toks = e.get("total_tokens_est", 0)
        cost = e.get("cost_usd_est", 0.0)
        global_total_tokens += toks
        global_total_cost += cost

        # Synthèse par projet
        if summary_key not in by_project_summary:
            by_project_summary[summary_key] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        by_project_summary[summary_key]["calls"] += 1
        by_project_summary[summary_key]["tokens"] += toks
        by_project_summary[summary_key]["cost_usd"] += cost

        # Synthèse par source
        if s_name not in by_source_summary:
            by_source_summary[s_name] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        by_source_summary[s_name]["calls"] += 1
        by_source_summary[s_name]["tokens"] += toks
        by_source_summary[s_name]["cost_usd"] += cost

    for bp in by_project_summary.values():
        bp["cost_usd"] = round(bp["cost_usd"], 4)
    for bs in by_source_summary.values():
        bs["cost_usd"] = round(bs["cost_usd"], 4)

    # Filtrage des entrées selon les critères de la requête
    filtered = []
    project_entries_for_module_breakdown = []

    for e in raw_entries:
        entry_proj = e.get("project") or "Memory Loop"

        # Filtre projet si un projet spécifique est sélectionné et non ALL
        if target_project not in ("ALL", "Memory Loop", "global", "All", "*"):
            if not _match_project_alias(entry_proj, target_project, e):
                continue

        project_entries_for_module_breakdown.append(e)

        # Filtre Module / Epic
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

        # Filtre Source LLM (Tous | antigravity-chat | opencode-desktop | llm_nmedia_cloud)
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

        # Filtre modèle
        if model and model.strip():
            if model.lower() not in (e.get("model") or "").lower():
                continue

        # Filtre action
        if action and action.strip():
            if action.lower() != (e.get("action") or "").lower():
                continue

        # Filtre date de début
        ts = e.get("timestamp", "")
        if start_date and start_date.strip():
            if ts < start_date.strip():
                continue

        # Filtre date de fin
        if end_date and end_date.strip():
            e_clean = end_date.strip()
            if len(e_clean) == 10:
                e_clean = f"{e_clean}T23:59:59.999999"
            if ts > e_clean:
                continue

        # Recherche textuelle libre (incluant la source et le module)
        if search and search.strip():
            s_term = search.strip().lower()
            haystack = f"{e.get('target', '')} {e.get('action', '')} {e.get('model', '')} {entry_proj} {e.get('key_label', '')} {e.get('source', '')} {e.get('module', '')} {e.get('module_label', '')}".lower()
            if s_term not in haystack:
                continue

        filtered.append(e)

    # Métriques filtrées
    filtered_tokens = sum(e.get("total_tokens_est", 0) for e in filtered)
    filtered_cost_usd = sum(e.get("cost_usd_est", 0.0) for e in filtered)
    filtered_prompt_tokens = sum(e.get("prompt_tokens_est", 0) for e in filtered)
    filtered_completion_tokens = sum(e.get("completion_tokens_est", 0) for e in filtered)

    # Ventilation par modèle des entrées filtrées
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

    # Synthèse par module pour le projet sélectionné
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

    # Compléter avec les modules découverts s'ils n'ont pas encore de logs
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
                extra={
                    "component": "dashboard.server",
                    "operation": "get_ledger",
                    "project": target_project,
                    "error": str(e),
                },
            )

    for bm in by_module_summary.values():
        bm["cost_usd"] = round(bm["cost_usd"], 4)

    # Pagination
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


@app.get("/api/events")
def get_events(
    project: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
    module: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne le journal live des événements récents depuis events.jsonl.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    events_files: List[tuple[Path, bool]] = []

    if p_root != REPO_ROOT:
        p_events = p_root / "memory" / "events.jsonl"
        if p_events.exists():
            events_files.append((p_events, True))

    global_events = REPO_ROOT / "memory" / "events.jsonl"
    if global_events.exists():
        events_files.append((global_events, False))

    raw_events = []
    seen = set()

    for ef, is_dedicated in events_files:
        try:
            with open(ef, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        if not is_dedicated and target_project not in (
                            "Memory Loop",
                            "mLoop",
                            "global",
                            "All",
                            "ALL",
                            "*",
                        ):
                            if not _match_project_alias(ev.get("project", ""), target_project):
                                continue

                        if event_type and event_type != "ALL":
                            if ev.get("event_type", "").upper() != event_type.upper():
                                continue

                        if module and module.upper() not in ("ALL", "*", "TOUS"):
                            details_str = str(ev.get("details", ""))
                            target_str = str(ev.get("target", ""))
                            if not match_module_entry(
                                target_str, module, [details_str, str(ev.get("file_attention", ""))]
                            ):
                                continue

                        fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
                        if fp in seen:
                            continue
                        seen.add(fp)
                        raw_events.append(ev)
                    except Exception as e:
                        logger.debug(
                            "Événement JSONL illisible dans events.jsonl, ligne ignorée",
                            exc_info=True,
                            extra={
                                "component": "dashboard.server",
                                "operation": "get_events",
                                "events_path": str(ef),
                                "error": str(e),
                            },
                        )
                        continue
        except Exception as e:
            logger.warning(
                "Lecture de events.jsonl échouée, journal d'événements incomplet",
                exc_info=True,
                extra={
                    "component": "dashboard.server",
                    "operation": "get_events",
                    "events_path": str(ef),
                    "error": str(e),
                },
            )

    raw_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    selected = raw_events[:limit]

    return {
        "project": target_project,
        "count": len(selected),
        "total_captured": len(raw_events),
        "events": selected,
    }


@app.get("/api/stream/events")
async def stream_events(
    project: Optional[str] = None,
    event_type: Optional[str] = None,
    module: Optional[str] = None,
):
    """
    Stream SSE (Server-Sent Events) pour l'Event Bus mLoop en temps réel (ST-112).
    Diffuse les événements au fur et à mesure de leur écriture dans memory/events.jsonl.
    """
    target_project = _resolve_project_canonical_name(project)

    async def event_generator():
        # 1. Événement initial : 40 derniers événements
        initial_res = get_events(
            project=target_project, limit=40, event_type=event_type, module=module
        )
        initial_list = list(reversed(initial_res.get("events", [])))
        yield f"event: initial\ndata: {json.dumps(initial_list, ensure_ascii=False)}\n\n"

        events_file = REPO_ROOT / "memory" / "events.jsonl"
        last_pos = events_file.stat().st_size if events_file.exists() else 0
        seen_fp = set()
        for ev in initial_list:
            fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
            seen_fp.add(fp)

        heartbeat_counter = 0
        try:
            while True:
                await asyncio.sleep(0.5)
                heartbeat_counter += 1

                if heartbeat_counter >= 30:  # ~15s ping
                    yield ": keepalive\n\n"
                    heartbeat_counter = 0

                if not events_file.exists():
                    continue

                curr_size = events_file.stat().st_size
                if curr_size < last_pos:
                    last_pos = 0

                if curr_size > last_pos:
                    try:
                        with open(events_file, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(last_pos)
                            new_lines = f.readlines()
                            last_pos = f.tell()

                        for line in new_lines:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                ev = json.loads(line)
                                entry_proj = ev.get("project", "")
                                if target_project not in (
                                    "Memory Loop",
                                    "mLoop",
                                    "global",
                                    "All",
                                    "ALL",
                                    "*",
                                ):
                                    if not _match_project_alias(entry_proj, target_project):
                                        continue

                                if event_type and event_type != "ALL":
                                    if ev.get("event_type", "").upper() != event_type.upper():
                                        continue

                                if module and module.upper() not in ("ALL", "*", "TOUS"):
                                    details_str = str(ev.get("details", ""))
                                    target_str = str(ev.get("target", ""))
                                    if not match_module_entry(
                                        target_str,
                                        module,
                                        [details_str, str(ev.get("file_attention", ""))],
                                    ):
                                        continue

                                fp = f"{ev.get('timestamp')}_{ev.get('event_type')}_{ev.get('agent')}_{str(ev.get('details'))[:40]}"
                                if fp in seen_fp:
                                    continue
                                seen_fp.add(fp)

                                yield f"event: message\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
                            except Exception as e:
                                logger.debug(
                                    "Événement SSE JSONL illisible, ligne ignorée",
                                    exc_info=True,
                                    extra={
                                        "component": "dashboard.server",
                                        "operation": "stream_events",
                                        "events_path": str(events_file),
                                        "error": str(e),
                                    },
                                )
                                continue
                    except Exception as e:
                        logger.warning(
                            "Lecture incrémentale de events.jsonl échouée, flux SSE suspendu pour ce cycle",
                            exc_info=True,
                            extra={
                                "component": "dashboard.server",
                                "operation": "stream_events",
                                "events_path": str(events_file),
                                "error": str(e),
                            },
                        )
        except asyncio.CancelledError:
            logger.debug(
                "Flux SSE d'événements annulé par le client",
                extra={"component": "dashboard.server", "operation": "stream_events"},
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/backlog/{project_name}")
def get_project_backlog(project_name: str, module: Optional[str] = None) -> Dict[str, Any]:
    """Retourne la liste des User Stories d'un projet pour le Backlog Drawer (ST-114)."""
    return get_stories(project=project_name, module=module)


@app.get("/api/backlog/{project_name}/{story_id}")
def get_project_story_detail(project_name: str, story_id: str) -> Dict[str, Any]:
    """
    Retourne le détail complet d'une User Story pour inspection approfondie dans le Backlog Drawer.
    """
    target_project = _resolve_project_canonical_name(project_name)
    p_root = _get_project_root(target_project)

    backlog_roots = [p_root / "backlog"]
    if target_project in ("Memory Loop", "mLoop", "ALL"):
        dash_b = REPO_ROOT / "Projects" / "mLoop-Dashboard" / "backlog"
        if dash_b.exists():
            backlog_roots.append(dash_b)

    found_file: Optional[Path] = None
    for b_root in backlog_roots:
        if not b_root.exists():
            continue
        for md_file in b_root.rglob("*.md"):
            if md_file.stem.lower() == story_id.lower() or story_id.lower() in md_file.stem.lower():
                found_file = md_file
                break
        if found_file:
            break

    if not found_file or not found_file.exists():
        raise HTTPException(
            status_code=404, detail=f"Story '{story_id}' introuvable dans '{project_name}'."
        )

    content = found_file.read_text(encoding="utf-8", errors="ignore")

    meta: Dict[str, Any] = {
        "id": story_id,
        "title": found_file.stem,
        "status": "OPEN",
        "type": "feature",
        "layer": "vertical-slice",
        "jira_key": "",
        "epic_key": "",
    }
    body = content
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = content[fm_match.end() :].strip()
        for line in fm_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip("'\"")

    if meta.get("title") == found_file.stem:
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            meta["title"] = h1_match.group(1).strip()

    scenarios = []
    gherkin_blocks = re.findall(r"```gherkin(.*?)```", content, re.DOTALL | re.IGNORECASE)
    for block in gherkin_blocks:
        scen_matches = re.split(r"(?im)^\s*(?:Scénario|Scenario)\s*:\s*", block)
        for s in scen_matches[1:]:
            lines = s.strip().splitlines()
            s_name = lines[0].strip() if lines else "Scénario"
            steps = [l.strip() for l in lines[1:] if l.strip() and not l.strip().startswith("#")]
            scenarios.append({"name": s_name, "steps": steps})

    # Business rules extraction (R-xxx or RM-xxx)
    rules = re.findall(r"(?im)^\s*[\*\-]\s*`?([A-Za-z0-9_\-]+)`?\s*:\s*(.+)$", content)
    business_rules = [
        {"code": r[0], "description": r[1].strip()}
        for r in rules
        if r[0].upper().startswith(("R-", "RM-", "REGLE", "RULE"))
    ]

    evidence_data = None
    evidence_dirs = [p_root / "memory" / "evidence", REPO_ROOT / "memory" / "evidence"]
    for ev_dir in evidence_dirs:
        if ev_dir.exists():
            cand = ev_dir / f"{story_id}_evidence.json"
            if not cand.exists():
                cand = ev_dir / f"{found_file.stem}_evidence.json"
            if cand.exists():
                try:
                    evidence_data = json.loads(cand.read_text(encoding="utf-8"))
                    break
                except Exception as e:
                    logger.debug(
                        "Lecture de l'EvidencePack échouée, story affichée sans preuve",
                        exc_info=True,
                        extra={
                            "component": "dashboard.server",
                            "operation": "get_project_story_detail",
                            "evidence_path": str(cand),
                            "error": str(e),
                        },
                    )

    return {
        "project": target_project,
        "id": meta.get("id", story_id),
        "story_id": meta.get("id", story_id),
        "title": meta.get("title", found_file.stem),
        "status": meta.get("status", "OPEN"),
        "type": meta.get("type", "feature"),
        "layer": meta.get("layer", "vertical-slice"),
        "jira_key": meta.get("jira_key", ""),
        "epic_key": meta.get("epic_key", ""),
        "file_path": found_file.relative_to(REPO_ROOT).as_posix()
        if found_file.is_relative_to(REPO_ROOT)
        else found_file.name,
        "scenarios": scenarios,
        "business_rules": business_rules,
        "has_evidence": evidence_data is not None,
        "evidence": evidence_data,
        "raw_markdown": body,
    }


@app.get("/api/rho-rules")
def get_rho_rules(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Retourne l'inventaire des règles d'auto-amélioration et d'exclusion sémantiques RHO (ST-104).
    """
    import yaml

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

    def _parse_yaml(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            data = yaml.safe_load(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("rules", [data])
            return []
        except Exception:
            return []

    global_rules = _parse_yaml(global_rules_file)
    local_rules = []
    for lc in local_candidates:
        if lc.exists() and lc != global_rules_file:
            local_rules = _parse_yaml(lc)
            if local_rules:
                break

    return {
        "project": target_project,
        "global_rules_count": len(global_rules),
        "local_rules_count": len(local_rules),
        "global_rules": global_rules,
        "local_rules": local_rules,
    }


@app.get("/api/stories")
def get_stories(project: Optional[str] = None, module: Optional[str] = None) -> Dict[str, Any]:
    """
    Scanne les User Stories du projet récursivement, extrait leur statut et inspecte leurs EvidencePacks.
    Supporte le filtrage par module/epic (ex: 01-reception, OneTrust).
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    backlog_root = p_root / "backlog"
    # Si racine mLoop, inclure aussi Projects/mLoop-Dashboard/backlog
    backlog_roots = [backlog_root]
    if target_project in ("Memory Loop", "ALL"):
        dash_b = REPO_ROOT / "Projects" / "mLoop-Dashboard" / "backlog"
        if dash_b.exists():
            backlog_roots.append(dash_b)
        if target_project == "ALL":
            projects_dir = REPO_ROOT / "Projects"
            if projects_dir.exists():
                for p in projects_dir.iterdir():
                    if (
                        p.is_dir()
                        and not p.name.startswith(".")
                        and not p.name.startswith("_")
                        and p.name.lower() not in {"default", "cacheproj", "timeoutproj"}
                    ):
                        pb = p / "backlog"
                        if pb.exists() and pb not in backlog_roots:
                            backlog_roots.append(pb)

    # 1. Scanner le sprint_backlog.md pour extraire la table de métadonnées officielles
    sprint_table: Dict[str, Dict[str, str]] = {}
    for b_root in backlog_roots:
        sb_file = b_root / "sprint_backlog.md"
        if sb_file.exists():
            try:
                sb_text = sb_file.read_text(encoding="utf-8", errors="ignore")
                for row in re.finditer(
                    r"\|\s*([A-Za-z0-9_\-]+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]*)\|", sb_text
                ):
                    s_id = row.group(1).strip()
                    s_title = row.group(2).strip()
                    s_status = row.group(3).strip().upper()
                    s_jira = row.group(4).strip()
                    if s_id.lower() not in ("id", "---"):
                        sprint_table[s_id] = {
                            "title": s_title,
                            "status": s_status,
                            "jira_key": s_jira,
                        }
            except Exception as e:
                logger.warning(
                    "Lecture de sprint_backlog.md échouée, table de métadonnées indisponible",
                    exc_info=True,
                    extra={
                        "component": "dashboard.server",
                        "operation": "get_stories",
                        "sprint_backlog": str(sb_file),
                        "error": str(e),
                    },
                )

    # 2. Indexer tous les EvidencePacks existants (recherche récursive)
    evidence_index: Dict[str, Path] = {}
    evidence_dirs = [p_root / "memory" / "evidence", REPO_ROOT / "memory" / "evidence"]
    for ev_dir in evidence_dirs:
        if ev_dir.exists():
            for ev_file in ev_dir.rglob("*.json"):
                stem = ev_file.stem.replace("_evidence", "")
                evidence_index[stem.lower()] = ev_file

    stories = []
    seen_ids = set()

    for b_root in backlog_roots:
        if not b_root.exists():
            continue
        # Scan récursif pour découvrir toutes les sous-catégories (01-reception, etc.)
        for md_file in b_root.rglob("*.md"):
            rel_parts = [p.lower() for p in md_file.relative_to(b_root).parts]
            if any(
                x in rel_parts
                for x in ("reviews", "gates", "archive", "templates", "tmp", "handoff")
            ):
                continue
            if md_file.name.lower() in ("sprint_backlog.md", "readme.md", "wayfinder_map.md"):
                continue

            story_mod = get_story_module(md_file, b_root.parent)
            if module and module.strip() and module.strip().upper() not in ("ALL", "*", "TOUS"):
                if not match_module_entry(str(md_file), module.strip()):
                    continue
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                story_id = md_file.stem
                title = md_file.stem
                status = "OPEN"
                stype = "Feature"
                layer = "vertical-slice"
                jira_key = ""
                epic_key = ""

                # Parser frontmatter YAML
                fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                if fm_match:
                    fm_text = fm_match.group(1)
                    for line in fm_text.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k = k.strip().lower()
                            v = v.strip().strip("'\"")
                            if k == "id":
                                story_id = v
                            elif k == "title":
                                title = v
                            elif k == "status":
                                status = v.upper()
                            elif k == "type":
                                stype = v
                            elif k == "layer":
                                layer = v
                            elif k == "jira_key":
                                jira_key = v
                            elif k == "epic_key":
                                epic_key = v

                # Enrichir avec la table sprint_backlog.md si présente
                if story_id in sprint_table:
                    sb_info = sprint_table[story_id]
                    if sb_info.get("status") and status == "OPEN":
                        status = sb_info["status"]
                    if sb_info.get("jira_key") and not jira_key:
                        jira_key = sb_info["jira_key"]
                    if sb_info.get("title") and title == md_file.stem:
                        title = sb_info["title"]

                # Chercher titre H1 si non trouvé
                if title == md_file.stem:
                    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if h1_match:
                        title = h1_match.group(1).strip()

                if story_id in seen_ids:
                    continue
                seen_ids.add(story_id)

                # Vérifier présence de l'EvidencePack via l'index récursif
                ev_candidate = evidence_index.get(story_id.lower()) or evidence_index.get(
                    md_file.stem.lower()
                )
                has_evidence = ev_candidate is not None
                evidence_info = {}

                if has_evidence and ev_candidate:
                    try:
                        ev_data = json.loads(ev_candidate.read_text(encoding="utf-8"))
                        evidence_info = {
                            "risk_level": ev_data.get("highest_risk", "LOW"),
                            "total_items": len(ev_data.get("items", []))
                            or len(ev_data.get("facts_verified", [])),
                            "confidence_score": ev_data.get("root_score", 1.0),
                            "file_name": ev_candidate.name,
                        }
                    except Exception as e:
                        logger.debug(
                            "Lecture de l'EvidencePack échouée, métadonnées de preuve ignorées",
                            exc_info=True,
                            extra={
                                "component": "dashboard.server",
                                "operation": "get_stories",
                                "evidence_path": str(ev_candidate),
                                "error": str(e),
                            },
                        )

                scenario_count = len(re.findall(r"(?im)^\s*(?:Scénario|Scenario)\s*:", content))

                rel_path = (
                    md_file.relative_to(p_root).as_posix()
                    if p_root != REPO_ROOT
                    else md_file.relative_to(REPO_ROOT).as_posix()
                )

                stories.append(
                    {
                        "id": story_id,
                        "title": title,
                        "status": status,
                        "type": stype,
                        "layer": layer,
                        "module": story_mod,
                        "jira_key": jira_key,
                        "epic_key": epic_key,
                        "file_path": rel_path,
                        "has_evidence": has_evidence,
                        "evidence_info": evidence_info,
                        "scenario_count": scenario_count,
                    }
                )
            except Exception as e:
                logger.debug(
                    "Parsing d'un fichier story échoué, récit ignoré dans le scan du backlog",
                    exc_info=True,
                    extra={
                        "component": "dashboard.server",
                        "operation": "get_stories",
                        "story_file": str(md_file),
                        "error": str(e),
                    },
                )
                continue

    status_order = {
        "READY_FOR_DEV": 1,
        "IN_BUILD": 2,
        "IN_QA": 3,
        "IN_PLAN": 4,
        "IN_ANALYZE": 5,
        "OPEN": 6,
        "DONE": 7,
        "ACCEPTED": 8,
    }
    stories.sort(key=lambda x: (status_order.get(x["status"], 99), x["id"]))

    by_mod: Dict[str, Dict[str, Any]] = {}
    for item in stories:
        m = item.get("module") or "default"
        if m not in by_mod:
            by_mod[m] = {"total": 0, "status_counts": {}}
        by_mod[m]["total"] += 1
        st = item.get("status", "OPEN")
        by_mod[m]["status_counts"][st] = by_mod[m]["status_counts"].get(st, 0) + 1

    return {
        "project": target_project,
        "module": module,
        "total_stories": len(stories),
        "stories": stories,
        "status_counts": {
            s: sum(1 for item in stories if item["status"] == s)
            for s in set(item["status"] for item in stories)
        },
        "by_module": by_mod,
    }


@app.get("/api/graph")
def get_graph_stats(project: Optional[str] = None) -> Dict[str, Any]:
    """
    Statistiques du graphe de connaissances (Ground Truth) et de l'hypergraphe.
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)

    graph_candidates = [
        p_root / "memory" / "knowledge_graph.json",
        p_root / "memory" / "hypergraph.json",
        p_root / "graphify-out" / "graph.json",
        REPO_ROOT / "memory" / "knowledge_graph.json",
        REPO_ROOT / "graphify-out" / "graph.json",
    ]

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    for gc in graph_candidates:
        if gc.exists():
            try:
                data = json.loads(gc.read_text(encoding="utf-8"))
                if "nodes" in data and isinstance(data["nodes"], list):
                    nodes.extend(data["nodes"])
                if "edges" in data and isinstance(data["edges"], list):
                    edges.extend(data["edges"])
                if nodes:
                    break
            except Exception as e:
                logger.debug(
                    "Lecture d'un fichier de graphe échouée, candidat suivant essayé",
                    exc_info=True,
                    extra={
                        "component": "dashboard.server",
                        "operation": "get_graph_stats",
                        "graph_path": str(gc),
                        "error": str(e),
                    },
                )

    unique_nodes = {}
    for n in nodes:
        nid = n.get("id") or n.get("name")
        if nid and nid not in unique_nodes:
            unique_nodes[nid] = n

    node_types: Dict[str, int] = {}
    for n in unique_nodes.values():
        ntype = n.get("type") or n.get("layer") or n.get("label") or "Concept"
        node_types[ntype] = node_types.get(ntype, 0) + 1

    sample_nodes = list(unique_nodes.values())[:15]

    return {
        "project": target_project,
        "total_nodes": len(unique_nodes),
        "total_edges": len(edges),
        "node_types": node_types,
        "sample_nodes": sample_nodes,
    }


@app.get("/api/state")
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


# ── MONTER LE FRONTEND WEB ─────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def get_index():
    """Sert l'interface Web d'observabilité principale."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>mLoop Dashboard : index.html introuvable</h1>", status_code=404)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
