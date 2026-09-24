"""
_sync_backlog_parser.py — Parsing colonne-aware du sprint_backlog.md (SSOT).

Extrait du sprint_backlog.md la map {story_id -> statut} en localisant
dynamiquement la colonne 'Statut' dans chaque en-tete de tableau Markdown.

Extrait de _sync_docs.py (FRAMEWORK-SELFDEV-SYNC-BACKLOG) pour respecter
ADR-0202 (≤ 300 L / 15 Ko) sans modifier la signature publique de sync_sprint_backlog.

ADR-0369 : aucun appel reseau ; zéro except: pass ; logging extra={...}.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Vocabulaire complet des statuts reconnus dans la colonne Statut du backlog.
# Ordre : DONE_TESTED avant DONE pour eviter tout matching prefixe incorrect.
STATUS_VOCAB_RE = re.compile(
    r"\b(ACCEPTED|DONE_TESTED|DONE|IN_QA|IN_DEV|READY_FOR_DEV|READY_FOR_GROOMING"
    r"|IN_REVIEW|IN-REVIEW|IN_VALIDATE|IN_PLAN|IN_ANALYZE|OPEN"
    r"|ON_HOLD|ON-HOLD|CLOSED|BACKLOG|DRAFT|TOMBSTONE)\b",
    re.IGNORECASE,
)

_ID_RE = re.compile(r"\b([A-Z0-9]+(?:-[A-Z0-9]+)+)\b")
_SEPARATOR_RE = re.compile(r"^\|[\s|:\-]+\|")


def _norm(txt: str) -> str:
    """Normalise une chaine : NFKD → ASCII → majuscules."""
    return unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8").upper()


def _find_statut_col_index(header_cells: list[str]) -> int | None:
    """
    Retourne l'index (base-0 dans la liste cells issue de line.split('|'))
    de la colonne dont le libelle normalise est 'STATUT', ou None si absente.

    cells = ['', ' Col1 ', ' Col2 ', ..., '']  (split sur '|' avec bordures)
    => index 0 est toujours vide (avant le premier pipe), index -1 aussi.
    """
    for idx, cell in enumerate(header_cells):
        if _norm(cell.strip()) == "STATUT":
            return idx
    return None


def parse_backlog_status_maps(
    backlog_file: Path,
) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    """
    Parse sprint_backlog.md et retourne deux maps :
      - direct_id_status_map  : {story_id_upper -> statut}
      - status_map            : {(categorie_upper, story_id_upper) -> statut}

    Algorithme colonne-aware :
    1. Detecte les sections ## / ### / MODULE / CODEBASE comme categories.
    2. Sur un separateur (|---|), inspecte la ligne precedente pour localiser
       dynamiquement l'index de la colonne 'Statut'.
    3. Sur les lignes de donnees, extrait le statut uniquement depuis cette cellule.
    4. Ne filtre JAMAIS les cellules vides avant indexation (stabilite d'indice).
    """
    direct_id_status_map: dict[str, str] = {}
    status_map: dict[tuple[str, str], str] = {}

    content = backlog_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    current_cat: str | None = None
    i_statut: int | None = None
    header_cells_len: int = 0

    for line_idx, line in enumerate(lines):
        nline = _norm(line)

        # Detection section categorie
        if (
            "CODEBASE :" in nline
            or "MODULE :" in nline
            or nline.startswith("## ")
            or nline.startswith("### ")
        ):
            current_cat = (
                nline.replace("#", "").replace("MODULE :", "").replace("CODEBASE :", "").strip()
            )
            i_statut = None
            header_cells_len = 0
            continue

        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        # Detecter separateur tableau (|---|, | :---|, |:---|)
        is_separator = bool(_SEPARATOR_RE.match(stripped)) and "---" in stripped

        if is_separator:
            # La ligne precedente est l'en-tete du tableau
            if line_idx > 0:
                prev = lines[line_idx - 1]
                if prev.strip().startswith("|"):
                    prev_cells = prev.split("|")
                    found = _find_statut_col_index(prev_cells)
                    if found is not None:
                        i_statut = found
                        header_cells_len = len(prev_cells)
                    else:
                        # En-tete sans colonne Statut : ignorer ce bloc
                        i_statut = None
                        header_cells_len = 0
            continue

        # Ligne de donnees
        if i_statut is None:
            continue  # Pas de colonne Statut pour ce bloc => ignorer

        cells = line.split("|")
        if len(cells) != header_cells_len:
            continue  # Incoherence de colonnes => ignorer proprement

        # Extraire la valeur de la cellule Statut
        raw_cell = cells[i_statut].strip()
        m_statut = STATUS_VOCAB_RE.search(raw_cell)
        if not m_statut:
            continue

        st_val = m_statut.group(1).upper().replace("-", "_")

        # Extraire les IDs de la ligne entiere
        m_ids = _ID_RE.findall(line)
        if not m_ids:
            continue

        for s_id in m_ids:
            direct_id_status_map[s_id.upper()] = st_val
            if current_cat:
                status_map[(current_cat, s_id.upper())] = st_val

    return direct_id_status_map, status_map
