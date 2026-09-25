# -*- coding: utf-8 -*-
"""
Rejeu déterministe de l'incident du 24/09/2026 (MLOOP-270-BE / ADR-011, CA-3).

Incident : promotion sauvage d'un récit en `READY_FOR_DEV` par édition brute de
la ligne `status:` du frontmatter, sans feu vert humain ni entrée au journal.

Rejeu couvert :
  1. promotion brute → `scan_transitions()` détecte `approval_missing` ;
  2. rétrogradation sanctionnée journalisée (`origin: sanction`) si
     `apply_sanctions=True` (légal ici : sanction hors FSM explicite) ;
  3. le récit n'est JAMAIS supprimé (Failure Contract, zéro purge) ;
  4. divergence journal ↔ ligne d'état (`state_mismatch`) détectée en lecture
     seule ;
  5. transition hors table ré-émise ⇒ `StateTransitionError` sans écriture.

Toutes les fixtures sont locales à `tmp_path` (CA-7).
"""

from __future__ import annotations

import pytest
from pathlib import Path

from src.core.transition_journal import append_entry, build_entry, read_entries
from src.pipelines import _story_lock_io as lock_io
from src.pipelines.state_machine import StateTransitionError
from src.pipelines.story_status_lock import SANCTION_REASON, scan_transitions, set_story_status


def _make_story(project: Path, story_id: str = "T1", status: str = "IN_REVIEW") -> Path:
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
        "## En tant que test\n\nJe veux empêcher les promotions sauvages.\n\n"
        "## Scénarios de test\n\n- scénario unique\n",
        encoding="utf-8",
    )
    return path


def _raw_promote(story: Path, target: str = "READY_FOR_DEV") -> None:
    """Rejoue l'incident : édition brute de la ligne `status:` (sans journal)."""
    original = story.read_text(encoding="utf-8")
    story.write_text(lock_io.write_field(original, "status", target), encoding="utf-8")
    assert story.exists()


class TestRejeuPromotionSauvage:
    """CA-3 : détection → sanction journalisée → récit intact."""

    def test_detection_et_sanction_complete(self, tmp_path: Path):
        story = _make_story(tmp_path, status="IN_REVIEW")
        _raw_promote(story)

        report = scan_transitions(tmp_path, apply_sanctions=True)
        assert [i["kind"] for i in report["issues"]] == ["approval_missing"]
        assert report["downgraded"] == ["T1"]
        assert report["backfilled"] is False

        # Rétrogradation appliquée : le récit existe toujours (jamais supprimé).
        assert story.exists()
        assert "status: READY_FOR_GROOMING" in story.read_text(encoding="utf-8")

        # La sanction est journalisée avec son motif — jamais un silence.
        sanctions = [e for e in read_entries(tmp_path) if e["origin"] == "sanction"]
        assert len(sanctions) == 1
        assert sanctions[0]["from_status"] == "READY_FOR_DEV"
        assert sanctions[0]["to_status"] == "READY_FOR_GROOMING"
        assert sanctions[0]["reason"] == SANCTION_REASON
        assert sanctions[0]["actor"] == "scan_transitions"

    @pytest.mark.parametrize(
        ("apply_sanctions", "expected_suffix"),
        [(False, "[sanction_pending]"), (True, "[sanction_applied]")],
    )
    def test_mode_lecture_seule_vs_sanction(
        self, tmp_path: Path, apply_sanctions: bool, expected_suffix: str
    ):
        story = _make_story(tmp_path, status="IN_REVIEW")
        _raw_promote(story)

        report = scan_transitions(tmp_path, apply_sanctions=apply_sanctions)
        detail = report["issues"][0]["detail"]
        assert expected_suffix in detail

        if apply_sanctions:
            assert "status: READY_FOR_GROOMING" in story.read_text(encoding="utf-8")
            assert report["downgraded"] == ["T1"]
        else:
            # Aucun contrôle ne modifie backlog/ en mode lecture seule.
            assert "status: READY_FOR_DEV" in story.read_text(encoding="utf-8")
            assert report["downgraded"] == []

    def test_scan_idempotent_apres_sanction(self, tmp_path: Path):
        story = _make_story(tmp_path, status="IN_REVIEW")
        _raw_promote(story)
        scan_transitions(tmp_path, apply_sanctions=True)
        second = scan_transitions(tmp_path, apply_sanctions=True)
        assert second["downgraded"] == []  # déjà rétrogradé, aucune seconde sanction
        assert story.exists()

    def test_divergence_journal_detectee_sans_modification(self, tmp_path: Path):
        """Édition brute après une transition journalisée : mismatch signalé, récit intact."""
        story = _make_story(tmp_path, status="IN_REVIEW")
        append_entry(
            tmp_path,
            build_entry("T1", "OPEN", "IN_REVIEW", "Marco", "focus", "api"),
        )
        _raw_promote(story, target="ON_HOLD")

        report = scan_transitions(tmp_path, apply_sanctions=True)
        assert [i["kind"] for i in report["issues"]] == ["state_mismatch"]
        assert report["issues"][0]["severity"] == "BLOCKING"
        assert report["downgraded"] == []  # la sanction ne couvre que approval_missing
        assert "status: ON_HOLD" in story.read_text(encoding="utf-8")


class TestRemissionTransitionHorsTable:
    """Failure Contract : la ré-émision d'une transition illégale échoue net."""

    @pytest.mark.parametrize(
        ("start", "target"),
        [
            ("READY_FOR_DEV", "READY_FOR_GROOMING"),  # OQ-270-1 : hors table
            ("IN_REVIEW", "SHIPPED"),  # livraison sans passer par le dev
        ],
    )
    def test_transition_illegale_levee_sans_ecriture(self, tmp_path: Path, start: str, target: str):
        story = _make_story(tmp_path, status=start)
        before = story.read_bytes()
        with pytest.raises(StateTransitionError):
            set_story_status(tmp_path, "T1", target, "Marco", "incident-replay")
        assert story.read_bytes() == before
        assert read_entries(tmp_path) == []
