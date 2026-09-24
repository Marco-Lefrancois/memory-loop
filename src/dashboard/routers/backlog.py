# -*- coding: utf-8 -*-
"""
src/dashboard/routers/backlog.py — Routeur FastAPI pour la visualisation et inspection du Backlog mLoop.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from src.dashboard.module_utils import get_story_module, match_module_entry
from src.dashboard.project_utils import (
    resolve_project_canonical_name as _resolve_project_canonical_name,
    resolve_project_path as _get_project_root,
)
from src.dashboard.routers._backlog_helpers import (
    build_evidence_index,
    parse_sprint_table,
    parse_story_detail,
    resolve_backlog_roots,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.backlog")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

router = APIRouter(tags=["Backlog & Stories"])

STATUS_ORDER = {
    "READY_FOR_DEV": 1,
    "IN_BUILD": 2,
    "IN_QA": 3,
    "IN_PLAN": 4,
    "IN_ANALYZE": 5,
    "OPEN": 6,
    "DONE": 7,
    "ACCEPTED": 8,
}


@router.get("/api/backlog/{project_name}")
def get_project_backlog(project_name: str, module: Optional[str] = None) -> Dict[str, Any]:
    """Retourne la liste des User Stories d'un projet pour le Backlog Drawer (ST-114)."""
    return get_stories(project=project_name, module=module)


@router.get("/api/backlog/{project_name}/{story_id}")
def get_project_story_detail(project_name: str, story_id: str) -> Dict[str, Any]:
    """
    Retourne le détail complet d'une User Story pour inspection approfondie dans le Backlog Drawer.
    """
    target_project = _resolve_project_canonical_name(project_name)
    p_root = _get_project_root(target_project)
    backlog_roots = resolve_backlog_roots(target_project, p_root, REPO_ROOT)

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

    return parse_story_detail(found_file, story_id, p_root, REPO_ROOT, target_project)


@router.get("/api/stories")
def get_stories(project: Optional[str] = None, module: Optional[str] = None) -> Dict[str, Any]:
    """
    Scanne les User Stories du projet récursivement, extrait leur statut et inspecte leurs EvidencePacks.
    Supporte le filtrage par module/epic (ex: 01-reception, OneTrust).
    """
    target_project = _resolve_project_canonical_name(project)
    p_root = _get_project_root(target_project)
    backlog_roots = resolve_backlog_roots(target_project, p_root, REPO_ROOT)

    sprint_table = parse_sprint_table(backlog_roots)
    evidence_index = build_evidence_index(p_root, REPO_ROOT)

    stories = []
    seen_ids = set()

    for b_root in backlog_roots:
        if not b_root.exists():
            continue
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
                with open(md_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                story_id = md_file.stem
                title = md_file.stem
                status = "OPEN"
                stype = "Feature"
                layer = "vertical-slice"
                jira_key = ""
                epic_key = ""

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

                if story_id in sprint_table:
                    sb_info = sprint_table[story_id]
                    if sb_info.get("status") and status == "OPEN":
                        status = sb_info["status"]
                    if sb_info.get("jira_key") and not jira_key:
                        jira_key = sb_info["jira_key"]
                    if sb_info.get("title") and title == md_file.stem:
                        title = sb_info["title"]

                if title == md_file.stem:
                    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if h1_match:
                        title = h1_match.group(1).strip()

                if story_id in seen_ids:
                    continue
                seen_ids.add(story_id)

                ev_candidate = evidence_index.get(story_id.lower()) or evidence_index.get(
                    md_file.stem.lower()
                )
                has_evidence = ev_candidate is not None
                evidence_info = {}

                if has_evidence and ev_candidate:
                    try:
                        with open(ev_candidate, "r", encoding="utf-8") as f:
                            ev_data = json.load(f)
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
                                "component": "dashboard.routers.backlog",
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
                        "component": "dashboard.routers.backlog",
                        "operation": "get_stories",
                        "story_file": str(md_file),
                        "error": str(e),
                    },
                )
                continue

    stories.sort(key=lambda x: (STATUS_ORDER.get(x["status"], 99), x["id"]))

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
