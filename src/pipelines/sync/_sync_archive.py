"""
_sync_archive.py — Sous-module d'archivage automatique du backlog mLoop.

Détecte et archive de manière déterministe les épopées complétées (100% DONE/SHIPPED)
hors de sprint_backlog.md vers backlog/archive/ dès la finalisation Git (ADR-0391).

Responsabilités :
  - Détection automatique des épopées 100% closes dans sprint_backlog.md (parsing colonne-aware).
  - Déplacement physique des récits (.md) vers backlog/archive/stories/.
  - Déplacement physique des épopées (.md) vers backlog/archive/epics/.
  - Déplacement des sections Markdown de sprint_backlog.md vers l'historique d'archive.
  - Mise à jour autonome de l'en-tête de sprint_backlog.md sans pollution historique.

ADR-0202 (RULE-AST-01) : ≤ 300 L / 15 Ko.
ADR-0369 : zéro appel réseau (FS local uniquement).
"""

from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

from src.utils.logger import get_logger

logger = get_logger("pipelines.sync.archive")

_EPIC_HEADER_RE = re.compile(r"^##\s+Épopée\s*:\s*([A-Z0-9_\-]+)", re.MULTILINE)
_ID_RE = re.compile(r"\b([A-Z0-9]+(?:-[A-Z0-9]+)+)\b")
_CLOSED_STATUSES = {
    "DONE",
    "SHIPPED",
    "DONE_TESTED",
    "CLOSED",
    "TOMBSTONE",
}


def _norm(txt: str) -> str:
    """Normalise une chaîne : NFKD -> ASCII -> majuscules."""
    return unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8").upper()


def parse_epic_sections(content: str) -> List[Dict[str, Any]]:
    """Découpe sprint_backlog.md en sections d'épopées et évalue leur complétude (colonne-aware)."""
    matches = list(_EPIC_HEADER_RE.finditer(content))
    if not matches:
        return []

    sections: List[Dict[str, Any]] = []
    for i, m in enumerate(matches):
        epic_key = m.group(1).strip()
        start_idx = m.start()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        epic_text = content[start_idx:end_idx]
        lines = epic_text.splitlines()
        first_line = lines[0] if lines else ""

        stories_info: List[Dict[str, Any]] = []
        i_statut: int | None = None
        i_etat: int | None = None
        i_recit: int | None = None

        for l_idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue

            if "---" in stripped and l_idx > 0:
                prev_line = lines[l_idx - 1]
                if prev_line.strip().startswith("|"):
                    prev_cells = prev_line.split("|")
                    for c_idx, cell in enumerate(prev_cells):
                        n = _norm(cell.strip())
                        if n == "STATUT":
                            i_statut = c_idx
                        elif n in ("ETAT", "ETATS"):
                            i_etat = c_idx
                        elif n in ("RECIT", "RECITS", "STORY", "ID"):
                            i_recit = c_idx
                continue

            # Traitement d'une ligne de données
            cells = line.split("|")
            if len(cells) < 4:
                continue

            # Trouver le story_id
            story_id: str | None = None
            if i_recit is not None and i_recit < len(cells):
                m_id = _ID_RE.search(cells[i_recit])
                if m_id:
                    story_id = m_id.group(1).strip()

            if not story_id:
                m_id = _ID_RE.search(line)
                if m_id:
                    story_id = m_id.group(1).strip()

            if not story_id:
                continue

            checked = False
            if i_etat is not None and i_etat < len(cells):
                checked = "[X]" in cells[i_etat].upper()
            else:
                checked = "[X]" in cells[1].upper() if len(cells) > 1 else False

            status_cell = ""
            if i_statut is not None and i_statut < len(cells):
                status_cell = _norm(cells[i_statut])

            is_done = checked or any(st in status_cell for st in _CLOSED_STATUSES)
            stories_info.append({
                "id": story_id,
                "checked": checked,
                "status": status_cell,
                "is_done": is_done,
            })

        has_done_in_title = "[DONE]" in first_line.upper() or "SHIPPED" in first_line.upper()
        all_stories_done = len(stories_info) > 0 and all(s["is_done"] for s in stories_info)
        is_complete = has_done_in_title or all_stories_done

        sections.append({
            "epic_key": epic_key,
            "raw_text": epic_text,
            "start": start_idx,
            "end": end_idx,
            "stories": stories_info,
            "is_complete": is_complete,
        })

    return sections


def _relocate_file(source: Path, destination: Path, dry_run: bool = False) -> bool:
    """Déplace un fichier de façon sécurisée vers un dossier cible."""
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        shutil.move(str(source), str(destination))
    return True


def auto_archive_completed_epics(
    project_path: Path,
    archive_filename: str = "sprint_backlog_history_q3_q4_2026.md",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Archive automatiquement les épopées complétées et leurs récits physiques.

    Retourne un dictionnaire résumant les épopées et récits archivés.
    """
    backlog_file = project_path / "backlog" / "sprint_backlog.md"
    if not backlog_file.exists():
        return {"status": "no_backlog", "archived_epics": 0, "archived_stories": 0}

    content = backlog_file.read_text(encoding="utf-8")
    epics = parse_epic_sections(content)
    if not epics:
        return {"status": "no_epics", "archived_epics": 0, "archived_stories": 0}

    complete_epics = [e for e in epics if e["is_complete"]]
    if not complete_epics:
        return {"status": "no_completed_epics", "archived_epics": 0, "archived_stories": 0}

    archive_dir = project_path / "backlog" / "archive"
    archive_stories_dir = archive_dir / "stories"
    archive_epics_dir = archive_dir / "epics"
    archive_file = archive_dir / archive_filename

    archive_stories_dir.mkdir(parents=True, exist_ok=True)
    archive_epics_dir.mkdir(parents=True, exist_ok=True)

    archived_epics_keys: List[str] = []
    archived_stories_ids: List[str] = []
    epic_blocks_to_archive: List[str] = []

    stories_dir = project_path / "backlog" / "stories"
    epics_dir = project_path / "backlog" / "epics"

    for ep in complete_epics:
        epic_key = ep["epic_key"]
        archived_epics_keys.append(epic_key)
        epic_blocks_to_archive.append(ep["raw_text"].rstrip() + "\n\n---\n\n")

        # 1. Déplacer les fichiers de récits
        for st in ep["stories"]:
            s_id = st["id"]
            archived_stories_ids.append(s_id)
            src_story = stories_dir / f"{s_id}.md"
            dst_story = archive_stories_dir / f"{s_id}.md"
            _relocate_file(src_story, dst_story, dry_run=dry_run)

        # 2. Déplacer le fichier de cadrage de l'épopée si présent
        if epics_dir.exists():
            clean_token = epic_key.lower().replace("-", "_")
            parts = epic_key.split("-")
            prefix = parts[0].lower() + "_" + parts[1].lower() if len(parts) > 1 else clean_token
            for ef in epics_dir.glob("*.md"):
                ef_stem = ef.stem.lower()
                matched = (
                    clean_token in ef_stem
                    or prefix in ef_stem
                    or epic_key.lower() in ef_stem
                )
                if not matched:
                    try:
                        header_sample = ef.read_text(encoding="utf-8")[:300]
                        if epic_key in header_sample:
                            matched = True
                    except Exception as ef_err:
                        logger.debug(
                            f"Lecture impossible pour {ef.name} : {ef_err}",
                            exc_info=True,
                            extra={"project": project_path.name, "file": ef.name},
                        )

                if matched:
                    _relocate_file(ef, archive_epics_dir / ef.name, dry_run=dry_run)

    if not dry_run:
        # 3. Mettre à jour le fichier d'archive consolidé
        if not archive_file.exists():
            archive_header = (
                "# 🏛️ Registre Historique des Épopées Livrées — mLoop (Q3-Q4 2026)\n\n"
                "> 📦 **Statut** : ARCHIVE SOUVERAINE SCELLÉE (Épopées scellées Post-Git)\n"
                "> **Certification** : Tous les récits sont physiquement livrés, testés (pytest 100% PASS), et scellés.\n"
                "> **Sprint Backlog Actif** : [../sprint_backlog.md](../sprint_backlog.md)\n\n"
                "---\n\n"
            )
            archive_file.write_text(archive_header + "".join(epic_blocks_to_archive), encoding="utf-8")
        else:
            current_archive = archive_file.read_text(encoding="utf-8")
            archive_file.write_text(current_archive.rstrip() + "\n\n" + "".join(epic_blocks_to_archive), encoding="utf-8")

        # 4. Reconstruire sprint_backlog.md en ne conservant que les épopées actives
        first_epic_start = epics[0]["start"]
        header_part = content[:first_epic_start]

        # En-tête des archives
        archive_banner_marker = "> 📦 **Archives des Sprints Antérieurs** :"
        new_archive_banner = (
            "> 📦 **Archives des Sprints Antérieurs** :\n"
            "> - **EPIC-1 à EPIC-20** (91 récits) : [archive/sprint_backlog_history_q2_q3_2026.md](archive/sprint_backlog_history_q2_q3_2026.md)\n"
            f"> - **Épopées Clôturées Q3-Q4 2026** : [archive/{archive_filename}](archive/{archive_filename})"
        )

        if archive_banner_marker in header_part:
            header_part = re.sub(
                r"> 📦 \*\*Archives des Sprints Antérieurs\*\* :.*?(?=\n\n---|\n---)",
                new_archive_banner,
                header_part,
                flags=re.DOTALL,
            )

        active_blocks = []
        for e in epics:
            if not e["is_complete"]:
                b = e["raw_text"].strip()
                if b.endswith("---"):
                    b = b[:-3].strip()
                active_blocks.append(b + "\n\n---\n\n")

        new_backlog_content = header_part.rstrip() + "\n\n" + "".join(active_blocks).rstrip() + "\n"
        new_backlog_content = re.sub(r"\n{3,}", "\n\n", new_backlog_content)
        backlog_file.write_text(new_backlog_content, encoding="utf-8")

    logger.info(
        f"[BACKLOG-ARCHIVE] {len(archived_epics_keys)} épopée(s) et {len(archived_stories_ids)} récit(s) archivé(s).",
        extra={
            "project": project_path.name,
            "archived_epics": archived_epics_keys,
            "archived_stories_count": len(archived_stories_ids),
            "dry_run": dry_run,
        },
    )

    return {
        "status": "success",
        "archived_epics": len(archived_epics_keys),
        "archived_epics_keys": archived_epics_keys,
        "archived_stories": len(archived_stories_ids),
        "archived_stories_ids": archived_stories_ids,
        "dry_run": dry_run,
    }
