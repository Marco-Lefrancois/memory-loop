"""
Tests unitaires pour la sonde déterministe des runtimes d'agents locaux (ADR-0377).
Conforme aux standards de robustesse Python senior (ADR-0369).
"""

import subprocess
from unittest.mock import MagicMock, patch
import pytest

from src.core.agent_probe import (
    AGENT_CATALOG,
    AgentAvailability,
    AgentDefinition,
    AgentProbe,
    render_agent_report,
)


@pytest.fixture
def sample_catalog():
    return {
        "test-agent": AgentDefinition(
            id="test-agent",
            name="Test Agent CLI",
            bin_name="testagent",
            version_args=["--version"],
            min_version="1.5.0",
            role="Test Role",
            critical_in_stages=("STAGE_BUILD",),
        )
    }


def test_probe_missing_binary(sample_catalog):
    """Vérifie que l'absence du binaire dans le PATH est détectée gracieusement."""
    probe = AgentProbe(catalog=sample_catalog)
    with patch("shutil.which", return_value=None):
        status = probe.probe("test-agent")
        assert status.availability == AgentAvailability.MISSING
        assert status.installed_path is None
        assert not status.is_usable


def test_probe_successful_available(sample_catalog):
    """Vérifie la détection nominale avec extraction de version semver."""
    probe = AgentProbe(catalog=sample_catalog)
    mock_run = MagicMock()
    mock_run.stdout = "testagent version 2.0.1 (build x86_64)"
    mock_run.stderr = ""

    with patch("shutil.which", return_value="/usr/local/bin/testagent"), \
         patch("subprocess.run", return_value=mock_run):
        status = probe.probe("test-agent")
        assert status.availability == AgentAvailability.AVAILABLE
        assert status.detected_version == "2.0.1"
        assert status.installed_path == "/usr/local/bin/testagent"
        assert status.is_usable


def test_probe_outdated_version(sample_catalog):
    """Vérifie qu'une version inférieure à la version minimale requise est signalée."""
    probe = AgentProbe(catalog=sample_catalog)
    mock_run = MagicMock()
    mock_run.stdout = "testagent version 1.2.0"
    mock_run.stderr = ""

    with patch("shutil.which", return_value="/usr/local/bin/testagent"), \
         patch("subprocess.run", return_value=mock_run):
        status = probe.probe("test-agent")
        assert status.availability == AgentAvailability.OUTDATED
        assert status.detected_version == "1.2.0"
        assert status.is_usable  # Un agent obsolète reste utilisable mais déclenche un avertissement


def test_probe_timeout_resilience(sample_catalog):
    """Vérifie la gestion d'un timeout strict sans bloquer l'agent (ADR-0369 Standard 3)."""
    probe = AgentProbe(catalog=sample_catalog, probe_timeout=0.5)

    with patch("shutil.which", return_value="/usr/local/bin/testagent"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["testagent"], timeout=0.5)):
        status = probe.probe("test-agent")
        assert status.availability == AgentAvailability.TIMEOUT
        assert not status.is_usable
        assert "timeout" in (status.error_message or "").lower()


def test_probe_unexpected_exception(sample_catalog):
    """Vérifie qu'une exception inattendue est capturée et journalisée (Zero-Silent-Pass)."""
    probe = AgentProbe(catalog=sample_catalog)

    with patch("shutil.which", return_value="/usr/local/bin/testagent"), \
         patch("subprocess.run", side_effect=PermissionError("Accès refusé")):
        status = probe.probe("test-agent")
        assert status.availability == AgentAvailability.ERROR
        assert not status.is_usable
        assert "accès refusé" in (status.error_message or "").lower()


@pytest.mark.parametrize(
    ("current", "target", "expected_older"),
    [
        ("1.0.0", "1.1.0", True),
        ("2.0.0", "1.9.9", False),
        ("1.5.0", "1.5.0", False),
        ("0.4.0", "0.5.0", True),
    ],
)
def test_version_comparison_logic(current, target, expected_older):
    """Vérifie la logique de comparaison semver simple."""
    assert AgentProbe._is_version_older(current, target) == expected_older


def test_check_readiness_stage_rules():
    """Vérifie les règles de validation par étape de cycle."""
    probe = AgentProbe()

    # En phase INGEST, herdr manquant n'est pas bloquant
    with patch.object(probe, "probe_all") as mock_probe_all:
        mock_status = MagicMock()
        mock_status.definition = AGENT_CATALOG["herdr"]
        mock_status.is_usable = False
        mock_status.error_message = "absent"
        mock_status.availability = AgentAvailability.MISSING
        mock_probe_all.return_value = [mock_status]

        # En STAGE_1_INGEST : passe car herdr n'est pas critique en ingest
        ready, violations = probe.check_readiness(stage="STAGE_1_INGEST")
        assert ready is True
        assert len(violations) == 0

        # En STAGE_BUILD : herdr est critique -> échec
        ready_build, violations_build = probe.check_readiness(stage="STAGE_BUILD")
        assert ready_build is False
        assert len(violations_build) > 0


def test_render_agent_report_formats(sample_catalog):
    """Vérifie le rendu texte et JSON du rapport d'audit."""
    probe = AgentProbe(catalog=sample_catalog)
    with patch("shutil.which", return_value=None):
        statuses = probe.probe_all()

    text_report = render_agent_report(statuses, json_format=False)
    assert "Test Agent CLI" in text_report
    assert "○ INTROUVABLE" in text_report

    json_report = render_agent_report(statuses, json_format=True)
    import json
    data = json.loads(json_report)
    assert isinstance(data, list)
    assert data[0]["id"] == "test-agent"
    assert data[0]["availability"] == "MISSING"
