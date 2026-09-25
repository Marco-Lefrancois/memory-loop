# -*- coding: utf-8 -*-
"""
Tests du journal append-only des transitions (MLOOP-270-BE / ADR-011).

Piliers couverts :
  - Ordre chronologique strict et complétude du schéma d'entrée ;
  - Append-only : aucune réécriture ni suppression de ligne existante ;
  - Résilience de lecture (ligne corrompue écartée, jamais purgée) ;
  - Failure contract d'écriture : échec ⇒ exception propagée (ADR-0369).

Toutes les fixtures sont locales à `tmp_path` — aucun récit réel n'est touché (CA-7).
"""

from __future__ import annotations

import pytest
from pathlib import Path

from src.core.transition_journal import (
    ORIGINS,
    append_entry,
    build_entry,
    index_last_entries,
    is_backfilled,
    journal_path,
    last_entry_for,
    read_entries,
)


def _entry(story_id: str = "T1", origin: str = "api", **extra):
    """Entrée de test conforme au schéma."""
    return build_entry(
        story_id, "IN_REVIEW", "READY_FOR_DEV", "Marco", "story-approve", origin, **extra
    )


class TestBuildEntry:
    """Schéma d'entrée : champs complets et domaine contraint."""

    def test_schema_complet(self):
        entry = _entry()
        assert entry["story_id"] == "T1"
        assert entry["from_status"] == "IN_REVIEW"
        assert entry["to_status"] == "READY_FOR_DEV"
        assert entry["actor"] == "Marco"
        assert entry["source_cmd"] == "story-approve"
        assert entry["origin"] == "api"
        assert entry["kind"] == "transition"
        assert entry["ts"]  # horodatage ISO-8601 non vide

    @pytest.mark.parametrize("origin", list(ORIGINS))
    def test_origines_valides(self, origin: str):
        assert _entry(origin=origin)["origin"] == origin

    @pytest.mark.parametrize("origin", ["", "HACK", "manual_edit"])
    def test_origine_invalide_rejetee(self, origin: str):
        with pytest.raises(ValueError):
            _entry(origin=origin)

    @pytest.mark.parametrize("kind", ["transition", "approval", "control_claim"])
    def test_kinds_valides(self, kind: str):
        entry = build_entry("T1", "A", "B", "Marco", "cmd", "api", kind)
        assert entry["kind"] == kind

    def test_kind_invalide_rejete(self):
        with pytest.raises(ValueError):
            build_entry("T1", "A", "B", "Marco", "cmd", "api", "hack")


class TestAppendEntry:
    """Append-only strict + ordre chronologique + failure contract."""

    def test_ordre_chronologique_preserve(self, tmp_path: Path):
        for index in range(3):
            append_entry(tmp_path, _entry(story_id=f"T{index}"))
        entries = read_entries(tmp_path)
        assert [e["story_id"] for e in entries] == ["T0", "T1", "T2"]

    def test_append_only_aucune_reecriture(self, tmp_path: Path):
        append_entry(tmp_path, _entry(story_id="T0"))
        first_line = journal_path(tmp_path).read_text(encoding="utf-8").splitlines()[0]
        append_entry(tmp_path, _entry(story_id="T1"))
        lines = journal_path(tmp_path).read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        assert lines[0] == first_line  # la première ligne est bit-à-bit intacte

    def test_echec_ecriture_leve_l_exception(self, tmp_path: Path):
        """Pilier 4 : l'échec d'écriture n'est JAMAIS absorbé (ADR-0369 §5)."""
        journal_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
        journal_path(tmp_path).mkdir()  # le journal est un répertoire ⇒ ouverture impossible
        with pytest.raises(OSError):
            append_entry(tmp_path, _entry())

    def test_ligne_corrompue_ecartee_sans_purge(self, tmp_path: Path):
        append_entry(tmp_path, _entry(story_id="T0"))
        with open(journal_path(tmp_path), "a", encoding="utf-8") as handle:
            handle.write("{json-corrompu\n")
        append_entry(tmp_path, _entry(story_id="T1"))
        entries = read_entries(tmp_path)
        assert [e["story_id"] for e in entries] == ["T0", "T1"]
        # Résilience sans purge : la ligne corrompue est toujours sur disque.
        assert "{json-corrompu" in journal_path(tmp_path).read_text(encoding="utf-8")

    def test_lecture_resiliente_projet_sans_journal(self, tmp_path: Path):
        assert read_entries(tmp_path) == []
        assert last_entry_for(tmp_path, "T1") is None
        assert index_last_entries(tmp_path) == {}
        assert is_backfilled(tmp_path) is False


class TestConsultations:
    """Dernière entrée, index project-wide et bascule `is_backfilled`."""

    def test_last_entry_for_retourne_la_plus_recente(self, tmp_path: Path):
        append_entry(tmp_path, _entry(story_id="T1", origin="backfill"))
        append_entry(tmp_path, _entry(story_id="T1", origin="api"))
        append_entry(tmp_path, _entry(story_id="T2"))
        entry_t1 = last_entry_for(tmp_path, "T1")
        entry_t2 = last_entry_for(tmp_path, "T2")
        assert entry_t1 is not None and entry_t1["origin"] == "api"
        assert entry_t2 is not None and entry_t2["story_id"] == "T2"
        assert last_entry_for(tmp_path, "T404") is None

    def test_index_last_entries(self, tmp_path: Path):
        append_entry(tmp_path, _entry(story_id="T1"))
        append_entry(tmp_path, _entry(story_id="T2"))
        index = index_last_entries(tmp_path)
        assert set(index) == {"T1", "T2"}

    @pytest.mark.parametrize(
        ("origins", "expected"),
        [
            (["api", "sanction"], False),
            (["backfill"], True),
            (["api", "backfill"], True),
        ],
    )
    def test_is_backfilled_graduation(self, tmp_path: Path, origins, expected):
        for origin in origins:
            append_entry(tmp_path, _entry(story_id="T1", origin=origin))
        assert is_backfilled(tmp_path) is expected
