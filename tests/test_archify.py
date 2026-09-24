"""
Tests unitaires pour Archify Runner et l'intégration mLoop (tools/archify/archify_runner.py).
"""
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.commands.handlers.tooling import handle_archify
from src.state import LoopState
from tools.archify.archify_runner import (
    find_archify_bin,
    normalize_diagram_type,
    run_archify_command,
    run_archify_doctor,
)


def test_find_archify_bin():
    with patch("pathlib.Path.exists", return_value=True):
        bin_path = find_archify_bin()
        assert bin_path is not None
        assert "archify.mjs" in str(bin_path)


def test_normalize_diagram_type_native():
    assert normalize_diagram_type("architecture") == "architecture"
    assert normalize_diagram_type("workflow") == "workflow"
    assert normalize_diagram_type("sequence") == "sequence"
    assert normalize_diagram_type("dataflow") == "dataflow"
    assert normalize_diagram_type("lifecycle") == "lifecycle"


def test_normalize_diagram_type_aliases():
    assert normalize_diagram_type("flow") == "workflow"
    assert normalize_diagram_type("mindmap") == "architecture"


def test_normalize_diagram_type_auto_detection():
    assert normalize_diagram_type(None, "pipeline.dataflow.json") == "dataflow"
    assert normalize_diagram_type(None, "user_journey.workflow.json") == "workflow"
    assert normalize_diagram_type(None, "auth_dance.sequence.json") == "sequence"
    assert normalize_diagram_type(None, "story_state.lifecycle.json") == "lifecycle"
    assert normalize_diagram_type(None, "unknown.json") == "architecture"


@patch("tools.archify.archify_runner.subprocess.run")
@patch("tools.archify.archify_runner.find_archify_bin", return_value=Path("C:/fake/archify.mjs"))
def test_run_archify_doctor(mock_bin, mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    code = run_archify_doctor()
    assert code == 0
    mock_run.assert_called_once_with(["node", "C:\\fake\\archify.mjs", "doctor"], text=True, timeout=60)


@patch("tools.archify.archify_runner.subprocess.run")
@patch("tools.archify.archify_runner.find_archify_bin", return_value=Path("C:/fake/archify.mjs"))
def test_run_archify_command_validate(mock_bin, mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout='{"ok": true}', stderr="")
    code = run_archify_command("validate", "workflow", "spec.json", quality="showcase")
    assert code == 0
    mock_run.assert_called_once()
    called_args = mock_run.call_args[0][0]
    assert called_args == ["node", "C:\\fake\\archify.mjs", "validate", "workflow", "spec.json", "--quality", "showcase", "--json"]


@patch("tools.archify.archify_runner.run_archify_doctor", return_value=0)
def test_handle_archify_doctor(mock_doctor):
    args = argparse.Namespace(doctor=True, file=None)
    code = handle_archify(args, None, None)
    assert code == 0
    mock_doctor.assert_called_once()


def test_handle_archify_missing_file():
    args = argparse.Namespace(doctor=False, file=None)
    code = handle_archify(args, None, None)
    assert code == 1


@patch("tools.archify.archify_runner.run_archify_command", return_value=0)
def test_handle_archify_validate_only(mock_run, tmp_path: Path):
    dummy_spec = tmp_path / "diagram.workflow.json"
    dummy_spec.write_text("{}", encoding="utf-8")

    args = argparse.Namespace(
        doctor=False,
        file=str(dummy_spec),
        type=None,
        validate_only=True,
        quality="showcase",
        output=None,
        open=False,
    )
    code = handle_archify(args, None, tmp_path)
    assert code == 0
    mock_run.assert_called_once_with("validate", "workflow", str(dummy_spec), quality="showcase")
