"""
test_worker_harvest_partial.py - Tests de contrat pour la moisson partielle Herdr (L-02).

Vérifie que `harvest_story_evidence` distingue une moisson COMPLÈTE (worker inactif)
d'une moisson PARTIELLE (worker encore actif, capture 'visible' de repli), afin d'éliminer
le message contradictoire « agent_not_idle + Moisson réussie » observé lors du PoC de délégation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.herdr_adapter import HerdrAdapter


@pytest.fixture
def harvest_project(tmp_path):
    """Projet minimal avec un EvidencePack pré-existant."""
    proj = tmp_path / "Projects" / "TestHarvest"
    (proj / "memory" / "evidence").mkdir(parents=True)
    return proj


@pytest.mark.parametrize(
    "read_result, expected_partial, expected_status",
    [
        # Worker inactif : lecture recent-unwrapped réussie, aucun fallback -> moisson complète.
        (
            {"success": True, "raw_output": "log complet de la story"},
            False,
            "COMPLETED",
        ),
        # Worker actif : fallback 'visible' déclenché (worker_was_active) -> moisson partielle.
        (
            {
                "success": True,
                "raw_output": "capture visible partielle",
                "source_fallback": "visible",
                "worker_was_active": True,
            },
            True,
            "PARTIAL",
        ),
    ],
)
def test_harvest_flags_partial_state(
    harvest_project, read_result, expected_partial, expected_status
):
    """La moisson doit refléter fidèlement si le worker était encore actif."""
    adapter = HerdrAdapter()
    with patch.object(adapter, "read_agent_output", return_value=read_result):
        res = adapter.harvest_story_evidence(
            project_name="TestHarvest",
            story_id="SHOP-999",
            project_path=str(harvest_project.resolve()),
            lines=150,
        )

    assert res["success"] is True
    assert res.get("partial_harvest") is expected_partial
    assert res.get("worker_active_during_harvest") is expected_partial

    evidence_file = harvest_project / "memory" / "evidence" / "SHOP-999_evidence.json"
    assert evidence_file.exists()
    import json

    data = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert data["harvest_status"] == expected_status


def test_harvest_read_failure_is_not_partial(harvest_project):
    """Un échec de lecture total ne doit pas être confondu avec une moisson partielle."""
    adapter = HerdrAdapter()
    failed_read = {"success": False, "raw_output": "", "error": "pane introuvable"}
    with patch.object(adapter, "read_agent_output", return_value=failed_read):
        res = adapter.harvest_story_evidence(
            project_name="TestHarvest",
            story_id="SHOP-998",
            project_path=str(harvest_project.resolve()),
            lines=150,
        )

    # Pas de fallback 'visible' -> pas marqué partiel (le worker n'était pas "actif", la lecture a juste échoué).
    assert res.get("partial_harvest") is False
