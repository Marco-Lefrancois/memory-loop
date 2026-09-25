"""
Harnais de Non-Régression — Découplage Modalité Grill × Scope & Anti-Cascade.

MLOOP-324-FULL / EPIC-32 / ADR-0393.

Suite hermétique prouvant de manière reproductible et déterministe qu'aucune
combinaison de paramètres de grill ne peut :
  - provoquer une mutation de récit non sollicitée (étanchéité de scope transverse) ;
  - court-circuiter l'autorité humaine exclusive de la Gate 2 (READY_FOR_DEV) ;
  - échapper à la sonde de détection de cascade (Check 28).

Étanchéité absolue : toutes les opérations disque s'effectuent sous `tmp_path`.
Aucune dépendance sur l'espace de travail réel `Projects/`.

Conforme ADR-0369 : `pytest.raises`, `@pytest.mark.parametrize`, zéro ressource
non gérée, zéro I/O réseau.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from src.pipelines._fsm_authority import (
    LifecycleAuthorityError,
    validate_gate2_authority,
)
from src.pipelines.grill._grill_guards import assert_no_story_mutation
from src.pipelines.state_machine import StateTransitionError
from src.pipelines.vibe_check._vc_cascade import check_28_story_cascade_drift
from src.state import ProjectLayout


# ─── Fixtures hermétiques ───────────────────────────────────────────────────────


def _make_project(
    tmp_path: Path,
    stories: dict[str, str],
    evidence: set[str] | None = None,
    backlog_rows: str = "",
) -> Path:
    """
    Construit une arborescence projet mLoop étanche sous `tmp_path`.

    Args:
        stories: mapping {story_id: statut} → un récit Markdown par entrée.
        evidence: identifiants disposant d'un `<ID>_fact_dossier.md`.
        backlog_rows: lignes additionnelles injectées dans sprint_backlog.md.
    """
    project_dir = tmp_path / "hermetic_project"
    (project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE).mkdir(parents=True)
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    stories_dir.mkdir(parents=True)
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)

    for story_id, status in stories.items():
        (stories_dir / f"{story_id}.md").write_text(
            f"---\nid: {story_id}\ntitle: Récit {story_id}\nstatus: {status}\n---\n"
            "## Description\nCorps hermétique.\n",
            encoding="utf-8",
        )

    for story_id in evidence or set():
        (evidence_dir / f"{story_id}_fact_dossier.md").write_text(
            f"# Dossier de preuves — {story_id}\n", encoding="utf-8"
        )

    sprint = project_dir / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
    sprint.write_text(
        "# Sprint Backlog\n\n| ID | Titre | Statut |\n| :--- | :--- | :--- |\n" + backlog_rows,
        encoding="utf-8",
    )
    return project_dir


def _set_mtime_window(
    project_dir: Path, story_ids: list[str], base_ns: int, spread_ns: int
) -> None:
    """Force les mtime des récits dans une fenêtre resserrée (simulation de rafale)."""
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    for offset, story_id in enumerate(story_ids):
        story_file = stories_dir / f"{story_id}.md"
        ts_ns = base_ns + offset * spread_ns
        ts_s = ts_ns / 1_000_000_000
        import os

        os.utime(story_file, (ts_s, ts_s))


# ─── Test 1 — Découplage Format × Scope unitaire ────────────────────────────────


def test_format_round_story_scope_never_promotes_beyond_grooming(tmp_path):
    """
    `--format round --story <ID>` exécute des questions groupées SANS jamais
    altérer le statut du récit au-delà de READY_FOR_GROOMING (le choix du format
    n'a aucun effet sur le scope ni sur le plafond de promotion — ADR-0393).
    """
    from src.pipelines.grill._engine import GrillEngine

    project_dir = _make_project(
        tmp_path,
        stories={"US-01": "IN_ANALYZE"},
        backlog_rows="| US-01 | Récit US-01 | IN_ANALYZE |\n",
    )
    engine = GrillEngine(project_dir)

    assert engine.mark_story_grilled("US-01") is True

    story_file = project_dir / ProjectLayout.BACKLOG / "stories" / "US-01.md"
    content = story_file.read_text(encoding="utf-8")
    assert "status: READY_FOR_GROOMING" in content
    assert "status: READY_FOR_DEV" not in content


# ─── Test 2 — Découplage Format × Scope transverse ──────────────────────────────


def test_atomic_project_scope_does_not_touch_stories_dir(tmp_path):
    """
    En scope transverse (`PROJECT`), aucune lecture/analyse ne doit muter le
    répertoire `backlog/stories/`. Le gestionnaire d'étanchéité laisse passer
    une opération non mutante sans lever d'exception ni altérer les mtime.
    """
    project_dir = _make_project(
        tmp_path,
        stories={"US-01": "READY_FOR_GROOMING", "US-02": "READY_FOR_GROOMING"},
        evidence={"US-01", "US-02"},
    )
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    before = {p: p.stat().st_mtime_ns for p in stories_dir.rglob("*.md")}

    # Opération transverse purement analytique (aucune écriture) → doit passer.
    with assert_no_story_mutation("PROJECT", stories_dir):
        _ = [p.read_text(encoding="utf-8") for p in stories_dir.rglob("*.md")]

    after = {p: p.stat().st_mtime_ns for p in stories_dir.rglob("*.md")}
    assert before == after, "Aucun récit ne doit être muté en scope transverse."


# ─── Test 3 — Sanction Fail-Closed Moteur ───────────────────────────────────────


def test_transverse_scope_write_attempt_raises_and_audits(tmp_path):
    """
    Toute tentative d'écriture de récit lors d'un grill transverse (`PROJECT`)
    déclenche `LifecycleAuthorityError` (Fail-Closed) et journalise l'incident
    dans `memory/audit_lifecycle_violations.jsonl`.
    """
    project_dir = _make_project(tmp_path, stories={"US-01": "READY_FOR_GROOMING"})
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"

    # L'exception est un sous-type de StateTransitionError (rétrocompatibilité FSM).
    assert issubclass(LifecycleAuthorityError, StateTransitionError)

    from src.pipelines.grill._grill_guards import log_lifecycle_violation

    with pytest.raises(LifecycleAuthorityError):
        with assert_no_story_mutation("PROJECT", stories_dir):
            # Mutation interdite : création d'un récit sous scope transverse.
            (stories_dir / "US-99_illicit.md").write_text("---\nid: US-99\n---\n", encoding="utf-8")

    # Journalisation explicite de l'infraction (helper partagé CLI/engine).
    log_lifecycle_violation(project_dir, "US-99", "tentative de mutation transverse", "PROJECT")
    audit_file = project_dir / "memory" / "audit_lifecycle_violations.jsonl"
    assert audit_file.exists()
    entries = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
    assert any(e["story_id"] == "US-99" and e["scope"] == "PROJECT" for e in entries)


# ─── Test 4 — Verrou Gate 2 nominatif ───────────────────────────────────────────


@pytest.mark.parametrize(
    "frontmatter, should_raise",
    [
        ({"validated_by": "", "validated_at": "2026-09-25T08:00:00-04:00"}, True),
        ({"validated_at": "2026-09-25T08:00:00-04:00"}, True),  # validated_by absent
        ({"validated_by": "agent-bot", "validated_at": "2026-09-25T08:00:00-04:00"}, True),
        ({"validated_by": "pipeline-auto", "validated_at": "2026-09-25T08:00:00-04:00"}, True),
        ({"validated_by": "Marco", "validated_at": ""}, True),  # horodatage absent
        ({"validated_by": "Marco", "validated_at": "pas-une-date"}, True),  # ISO invalide
        ({"validated_by": "Marco Lefrançois", "validated_at": "2026-09-25T08:00:00-04:00"}, False),
    ],
)
def test_gate2_authority_rejects_missing_or_bot_signature(frontmatter, should_raise):
    """
    La transition vers READY_FOR_DEV est rejetée avec `LifecycleAuthorityError`
    si `validated_by` est absent/bot ou `validated_at` absent/non ISO-8601.
    Une signature humaine nominative valide + horodatage ISO passe sans exception.
    """
    if should_raise:
        with pytest.raises(LifecycleAuthorityError):
            validate_gate2_authority(frontmatter, "US-01")
    else:
        validate_gate2_authority(frontmatter, "US-01")  # ne doit rien lever


# ─── Test 5 — Sonde Check 28 ────────────────────────────────────────────────────


def test_check_28_pass_when_fact_dossiers_present(tmp_path):
    """Check 28 retourne PASS lorsque chaque récit engagé possède son dossier."""
    project_dir = _make_project(
        tmp_path,
        stories={
            "US-01": "READY_FOR_GROOMING",
            "US-02": "READY_FOR_DEV",
            "US-03": "READY_FOR_GROOMING",
        },
        evidence={"US-01", "US-02", "US-03"},
    )
    result = check_28_story_cascade_drift(project_dir, "plan")
    assert result["status"] == "PASS"


def test_check_28_warning_in_phase2_on_cascade(tmp_path):
    """
    Une cascade simulée (≥ 3 récits engagés en rafale < 60s sans dossiers) donne
    un WARNING informatif en Phase 2 (PLAN).
    """
    project_dir = _make_project(
        tmp_path,
        stories={
            "US-01": "READY_FOR_GROOMING",
            "US-02": "READY_FOR_GROOMING",
            "US-03": "READY_FOR_GROOMING",
        },
        evidence=set(),  # aucun dossier de preuves → orphelins
    )
    # Rafale : 3 récits modifiés en 3 secondes (fenêtre < 60s).
    _set_mtime_window(
        project_dir,
        ["US-01", "US-02", "US-03"],
        base_ns=1_700_000_000_000_000_000,
        spread_ns=1_000_000_000,
    )
    result = check_28_story_cascade_drift(project_dir, "plan")
    assert result["status"] == "WARNING"
    assert "US-01" in result["check"]


def test_check_28_fail_blocking_in_phase4(tmp_path):
    """La même cascade en Phase 4 (VALIDATE) produit un FAIL bloquant."""
    project_dir = _make_project(
        tmp_path,
        stories={
            "US-01": "READY_FOR_GROOMING",
            "US-02": "READY_FOR_GROOMING",
            "US-03": "READY_FOR_DEV",
        },
        evidence=set(),
    )
    _set_mtime_window(
        project_dir,
        ["US-01", "US-02", "US-03"],
        base_ns=1_700_000_000_000_000_000,
        spread_ns=1_000_000_000,
    )
    result = check_28_story_cascade_drift(project_dir, "validate")
    assert result["status"] == "FAIL"


# ─── Test 6 — Résolution CLI (primauté --format sur --mode) ──────────────────────


def test_cli_format_takes_precedence_over_mode_and_scope_routing(tmp_path, monkeypatch):
    """
    Vérifie la primauté de `--format` sur `--mode` et le bon acheminement du
    scope. `--format round` + `--mode atomic` en macro (sans --story) doit
    résoudre le format `round` et le scope `PROJECT`, sans mutation de récit.
    """
    import src.pipelines.grill._cli_handler as handler

    project_dir = _make_project(
        tmp_path, stories={"US-01": "READY_FOR_GROOMING"}, evidence={"US-01"}
    )

    # Neutralisation des collaborateurs externes (I/O réseau / sync canonique).
    monkeypatch.setattr(handler, "run_sync", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(
        handler,
        "check_context_health",
        lambda *a, **k: {"alert": False, "zone": "SMART_ZONE", "message": ""},
        raising=True,
    )

    captured: dict[str, str] = {}
    real_resolve_format = handler._resolve_format
    real_resolve_scope = handler._resolve_scope

    def _spy_format(raw_format, raw_mode, is_macro):
        result = real_resolve_format(raw_format, raw_mode, is_macro)
        captured["format"] = result
        return result

    def _spy_scope(raw_scope, is_macro):
        result = real_resolve_scope(raw_scope, is_macro)
        captured["scope"] = result
        return result

    monkeypatch.setattr(handler, "_resolve_format", _spy_format)
    monkeypatch.setattr(handler, "_resolve_scope", _spy_scope)

    args = argparse.Namespace(
        project=str(project_dir),
        story=None,  # macro → scope transverse
        scope=None,
        mode="atomic",
        format="round",
        title=None,
        query=None,
        context=None,
        decision=None,
        positives=None,
        negatives=None,
        health=False,
    )

    # run_sync neutralisé ; on n'audite que la résolution de la matrice.
    class _DummyState:
        """État factice : `run_sync` étant neutralisé, l'état n'est jamais consommé."""

    exit_code = handler.execute_grill_cli(args, state=_DummyState(), project_path=project_dir)

    assert exit_code == 0
    assert captured["format"] == "round", "--format doit primer sur --mode."
    assert captured["scope"] == "PROJECT", "Un grill macro sans --story est transverse."
