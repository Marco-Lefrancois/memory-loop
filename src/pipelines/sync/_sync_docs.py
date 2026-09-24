"""
_sync_docs.py — Sous-module Sync : cache disque, directives, questions ouvertes & sprint backlog.

Responsabilités :
  - load_sync_cache / save_sync_cache      : persistance JSON du cache de synchronisation
  - sync_project_directives                : consolidation des ADRs dans business.md
  - sync_open_questions                    : résolution OQs -> wayfinder_map.md + deblocage stories
  - sync_sprint_backlog                    : alignement YAML stories <-> sprint_backlog.md (SSOT)

ADR-0202 (RULE-AST-01) : <= 300 L / 15 Ko.
ADR-0369              : aucun appel reseau dans ce module (tout est FS local).

Note logger : les fonctions utilisent _get_logger() (lookup dynamique via sys.modules) pour
garantir que patch.object(sync, "logger") dans test_sync_logging.py intercepte les appels
(compatibilite MLOOP-141-BE sans modifier les tests existants).
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

_fallback_logger = get_logger("pipelines.sync")


def _get_logger():
    """Retourne sync.logger (patchable par patch.object) ou le fallback."""
    sync_mod = sys.modules.get("src.pipelines.sync")
    if sync_mod is not None:
        return getattr(sync_mod, "logger", _fallback_logger)
    return _fallback_logger


# --- Cache disque ---


def load_sync_cache(project_path: Path) -> dict:
    """Charge le cache de synchronisation depuis memory/cache/sync_state.json."""
    cache_file = project_path / "memory" / "cache" / "sync_state.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            _get_logger().error(
                f"Erreur de lecture du cache de synchronisation '{cache_file}'.",
                exc_info=True,
                extra={"subsystem": "cache", "project": project_path.name},
            )
    return {"stories": {}, "questions": {}}


def save_sync_cache(project_path: Path, cache: dict) -> None:
    """Persiste le cache de synchronisation sur disque."""
    cache_dir = project_path / "memory" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "sync_state.json"
    cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


# --- Directives projet ---


def sync_project_directives(project_name: str, project_path: Path) -> None:
    """Synchronise automatiquement les directives et le journal de memoire a partir des ADRs."""
    directives_dir = project_path / "directives"
    architecture_dir = project_path / "docs" / "01-architecture"

    # Creation systematique de la structure canonique de memory (ADR-0100)
    memory_base = project_path / "memory"
    memory_subdirs = ["sessions", "debates", "sync", "reports", "cache", "tmp"]
    for sdir in memory_subdirs:
        (memory_base / sdir).mkdir(parents=True, exist_ok=True)

    # Verification et consolidation des directives
    bus_file = directives_dir / "business.md"
    if architecture_dir.exists() and bus_file.exists():
        adrs = list(architecture_dir.glob("ADR-*.md"))
        if adrs:
            content = bus_file.read_text(encoding="utf-8")

            start_marker = "<!-- BEGIN_ADR_LIST -->"
            end_marker = "<!-- END_ADR_LIST -->"

            new_adr_block = start_marker + "\n"
            for adr in adrs:
                new_adr_block += (
                    f"- **Reference ADR ({adr.stem})** : Decision enregistree sous"
                    f" [{adr.name}](file:///{adr.as_posix()}).\n"
                )
            new_adr_block += end_marker

            if start_marker in content and end_marker in content:
                content = re.sub(
                    rf"{start_marker}.*?{end_marker}",
                    new_adr_block,
                    content,
                    flags=re.DOTALL,
                )
            else:
                content += "\n\n" + new_adr_block

            bus_file.write_text(content, encoding="utf-8")


# --- Questions ouvertes ---


def sync_open_questions(project_name: str, project_path: Path) -> None:
    """Synchronise automatiquement l'etat des questions ouvertes vers le wayfinder."""
    transverse_dir = project_path / "docs" / "04-transverse"
    wayfinder_file = project_path / "backlog" / "wayfinder_map.md"

    if not transverse_dir.exists() or not wayfinder_file.exists():
        return

    resolved_qs: set[str] = set()
    open_qs: set[str] = set()
    cache = load_sync_cache(project_path)

    for md_file in transverse_dir.glob("00-questions-ouvertes-*.md"):
        mtime = os.path.getmtime(md_file)
        file_key = md_file.as_posix()

        file_cache = cache["questions"].get(file_key, {})
        if file_cache.get("mtime") == mtime:
            resolved_qs.update(file_cache.get("resolved", []))
            open_qs.update(file_cache.get("open", []))
            continue

        content = md_file.read_text(encoding="utf-8")
        file_resolved: set[str] = set()
        file_open: set[str] = set()

        # 1. Parsing Section Format: ### Q-XXX ou ### QD-XXX ... - **Decision** :
        sections = re.split(r"(?m)^###\s+((?:Q|QD)-\d+)", content)
        for i in range(1, len(sections), 2):
            q_id = sections[i]
            body = sections[i + 1] if i + 1 < len(sections) else ""
            if re.search(r"-\s*\*\*(?:Decision|Decision)\*\*\s*:", body, re.IGNORECASE):
                file_resolved.add(q_id)
            else:
                file_open.add(q_id)

        # 2. Parsing Table Format: | Q-XXX | ... | Decision/Archive/CLOSED | ...
        for match in re.finditer(r"(?m)^\|\s*((?:Q|QD)-\d+)\s*\|.*?\|\s*([^|]+)\s*\|", content):
            q_id = match.group(1)
            status_text = match.group(2).lower()
            if any(
                k in status_text
                for k in [
                    "decision",
                    "valide",
                    "archive",
                    "closed",
                ]
            ):
                file_resolved.add(q_id)
            else:
                if q_id not in file_resolved:
                    file_open.add(q_id)

        cache["questions"][file_key] = {
            "mtime": mtime,
            "resolved": list(file_resolved),
            "open": list(file_open),
        }
        resolved_qs.update(file_resolved)
        open_qs.update(file_open)

    save_sync_cache(project_path, cache)

    if not resolved_qs and not open_qs:
        return

    # Mise a jour wayfinder_map.md
    wf_content = wayfinder_file.read_text(encoding="utf-8")
    original_wf = wf_content

    for q_id in resolved_qs:
        wf_content = re.sub(rf"(?m)^(\s*-\s*)\[\s\](.*?\b{q_id}\b.*)$", r"\1[x]\2", wf_content)
    for q_id in open_qs:
        wf_content = re.sub(rf"(?m)^(\s*-\s*)\[x\](.*?\b{q_id}\b.*)$", r"\1[ ]\2", wf_content)

    if wf_content != original_wf:
        wayfinder_file.write_text(wf_content, encoding="utf-8")
        ZeroFluffConsole.info(
            "[Sync] Mise a jour automatique de l'etat des OQs dans wayfinder_map.md."
        )

    # Deblocage automatique des stories
    stories_dir = project_path / "backlog" / "stories"
    if stories_dir.exists() and resolved_qs:
        for story_file in stories_dir.rglob("*.md"):
            content = story_file.read_text(encoding="utf-8")
            original_content = content
            for q_id in resolved_qs:
                content = re.sub(
                    rf"(?m)^(>.*?BLOQUE.*?\b{q_id}\b.*)$",
                    rf"> DEBLOQUE : {q_id} (Decision actee)",
                    content,
                    flags=re.IGNORECASE,
                )
            if content != original_content:
                resolved_list = ", ".join(sorted(resolved_qs))
                story_file.write_text(content, encoding="utf-8")
                ZeroFluffConsole.info(
                    f"[Sync] Story {story_file.stem} debloqu\u00e9e (OQ {resolved_list})."
                )


# --- Sprint backlog ---

from src.pipelines.sync._sync_backlog_parser import parse_backlog_status_maps


def sync_sprint_backlog(project_name: str, project_path: Path) -> None:
    """
    Synchronise sprint_backlog.md (SSOT Master) et les en-tetes YAML des fichiers de recits.

    Algorithme colonne-aware (fix FRAMEWORK-SELFDEV-SYNC-BACKLOG) :
    - Localise dynamiquement la colonne 'Statut' via parse_backlog_status_maps().
    - Vocabulaire etendu : DONE_TESTED, DRAFT, TOMBSTONE inclus.
    - Supporte tout prefixe (REC, INC, US, Jira) et tout schema de tableau.
    """
    stories_dir = project_path / "backlog" / "stories"
    backlog_file = project_path / "backlog" / "sprint_backlog.md"

    if not stories_dir.exists() or not backlog_file.exists():
        return

    direct_id_status_map, status_map = parse_backlog_status_maps(backlog_file)

    updated_files = 0
    for f in stories_dir.rglob("*.md"):
        category = f.parent.name
        fc = f.read_text(encoding="utf-8")
        m_yaml = re.search(r"^---\n(.*?)\n---", fc, re.DOTALL)
        if not m_yaml:
            continue
        yaml_text = m_yaml.group(1)

        m_id_yaml = re.search(r"(?m)^id:\s*(.+)$", yaml_text)
        story_id = m_id_yaml.group(1).strip().strip("'\"") if m_id_yaml else f.stem

        target_status = (
            direct_id_status_map.get(story_id.upper())
            or status_map.get((category, story_id.upper()))
            or direct_id_status_map.get(f.stem.upper())
        )
        if target_status:
            m_curr = re.search(r"(?m)^status:\s*(.+)$", yaml_text)
            curr_status = m_curr.group(1).strip() if m_curr else None
            if curr_status != target_status:
                new_yaml = re.sub(r"(?m)^status:\s*.+$", f"status: {target_status}", yaml_text)
                f.write_text(fc.replace(yaml_text, new_yaml, 1), encoding="utf-8")
                updated_files += 1

    if updated_files > 0:
        ZeroFluffConsole.info(
            f"[Sync] {updated_files} fichier(s) de recit(s) realigne(s) sur le statut de"
            " sprint_backlog.md (SSOT)."
        )
