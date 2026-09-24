# -*- coding: utf-8 -*-
"""
src/dashboard/routers/_backlog_helpers.py — Helpers d'indexation, parsing et scan du Backlog et des preuves.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (robustesse Python senior).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("dashboard.routers.backlog_helpers")


def resolve_backlog_roots(target_project: str, p_root: Path, repo_root: Path) -> List[Path]:
    """Résout l'ensemble des dossiers backlog à scanner pour le projet ciblé."""
    backlog_roots = [p_root / "backlog"]
    if target_project in ("Memory Loop", "ALL"):
        dash_b = repo_root / "Projects" / "mLoop-Dashboard" / "backlog"
        if dash_b.exists():
            backlog_roots.append(dash_b)
        if target_project == "ALL":
            projects_dir = repo_root / "Projects"
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
    return backlog_roots


def parse_sprint_table(backlog_roots: List[Path]) -> Dict[str, Dict[str, str]]:
    """Scanne les fichiers sprint_backlog.md pour extraire la table de métadonnées officielles."""
    sprint_table: Dict[str, Dict[str, str]] = {}
    for b_root in backlog_roots:
        sb_file = b_root / "sprint_backlog.md"
        if sb_file.exists():
            try:
                with open(sb_file, "r", encoding="utf-8", errors="ignore") as f:
                    sb_text = f.read()
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
                        "component": "dashboard.routers.backlog_helpers",
                        "operation": "parse_sprint_table",
                        "sprint_backlog": str(sb_file),
                        "error": str(e),
                    },
                )
    return sprint_table


def build_evidence_index(p_root: Path, repo_root: Path) -> Dict[str, Path]:
    """Indexe tous les EvidencePacks existants (recherche récursive)."""
    evidence_index: Dict[str, Path] = {}
    evidence_dirs = [p_root / "memory" / "evidence", repo_root / "memory" / "evidence"]
    for ev_dir in evidence_dirs:
        if ev_dir.exists():
            for ev_file in ev_dir.rglob("*.json"):
                stem = ev_file.stem.replace("_evidence", "")
                evidence_index[stem.lower()] = ev_file
    return evidence_index


def parse_story_detail(
    found_file: Path,
    story_id: str,
    p_root: Path,
    repo_root: Path,
    target_project: str,
) -> Dict[str, Any]:
    """Extrait le détail complet d'une User Story (Gherkin, règles, preuves)."""
    with open(found_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

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

    rules = re.findall(r"(?im)^\s*[\*\-]\s*`?([A-Za-z0-9_\-]+)`?\s*:\s*(.+)$", content)
    business_rules = [
        {"code": r[0], "description": r[1].strip()}
        for r in rules
        if r[0].upper().startswith(("R-", "RM-", "REGLE", "RULE"))
    ]

    evidence_data = None
    evidence_dirs = [p_root / "memory" / "evidence", repo_root / "memory" / "evidence"]
    for ev_dir in evidence_dirs:
        if ev_dir.exists():
            cand = ev_dir / f"{story_id}_evidence.json"
            if not cand.exists():
                cand = ev_dir / f"{found_file.stem}_evidence.json"
            if cand.exists():
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        evidence_data = json.load(f)
                    break
                except Exception as e:
                    logger.debug(
                        "Lecture de l'EvidencePack échouée, story affichée sans preuve",
                        exc_info=True,
                        extra={
                            "component": "dashboard.routers.backlog_helpers",
                            "operation": "parse_story_detail",
                            "evidence_path": str(cand),
                            "error": str(e),
                        },
                    )

    rel_path = (
        found_file.relative_to(repo_root).as_posix()
        if found_file.is_relative_to(repo_root)
        else found_file.name
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
        "file_path": rel_path,
        "scenarios": scenarios,
        "business_rules": business_rules,
        "has_evidence": evidence_data is not None,
        "evidence": evidence_data,
        "raw_markdown": body,
    }
