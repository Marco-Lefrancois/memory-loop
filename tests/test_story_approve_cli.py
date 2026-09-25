# -*- coding: utf-8 -*-
"""
Tests des commandes CLI du verrou anti-promotion (MLOOP-270-BE / ADR-011).

Couverture (opérations 2 & 3 du plan) :
  - `story-approve` : nominal, approbateur machine refusé, approbateur vide
    refusé, récit introuvable — aucun refus n'écrit (CA-5) ;
  - `story-backfill` : **sans approbateur ⇒ 0 fichier touché** (CA-5),
    avec approbateur ⇒ récits actifs équipés (journal `origin: backfill` +
    stamps) et récits terminaux intacts (exemption `scratch_prune.py` L155).

Toutes les fixtures sont locales à `tmp_path` (CA-7).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.commands.handlers.story_approve import handle_story_approve
from src.commands.handlers.story_backfill import handle_story_backfill
from src.core.transition_journal import is_backfilled, read_entries


def _make_story(project: Path, story_id: str, status: str) -> Path:
    stories = project / "backlog" / "stories"
    stories.mkdir(parents=True, exist_ok=True)
    path = stories / f"{story_id}.md"
    path.write_text(
        "---\n"
        f"id: {story_id}\n"
        f"jira_key: {story_id}\n"
        "epic_key: EPIC-TEST\n"
        "type: user_story\n"
        f"title: Récit {story_id}\n"
        "layer: backend\n"
        f"status: {status}\n"
        "---\n\n"
        f"# Récit {story_id}\n\n"
        "## En tant que test\n\nJe veux approuver ce récit.\n\n"
        "## Scénarios de test\n\n- scénario unique\n",
        encoding="utf-8",
    )
    return path


def _tree_bytes(project: Path) -> dict:
    """Empreinte complète de l'arbre projet — la moindre écriture est détectée."""
    return {
        str(path.relative_to(project)): path.read_bytes()
        for path in sorted(project.rglob("*"))
        if path.is_file()
    }


class TestStoryApprove:
    """Opération 2 : seul écrivain de `validated_by` / `validated_at`."""

    def test_nominal_approbation_humaine(self, tmp_path: Path):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        args = SimpleNamespace(story="T1", approver="Marco")
        exit_code = handle_story_approve(args, None, tmp_path)

        assert exit_code == 0
        text = (tmp_path / "backlog/stories/T1.md").read_text(encoding="utf-8")
        assert "validated_by: Marco" in text
        assert "validated_at:" in text
        entries = read_entries(tmp_path)
        assert len(entries) == 1
        assert entries[0]["kind"] == "approval"
        assert entries[0]["actor"] == "Marco"

    def test_approbateur_machine_refuse_sans_ecriture(self, tmp_path: Path):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        before = _tree_bytes(tmp_path)
        args = SimpleNamespace(story="T1", approver="agent")
        exit_code = handle_story_approve(args, None, tmp_path)

        assert exit_code == 1
        assert _tree_bytes(tmp_path) == before  # zéro écriture
        assert read_entries(tmp_path) == []

    @pytest.mark.parametrize("approver", ["", None, "bot", "sentinel"])
    def test_approbateur_vide_ou_machine_refuse(self, tmp_path: Path, approver):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        before = _tree_bytes(tmp_path)
        args = SimpleNamespace(story="T1", approver=approver)
        exit_code = handle_story_approve(args, None, tmp_path)

        assert exit_code == 1
        assert _tree_bytes(tmp_path) == before
        assert read_entries(tmp_path) == []

    def test_recit_introuvable_refuse(self, tmp_path: Path):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        before = _tree_bytes(tmp_path)
        args = SimpleNamespace(story="T404", approver="Marco")
        exit_code = handle_story_approve(args, None, tmp_path)

        assert exit_code == 1
        assert _tree_bytes(tmp_path) == before


class TestStoryBackfill:
    """Opération 3 : CA-5 + exemption des statuts terminaux."""

    @pytest.mark.parametrize("approver", [None, "", "agent", "bot"])
    def test_sans_approbateur_zero_fichier_touche(self, tmp_path: Path, approver):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        _make_story(tmp_path, "T2", "SHIPPED")
        before = _tree_bytes(tmp_path)

        args = SimpleNamespace(approver=approver)
        exit_code = handle_story_backfill(args, None, tmp_path)

        assert exit_code == 1  # CA-5 : refus net
        assert _tree_bytes(tmp_path) == before  # 0 fichier touché, pas même le journal
        assert read_entries(tmp_path) == []
        assert is_backfilled(tmp_path) is False

    def test_approbateur_humain_equipe_les_actifs(self, tmp_path: Path):
        active = _make_story(tmp_path, "T1", "IN_REVIEW")
        gated = _make_story(tmp_path, "T2", "READY_FOR_DEV")
        args = SimpleNamespace(approver="Marco")
        exit_code = handle_story_backfill(args, None, tmp_path)

        assert exit_code == 0
        active_text = active.read_text(encoding="utf-8")
        assert "validated_by: Marco" in active_text
        assert "validated_at:" in active_text
        assert "validated_by: Marco" in gated.read_text(encoding="utf-8")

        entries = read_entries(tmp_path)
        assert {e["story_id"] for e in entries} == {"T1", "T2"}
        assert all(e["origin"] == "backfill" for e in entries)
        assert all(e["source_cmd"] == "story-backfill" for e in entries)
        assert is_backfilled(tmp_path) is True  # bascule WARNING → BLOCKING

    def test_recit_terminal_intact(self, tmp_path: Path):
        terminal = _make_story(tmp_path, "T2", "SHIPPED")
        before = terminal.read_bytes()
        exit_code = handle_story_backfill(SimpleNamespace(approver="Marco"), None, tmp_path)

        assert exit_code == 0
        assert terminal.read_bytes() == before  # exemption scratch_prune L155
        assert read_entries(tmp_path) == []  # aucune entrée pour un terminal

    def test_backfill_idempotent(self, tmp_path: Path):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        assert handle_story_backfill(SimpleNamespace(approver="Marco"), None, tmp_path) == 0
        first = _tree_bytes(tmp_path)

        assert handle_story_backfill(SimpleNamespace(approver="Marco"), None, tmp_path) == 0
        assert _tree_bytes(tmp_path) == first  # rien n'est réécrit ni doublonné
        assert len(read_entries(tmp_path)) == 1
