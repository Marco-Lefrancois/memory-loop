"""
Tests d'instrumentation logging pour QaCertifierEngine (MLOOP-141-BE / ADR-0369).
Valide que les except Exception de run_pytest_suite loguent l'erreur avec
stack trace (exc_info=True) et contexte métier (gate, phase, check_name).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipelines import qa_certifier
from src.pipelines.qa_certifier import QaCertifierEngine


def test_logger_bound_via_get_logger():
    """Vérifie que qa_certifier.logger est bien issu de get_logger (persistance mloop.log)."""
    assert qa_certifier.logger.name == "mloop.pipelines.qa_certifier"


def test_run_pytest_suite_timeout_logs_error(tmp_path):
    """Un TimeoutExpired lors de l'invocation pytest doit produire un logger.error contextualisé."""
    engine = QaCertifierEngine(project_path=tmp_path, project_name="TestProj")

    with (
        patch.object(qa_certifier, "logger") as mock_logger,
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=180.0),
        ),
    ):
        result = engine.run_pytest_suite()

    assert result.all_passed is False
    mock_logger.error.assert_called_once()
    _, kwargs = mock_logger.error.call_args
    assert kwargs.get("exc_info") is True
    extra = kwargs.get("extra", {})
    assert extra.get("gate") == 3
    assert extra.get("phase") == "STAGE_4_VALIDATE"
    assert extra.get("check_name") == "pytest_suite"
    assert extra.get("violation_type") == "timeout"


def test_run_pytest_suite_generic_exception_logs_error(tmp_path):
    """Une Exception générique lors de l'invocation pytest doit produire un logger.error contextualisé."""
    engine = QaCertifierEngine(project_path=tmp_path, project_name="TestProj")

    with (
        patch.object(qa_certifier, "logger") as mock_logger,
        patch("subprocess.run", side_effect=RuntimeError("pytest introuvable")),
    ):
        result = engine.run_pytest_suite()

    assert result.all_passed is False
    mock_logger.error.assert_called_once()
    _, kwargs = mock_logger.error.call_args
    assert kwargs.get("exc_info") is True
    extra = kwargs.get("extra", {})
    assert extra.get("check_name") == "pytest_suite"
    assert extra.get("violation_type") == "invocation_error"
    assert extra.get("project") == "TestProj"
