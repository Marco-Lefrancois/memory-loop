# -*- coding: utf-8 -*-
"""
src/dashboard/routers/_ledger_helpers.py — Helpers d'extraction et normalisation du Token Ledger.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from src.dashboard.module_utils import (
    get_module_friendly_info,
    match_module_entry,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.ledger_helpers")

KNOWN_MODULE_CANDIDATES = (
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
)


def collect_raw_ledger_entries(
    target_project: str, p_root: Path, repo_root: Path
) -> List[Dict[str, Any]]:
    """Scanne et normalise l'ensemble des entrées JSONL du Token Ledger."""
    ledger_files: List[Tuple[Path, bool]] = []

    # 1. Fichier spécifique projet si existant
    if p_root != repo_root and target_project != "ALL":
        proj_ledger = p_root / "memory" / "token_ledger.jsonl"
        if proj_ledger.exists():
            ledger_files.append((proj_ledger, True))

    # 2. Fichier global racine
    global_ledger = repo_root / "memory" / "token_ledger.jsonl"
    if global_ledger.exists():
        ledger_files.append((global_ledger, False))

    # Si ALL ou racine, scanner aussi les dossiers de projets pour exhaustivité
    if target_project in ("ALL", "Memory Loop"):
        projects_dir = repo_root / "Projects"
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
    seen_fingerprints: Set[str] = set()

    for l_path, _ in ledger_files:
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
                            for cand in KNOWN_MODULE_CANDIDATES:
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
                                "component": "dashboard.routers.ledger_helpers",
                                "operation": "collect_raw_ledger_entries",
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
                    "component": "dashboard.routers.ledger_helpers",
                    "operation": "collect_raw_ledger_entries",
                    "ledger_path": str(l_path),
                    "error": str(e),
                },
            )

    raw_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return raw_entries


def compute_global_summaries(
    raw_entries: List[Dict[str, Any]],
) -> Tuple[
    Set[str],
    Set[str],
    Set[str],
    Set[str],
    int,
    float,
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    """Calcule la synthèse consolidée (modèles, actions, projets, sources, totaux) sur toutes les entrées."""
    all_models: Set[str] = set()
    all_actions: Set[str] = set()
    all_projects: Set[str] = set()
    all_sources: Set[str] = {"llm_nmedia_cloud", "antigravity-chat", "opencode-desktop"}
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

        s_name = e.get("source") or "nmedia_cloud"
        if s_name in ("opencode-desktop", "opencode"):
            s_name = "opencode-desktop"
        elif s_name in ("antigravity-chat", "Google", "antigravity") or (
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

        if summary_key not in by_project_summary:
            by_project_summary[summary_key] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        by_project_summary[summary_key]["calls"] += 1
        by_project_summary[summary_key]["tokens"] += toks
        by_project_summary[summary_key]["cost_usd"] += cost

        if s_name not in by_source_summary:
            by_source_summary[s_name] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        by_source_summary[s_name]["calls"] += 1
        by_source_summary[s_name]["tokens"] += toks
        by_source_summary[s_name]["cost_usd"] += cost

    for bp in by_project_summary.values():
        bp["cost_usd"] = round(bp["cost_usd"], 4)
    for bs in by_source_summary.values():
        bs["cost_usd"] = round(bs["cost_usd"], 4)

    return (
        all_models,
        all_actions,
        all_projects,
        all_sources,
        global_total_tokens,
        global_total_cost,
        by_project_summary,
        by_source_summary,
    )
