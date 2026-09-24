"""
tests/test_sync_sprint_backlog.py — Couverture dédiée du parsing colonne-aware
de sync_sprint_backlog (FRAMEWORK-SELFDEV-SYNC-BACKLOG / ADR-0369 Failure Contract).

Scénarios couverts :
  1. Nominal colonne-aware : titre contenant READY_FOR_DEV, colonne Statut = DRAFT
     → frontmatter reçoit DRAFT (pas READY_FOR_DEV).
  2. Nominal vocab : colonne Statut = DONE_TESTED → frontmatter = DONE_TESTED (pas tronqué).
  3. Nominal paramétré : TOMBSTONE / READY_FOR_DEV / DONE alignés correctement.
  4. Exception en-tête sans colonne Statut → zéro écriture, pas de crash.
  5. Exception ligne sans ID → ignorée, pas de crash.
  6. Résilience : sprint_backlog.md absent → retour None silencieux.
  7. Persistance : frontmatter déjà aligné → updated_files == 0 (zéro écriture).
  8. Table 8 colonnes Grill-me|Statut : Grill-me=PENDING, Statut=DRAFT → DRAFT.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.pipelines.sync._sync_docs import sync_sprint_backlog


# ---------------------------------------------------------------------------
# Helpers de fixture
# ---------------------------------------------------------------------------


def _make_story(tmp_path: Path, story_id: str, status: str) -> Path:
    """Crée un fichier de récit minimal avec frontmatter YAML."""
    stories_dir = tmp_path / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    f = stories_dir / f"{story_id}.md"
    f.write_text(
        f"---\nid: {story_id}\nstatus: {status}\n---\n\n# Titre du récit\n",
        encoding="utf-8",
    )
    return f


def _make_backlog(tmp_path: Path, content: str) -> Path:
    """Crée sprint_backlog.md avec le contenu fourni."""
    bl_dir = tmp_path / "backlog"
    bl_dir.mkdir(parents=True, exist_ok=True)
    bl = bl_dir / "sprint_backlog.md"
    bl.write_text(content, encoding="utf-8")
    return bl


def _read_status(story_file: Path) -> str | None:
    """Extrait le champ status: du frontmatter YAML."""
    text = story_file.read_text(encoding="utf-8")
    m = re.search(r"(?m)^status:\s*(.+)$", text)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# 1. Nominal colonne-aware : titre contient READY_FOR_DEV, Statut = DRAFT
# ---------------------------------------------------------------------------


def test_column_aware_title_does_not_pollute_status(tmp_path):
    """
    Le titre de la ligne contient 'READY_FOR_DEV' mais la colonne Statut vaut 'DRAFT'.
    Avec l'ancien regex (scan toute la ligne), le statut lu était READY_FOR_DEV.
    Avec le fix colonne-aware, le frontmatter doit recevoir DRAFT.
    """
    story = _make_story(tmp_path, "TEST-001", "IN_ANALYZE")
    _make_backlog(
        tmp_path,
        "## EPIC-99\n\n"
        "| État | Récit | Clé Jira | Titre | Statut | Responsable |\n"
        "| :---: | :--- | :---: | :--- | :--- | :--- |\n"
        "| [ ] | **TEST-001** | - | Fix READY_FOR_DEV handling | `DRAFT` | ⚪ À faire |\n",
    )

    sync_sprint_backlog("Test", tmp_path)

    assert _read_status(story) == "DRAFT", (
        "Le statut doit être DRAFT (colonne Statut), pas READY_FOR_DEV (titre)."
    )


# ---------------------------------------------------------------------------
# 2. Nominal vocab : DONE_TESTED non tronqué en DONE
# ---------------------------------------------------------------------------


def test_done_tested_not_truncated(tmp_path):
    """DONE_TESTED dans la colonne Statut ne doit pas être tronqué en DONE."""
    story = _make_story(tmp_path, "TEST-002", "IN_DEV")
    _make_backlog(
        tmp_path,
        "## EPIC-99\n\n"
        "| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |\n"
        "| :---: | :--- | :---: | :--- | :--- | :--- | :--- |\n"
        "| [x] | **TEST-002** | - | Core | Récit pilote | `DONE_TESTED` | ✅ Clôturé |\n",
    )

    sync_sprint_backlog("Test", tmp_path)

    assert _read_status(story) == "DONE_TESTED"


# ---------------------------------------------------------------------------
# 3. Nominal paramétré : TOMBSTONE / READY_FOR_DEV / DONE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("statut_value", ["TOMBSTONE", "READY_FOR_DEV", "DONE"])
def test_standard_statuses_aligned(tmp_path, statut_value):
    """Chaque statut du vocabulaire étendu est correctement aligné dans le frontmatter."""
    story = _make_story(tmp_path, "TEST-003", "OPEN")
    _make_backlog(
        tmp_path,
        "## EPIC-99\n\n"
        "| État | Récit | Épopée | Composant | Titre | Statut | Décision |\n"
        "| :---: | :--- | :--- | :---: | :--- | :--- | :--- |\n"
        f"| [-] | **TEST-003** | EPIC-5 | Memory | Titre neutre | `{statut_value}` | Raison |\n",
    )

    sync_sprint_backlog("Test", tmp_path)

    assert _read_status(story) == statut_value


# ---------------------------------------------------------------------------
# 4. Exception : en-tête sans colonne Statut → zéro écriture, pas de crash
# ---------------------------------------------------------------------------


def test_no_statut_column_skips_block(tmp_path):
    """
    Si l'en-tête ne contient pas de colonne 'Statut', le bloc entier est ignoré.
    Zéro écriture sur le fichier de récit. Pas de crash.
    """
    story = _make_story(tmp_path, "TEST-004", "OPEN")
    original_status = _read_status(story)

    _make_backlog(
        tmp_path,
        "## EPIC-99\n\n"
        "| État | Récit | Titre | Responsable |\n"
        "| :---: | :--- | :--- | :--- |\n"
        "| [ ] | **TEST-004** | Titre | Quelqu'un |\n",
    )

    sync_sprint_backlog("Test", tmp_path)

    # Le status ne doit pas avoir changé
    assert _read_status(story) == original_status


# ---------------------------------------------------------------------------
# 5. Exception : ligne de données sans ID → ignorée, pas de crash
# ---------------------------------------------------------------------------


def test_line_without_id_is_ignored(tmp_path):
    """Une ligne de données sans token ID (XXX-YYY) est ignorée proprement."""
    story = _make_story(tmp_path, "TEST-005", "OPEN")

    _make_backlog(
        tmp_path,
        "## EPIC-99\n\n"
        "| État | Récit | Titre | Statut |\n"
        "| :---: | :--- | :--- | :--- |\n"
        # Ligne sans ID valide (aucun token A-Z0-9 avec tiret)
        "| [ ] | pas-un-id | Titre | DONE |\n"
        # Ligne avec ID valide
        "| [ ] | **TEST-005** | Titre | DRAFT |\n",
    )

    sync_sprint_backlog("Test", tmp_path)

    # TEST-005 doit être aligné sur DRAFT ; pas de crash sur la ligne sans ID
    assert _read_status(story) == "DRAFT"


# ---------------------------------------------------------------------------
# 6. Résilience : sprint_backlog.md absent → retour silencieux
# ---------------------------------------------------------------------------


def test_missing_backlog_file_returns_silently(tmp_path):
    """Si sprint_backlog.md n'existe pas, sync_sprint_backlog retourne sans lever."""
    story = _make_story(tmp_path, "TEST-006", "OPEN")
    # Ne pas créer backlog/sprint_backlog.md

    # Ne doit pas lever d'exception
    result = sync_sprint_backlog("Test", tmp_path)

    assert result is None
    assert _read_status(story) == "OPEN"  # Frontmatter inchangé


# ---------------------------------------------------------------------------
# 7. Persistance : frontmatter déjà aligné → zéro écriture (mtime stable)
# ---------------------------------------------------------------------------


def test_already_aligned_story_not_rewritten(tmp_path):
    """
    Si le frontmatter du récit est déjà égal au statut du backlog,
    sync_sprint_backlog ne doit pas réécrire le fichier.
    On vérifie via le mtime (le fichier ne doit pas être touché).
    """
    story = _make_story(tmp_path, "TEST-007", "DONE_TESTED")
    _make_backlog(
        tmp_path,
        "## EPIC-99\n\n"
        "| État | Récit | Composant | Titre | Statut | Responsable |\n"
        "| :---: | :--- | :--- | :--- | :--- | :--- |\n"
        "| [x] | **TEST-007** | Core | Titre | `DONE_TESTED` | ✅ |\n",
    )

    mtime_before = story.stat().st_mtime
    sync_sprint_backlog("Test", tmp_path)
    mtime_after = story.stat().st_mtime

    assert mtime_before == mtime_after, "Le fichier ne doit pas être réécrit si déjà aligné."


# ---------------------------------------------------------------------------
# 8. Table 8 colonnes Grill-me|Statut : Grill-me=PENDING, Statut=DRAFT
# ---------------------------------------------------------------------------


def test_8col_grill_me_not_extracted_as_status(tmp_path):
    """
    Tableau à 8 colonnes : Grill-me | Statut.
    La colonne Grill-me vaut PENDING (valeur valide pour cette colonne uniquement).
    La colonne Statut vaut DRAFT.
    Le frontmatter doit recevoir DRAFT, jamais PENDING.
    """
    story = _make_story(tmp_path, "TEST-008", "IN_ANALYZE")
    _make_backlog(
        tmp_path,
        "## EPIC-21\n\n"
        "| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |\n"
        "| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |\n"
        "| [ ] | **TEST-008** | - | Bridges | Titre neutre | `PENDING` | ⚪ `DRAFT` | ⚪ |\n",
    )

    sync_sprint_backlog("Test", tmp_path)

    assert _read_status(story) == "DRAFT", (
        "Le statut doit être DRAFT (colonne Statut), jamais PENDING (colonne Grill-me)."
    )
