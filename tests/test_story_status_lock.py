# -*- coding: utf-8 -*-
"""
Tests du verrou anti-promotion (MLOOP-270-BE / ADR-011).

Piliers couverts :
  - Pilier 1 (Nominal) : approbation + transition atomiques, journal complet ;
  - Pilier 2 (Exceptions) : promotions sans approbation, approbateurs machines,
    cibles hors FSM, transition hors table — tous refusés sans écriture ;
  - Pilier 3 (Résilience) : contention de verrou avec timeout borné et
    rollback récit sur échec du journal (contrat tout-ou-rien) ;
  - Façade `set_story_status` : réutilise strictement la FSM existante.

Toutes les fixtures sont locales à `tmp_path` (CA-7) — jamais `Projects/mLoop`.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from src.core.transition_journal import read_entries
from src.pipelines import _story_lock_io as lock_io
from src.pipelines.state_machine import StateTransitionError
from src.pipelines.story_status_lock import (
    apply_human_approval,
    set_story_status,
)
from src.utils.file_lock import FileLockTimeoutError, InterProcessFileLock


def _make_story(project: Path, story_id: str = "T1", status: str = "IN_REVIEW") -> Path:
    """Récit minimal conforme (frontmatter complet + H1 métier)."""
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
        "## En tant que test\n\nJe veux verrouiller les transitions.\n\n"
        "## Scénarios de test\n\n- scénario unique\n",
        encoding="utf-8",
    )
    return path


def _status_of(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return ""


class TestNominal:
    """Pilier 1 : la séquence approbation → transition est atomique et tracée."""

    def test_approbation_puis_transition(self, tmp_path: Path):
        story = _make_story(tmp_path)
        approval = apply_human_approval(tmp_path, "T1", "Marco")
        assert approval["validated_by"] == "Marco"
        assert approval["validated_at"]

        result = set_story_status(tmp_path, "T1", "READY_FOR_DEV", "Marco", "story-approve")
        assert result == {
            "changed": True,
            "story_id": "T1",
            "from": "IN_REVIEW",
            "to": "READY_FOR_DEV",
        }
        assert _status_of(story) == "READY_FOR_DEV"
        assert "validated_by: Marco" in story.read_text(encoding="utf-8")

        entries = read_entries(tmp_path)
        assert [e["kind"] for e in entries] == ["approval", "transition"]
        transition = entries[1]
        assert transition["origin"] == "api"
        assert transition["actor"] == "Marco"
        assert transition["source_cmd"] == "story-approve"
        assert transition["from_status"] == "IN_REVIEW"
        assert transition["to_status"] == "READY_FOR_DEV"
        assert transition["ts"]

    def test_transition_idempotente(self, tmp_path: Path):
        _make_story(tmp_path)
        apply_human_approval(tmp_path, "T1", "Marco")
        set_story_status(tmp_path, "T1", "READY_FOR_DEV", "Marco", "story-approve")
        again = set_story_status(tmp_path, "T1", "READY_FOR_DEV", "Marco", "story-approve")
        assert again["changed"] is False
        assert len(read_entries(tmp_path)) == 2  # aucune entrée en double


class TestExceptions:
    """Pilier 2 : tout refus est net et n'écrit JAMAIS (zéro entrée, zéro champ)."""

    def test_promotion_sans_approbation_refusee(self, tmp_path: Path):
        _make_story(tmp_path, status="IN_REVIEW")
        with pytest.raises(StateTransitionError):
            set_story_status(tmp_path, "T1", "READY_FOR_DEV", "Marco", "test-cmd")
        assert read_entries(tmp_path) == []  # aucune entrée journal

    def test_statut_cible_inconnu_refuse(self, tmp_path: Path):
        _make_story(tmp_path, status="IN_REVIEW")
        with pytest.raises(StateTransitionError, match="Statut cible inconnu"):
            set_story_status(tmp_path, "T1", "TOTALLY_UNKNOWN", "Marco", "test-cmd")
        assert read_entries(tmp_path) == []

    def test_transition_hors_table_fsm_refusee(self, tmp_path: Path):
        """READY_FOR_DEV → READY_FOR_GROOMING est hors `ALLOWED_TRANSITIONS` (OQ-270-1)."""
        story = _make_story(tmp_path, status="READY_FOR_DEV")
        apply_human_approval(tmp_path, "T1", "Marco")
        assert "validated_by: Marco" in story.read_text(encoding="utf-8")

        with pytest.raises(StateTransitionError):
            set_story_status(tmp_path, "T1", "READY_FOR_GROOMING", "Marco", "test-cmd")
        assert _status_of(story) == "READY_FOR_DEV"  # inchangé
        entries = read_entries(tmp_path)
        assert [e["kind"] for e in entries] == ["approval"]  # aucun journal de transition

    @pytest.mark.parametrize("approver", ["agent", "bot", "sentinel", "", None])
    def test_approbateur_machine_ou_vide_refuse(self, tmp_path: Path, approver):
        story = _make_story(tmp_path)
        before = story.read_bytes()
        with pytest.raises(ValueError):
            apply_human_approval(tmp_path, "T1", approver)
        assert story.read_bytes() == before
        assert read_entries(tmp_path) == []

    def test_approbation_sur_recit_terminal_refusee(self, tmp_path: Path):
        story = _make_story(tmp_path, status="SHIPPED")
        before = story.read_bytes()
        with pytest.raises(StateTransitionError):
            apply_human_approval(tmp_path, "T1", "Marco")
        assert story.read_bytes() == before

    def test_verrou_contention_timeout_borne_sans_ecriture(self, tmp_path: Path):
        story = _make_story(tmp_path)
        before = story.read_bytes()
        lock = InterProcessFileLock(lock_io.lock_path(tmp_path), timeout=1.0)
        with lock:
            with pytest.raises(FileLockTimeoutError):
                set_story_status(tmp_path, "T1", "READY_FOR_DEV", "Marco", "test", timeout_s=0.2)
        assert story.read_bytes() == before
        assert read_entries(tmp_path) == []


class TestResilience:
    """Pilier 3 : le journal qui échoue annule l'écriture du récit (rollback)."""

    def test_echec_journal_annule_la_transition(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        story = _make_story(tmp_path)
        apply_human_approval(tmp_path, "T1", "Marco")
        before = story.read_bytes()
        entry_count = len(read_entries(tmp_path))

        def _boom(project, entry):
            raise OSError("journal indisponible")

        monkeypatch.setattr(lock_io, "append_entry", _boom)
        with pytest.raises(OSError):
            set_story_status(tmp_path, "T1", "READY_FOR_DEV", "Marco", "story-approve")

        assert story.read_bytes() == before  # rollback : statut intact
        assert len(read_entries(tmp_path)) == entry_count

    def test_echec_journal_annule_l_approbation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        story = _make_story(tmp_path)
        before = story.read_bytes()

        def _boom(project, entry):
            raise OSError("journal indisponible")

        monkeypatch.setattr(lock_io, "append_entry", _boom)
        with pytest.raises(OSError):
            apply_human_approval(tmp_path, "T1", "Marco")

        assert story.read_bytes() == before  # stamps jamais seuls sans journal
        assert read_entries(tmp_path) == []
