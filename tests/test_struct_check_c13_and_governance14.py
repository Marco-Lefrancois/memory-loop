# -*- coding: utf-8 -*-
"""
Tests du contrôle C13 (struct-check) et du contrôle 25 de gouvernance
(MLOOP-270-BE / ADR-011).

Couverture :
  - C13 par récit : `READY_FOR_DEV` sans approbation ⇒ BLOCKING toujours ;
    divergence journal ↔ ligne d'état et récit engagé non journalisé ⇒
    graduation WARNING (legacy) / BLOCKING (`strict=True`) ;
  - Contrôle 25 projet-wide : PASS legacy (non rétro-équipé) vs FAIL
    (rétro-équipé avec écart BLOCKING) — graduation `WARNING → BLOCKING` ;
  - CA-4 : revendication `control_claim` sans artefact disque ⇒ « non
    corroborée » FAIL.

Toutes les fixtures sont locales à `tmp_path` (CA-7).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.transition_journal import (
    append_control_claim,
    append_entry,
    build_entry,
)
from src.pipelines import _story_lock_io as lock_io
from src.pipelines._struct_c13 import CONTROL_NAME, summarize_project_state_lock
from src.pipelines.struct_checker import StructCheckEngine, StructViolation
from src.pipelines.vibe_check._vc_governance import check_25_story_state_lock


def _make_story(project: Path, story_id: str, status: str, **extra) -> Path:
    stories = project / "backlog" / "stories"
    stories.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "id": story_id,
        "jira_key": story_id,
        "epic_key": "EPIC-TEST",
        "type": "user_story",
        "title": f"Récit {story_id}",
        "layer": "backend",
        "status": status,
    }
    frontmatter.update(extra)
    fm = "".join(f"{key}: {value}\n" for key, value in frontmatter.items())
    path = stories / f"{story_id}.md"
    path.write_text(
        f"---\n{fm}---\n\n"
        f"# Récit {story_id}\n\n"
        "## En tant que test\n\nJe veux auditer l'état de ce récit.\n\n"
        "## Scénarios de test\n\n- scénario unique\n",
        encoding="utf-8",
    )
    return path


def _approve(project: Path, story_id: str, approver: str = "Marco") -> None:
    """Appose les stamps d'approbation directement (fixture, pas le système sous test)."""
    story = lock_io.resolve_story_file(project, story_id)
    text = story.read_text(encoding="utf-8")
    text = lock_io.write_field(text, "validated_by", approver)
    text = lock_io.write_field(text, "validated_at", "2026-09-25T00:00:00+00:00")
    story.write_text(text, encoding="utf-8")


def _raw_set_status(project: Path, story_id: str, status: str) -> None:
    story = lock_io.resolve_story_file(project, story_id)
    text = story.read_text(encoding="utf-8")
    story.write_text(lock_io.write_field(text, "status", status), encoding="utf-8")


def _c13(project: Path, story_id: str, strict: bool = False) -> list[StructViolation]:
    engine = StructCheckEngine(project)
    report = engine.check_file(project / "backlog" / "stories" / f"{story_id}.md", strict=strict)
    return [v for v in report.violations if v.check_id == "C13"]


class TestStructCheckC13:
    """Règles (a)-(d) appliquées fichier par fichier."""

    @pytest.mark.parametrize("strict", [False, True])
    def test_ready_for_dev_sans_approbation_toujours_blocking(self, tmp_path: Path, strict: bool):
        _make_story(tmp_path, "T1", "READY_FOR_DEV")
        violations = _c13(tmp_path, "T1", strict=strict)
        # (a) approval_missing en tête, puis (c) récit engagé non journalisé.
        assert len(violations) == 2
        assert violations[0].severity == "BLOCKING"
        assert "approbation humaine" in violations[0].message
        assert violations[1].severity == ("BLOCKING" if strict else "WARNING")

    @pytest.mark.parametrize(
        ("strict", "expected"),
        [(False, "WARNING"), (True, "BLOCKING")],
    )
    def test_divergence_journal_graduee_strict(self, tmp_path: Path, strict: bool, expected: str):
        """Entrée journal présente mais ligne d'état éditée brutalement."""
        _make_story(tmp_path, "T1", "IN_REVIEW")
        append_entry(tmp_path, build_entry("T1", "OPEN", "IN_REVIEW", "Marco", "focus", "api"))
        _raw_set_status(tmp_path, "T1", "ON_HOLD")

        violations = _c13(tmp_path, "T1", strict=strict)
        assert len(violations) == 1
        assert violations[0].severity == expected
        assert "diverge du journal" in violations[0].message

    @pytest.mark.parametrize(
        ("strict", "expected"),
        [(False, "WARNING"), (True, "BLOCKING")],
    )
    def test_recit_engage_sans_journal_gradue(self, tmp_path: Path, strict: bool, expected: str):
        _make_story(tmp_path, "T1", "READY_FOR_GROOMING")
        violations = _c13(tmp_path, "T1", strict=strict)
        assert len(violations) == 1
        assert violations[0].severity == expected
        assert "sans aucune entrée au journal" in violations[0].message

    @pytest.mark.parametrize("status", ["IN_REVIEW", "IN_ANALYZE", "DRAFT"])
    def test_recit_non_engage_sans_journal_conforme(self, tmp_path: Path, status: str):
        """Règle (d) : hors `GATED_STATUSES`, l'absence de journal n'est pas un écart."""
        _make_story(tmp_path, "T1", status)
        assert _c13(tmp_path, "T1") == []

    @pytest.mark.parametrize("status", ["SHIPPED", "DONE_TESTED", "ACCEPTED"])
    def test_recit_terminal_exempte(self, tmp_path: Path, status: str):
        _make_story(tmp_path, "T1", status)
        assert _c13(tmp_path, "T1", strict=True) == []

    def test_recit_conforme_sans_violation(self, tmp_path: Path):
        """Stamps présents + journal aligné : zéro écart C13 même en strict."""
        _make_story(tmp_path, "T1", "READY_FOR_DEV")
        _approve(tmp_path, "T1")
        append_entry(
            tmp_path,
            build_entry("T1", "IN_REVIEW", "READY_FOR_DEV", "Marco", "story-approve", "api"),
        )
        assert _c13(tmp_path, "T1", strict=True) == []


class TestGouvernanceCheck25:
    """Contrôle projet-wide : graduation legacy, FAIL post-backfill, CA-4."""

    @pytest.mark.parametrize("message_fragment", ["WARNING", "non rétro-équipé"])
    def test_legacy_non_backfilled_passe_en_warning(self, tmp_path: Path, message_fragment: str):
        """Avant backfill : PASS avec avertissement — jamais de FAIL bloquant."""
        _make_story(tmp_path, "T1", "READY_FOR_GROOMING")  # engagé, non journalisé
        result = summarize_project_state_lock(tmp_path)
        assert result["status"] == "PASS"
        assert message_fragment in result["check"]

    def test_backfilled_avec_ecart_blocking_fais_fail(self, tmp_path: Path):
        """Après backfill : tout écart BLOCKING fait basculer le contrôle en FAIL."""
        _make_story(tmp_path, "T1", "READY_FOR_GROOMING")
        append_entry(
            tmp_path,
            build_entry("T1", "", "READY_FOR_GROOMING", "Marco", "story-backfill", "backfill"),
        )
        _raw_set_status(tmp_path, "T1", "READY_FOR_DEV")  # promotion brute sans stamps

        result = summarize_project_state_lock(tmp_path)
        assert result["status"] == "FAIL"
        assert "BLOCKING" in result["check"]
        assert "T1" in result["check"]

    def test_backfilled_propre_passe(self, tmp_path: Path):
        _make_story(tmp_path, "T1", "READY_FOR_DEV")
        _approve(tmp_path, "T1")
        # Ordre chronologique réel : le backfill sème AVANT les transitions suivantes.
        append_entry(
            tmp_path,
            build_entry("T1", "", "IN_REVIEW", "Marco", "story-backfill", "backfill"),
        )
        append_entry(
            tmp_path,
            build_entry("T1", "IN_REVIEW", "READY_FOR_DEV", "Marco", "story-approve", "api"),
        )
        result = summarize_project_state_lock(tmp_path)
        assert result["status"] == "PASS"
        assert "0 écart(s)" in result["check"]

    def test_ca4_revendication_sans_artefact_fais_fail(self, tmp_path: Path):
        """CA-4 : un claim sans fichier réel sur disque est « non corroboré »."""
        append_control_claim(
            tmp_path, CONTROL_NAME, "memory/rapport_inexistant.json", "attacker", "manual"
        )
        result = summarize_project_state_lock(tmp_path)
        assert result["status"] == "FAIL"
        assert "corroborée" in result["check"]
        assert "rapport_inexistant" in result["check"]

    def test_ca4_revendication_avec_artefact_reel_passe(self, tmp_path: Path):
        append_entry(
            tmp_path,
            build_entry("T1", "", "IN_REVIEW", "Marco", "story-backfill", "backfill"),
        )
        append_control_claim(
            tmp_path, CONTROL_NAME, "memory/story_transitions.jsonl", "Marco", "story-backfill"
        )
        result = summarize_project_state_lock(tmp_path)
        assert result["status"] == "PASS"

    def test_wrapper_vibe_check_delegue(self, tmp_path: Path):
        _make_story(tmp_path, "T1", "IN_REVIEW")
        result = check_25_story_state_lock(tmp_path, "tmp", "INIT", "STAGE_INIT")
        assert set(result) == {"check", "status"}
        assert result["status"] in {"PASS", "FAIL"}
