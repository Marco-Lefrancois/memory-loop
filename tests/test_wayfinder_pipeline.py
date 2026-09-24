"""Tests unitaires pour le pipeline décisionnel Wayfinder (MLOOP-222-BE / ADR-014)."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.pipelines.wayfinder import WayfinderEngine


@pytest.fixture
def temp_project(tmp_path: Path):
    """Fixture d'un projet isolé."""
    proj = tmp_path / "Projects" / "TestProject"
    proj.mkdir(parents=True, exist_ok=True)
    return proj


def test_wayfinder_init_map_canonical_path(temp_project: Path):
    """Vérifie l'initialisation de la carte sous memory/wayfinder/wayfinder_map.md."""
    wf = WayfinderEngine(temp_project)
    map_path = wf.init_map("Refonte Architecture", goal="Éliminer les goulets d'étranglement")

    assert map_path.exists()
    assert map_path == temp_project / "memory" / "wayfinder" / "wayfinder_map.md"

    content = map_path.read_text(encoding="utf-8")
    assert "Refonte Architecture" in content
    assert "Éliminer les goulets d'étranglement" in content
    assert "Destination" in content or "Objectif" in content


def test_wayfinder_add_ticket_hitl_and_afk(temp_project: Path):
    """Vérifie l'ajout de tickets typés HITL et AFK."""
    wf = WayfinderEngine(temp_project)
    wf.init_map("Projet Alpha", goal="Vision 2027")

    wf.add_ticket("T-01", "Choix du framework", "Arbitrage entre FastAPI et Starlite", kind="HITL")
    wf.add_ticket("T-02", "Benchmark réseau", "Mesure de latence sous charge", kind="AFK", blocked_by=["T-01"])

    frontier = wf.get_frontier()
    assert len(frontier) == 1
    assert frontier[0]["id"] == "T-01"
    assert frontier[0]["kind"] == "HITL"


def test_wayfinder_resolve_ticket_unblocks_frontier(temp_project: Path):
    """Vérifie que la résolution d'un ticket HITL débloque le ticket AFK dépendant."""
    wf = WayfinderEngine(temp_project)
    wf.init_map("Projet Beta", goal="Objectif")

    wf.add_ticket("T-01", "Choix Framework", "Description T-01", kind="HITL")
    wf.add_ticket("T-02", "Benchmark", "Description T-02", kind="AFK", blocked_by=["T-01"])

    # Avant résolution
    frontier_before = wf.get_frontier()
    assert len(frontier_before) == 1
    assert frontier_before[0]["id"] == "T-01"

    # Résolution de T-01
    success = wf.resolve_ticket("T-01", "FastAPI retenu pour écosystème mLoop")
    assert success is True

    # Après résolution : T-02 est débloqué sur la frontière
    frontier_after = wf.get_frontier()
    assert len(frontier_after) == 1
    assert frontier_after[0]["id"] == "T-02"
    assert frontier_after[0]["kind"] == "AFK"


def test_wayfinder_resolve_unknown_ticket(temp_project: Path):
    """Vérifie l'échec lors de la tentative de résolution d'un ticket inexistant."""
    wf = WayfinderEngine(temp_project)
    wf.init_map("Projet Gamma")
    success = wf.resolve_ticket("T-999", "Décision fantôme")
    assert success is False
