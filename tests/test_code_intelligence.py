"""
Tests unitaires pour les handlers Code Intelligence et l'intégration CodeGraph (ADR-0204).
"""
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.commands.handlers.code_intelligence import (
    _find_target_source_path,
    _get_codegraph_binary,
    handle_code_affected,
    handle_code_explore,
    handle_code_impact,
    handle_code_init,
    handle_code_status,
)
from src.state import LoopState


@pytest.fixture
def mock_project(tmp_path: Path):
    proj = tmp_path / "Projects" / "TestApp"
    proj.mkdir(parents=True)
    (proj / "reference" / "src_app").mkdir(parents=True)
    return proj


def test_find_target_source_path_with_explicit(mock_project: Path):
    custom = mock_project / "custom_src"
    custom.mkdir()
    found = _find_target_source_path(mock_project, "custom_src")
    assert found == custom


def test_find_target_source_path_in_reference(mock_project: Path):
    found = _find_target_source_path(mock_project)
    assert found == mock_project / "reference" / "src_app"


def test_find_target_source_path_with_dot_codegraph(mock_project: Path):
    dot_cg = mock_project / "reference" / "src_app" / ".codegraph"
    dot_cg.mkdir()
    found = _find_target_source_path(mock_project)
    assert found == mock_project / "reference" / "src_app"


@patch("src.commands.handlers.code_intelligence._run_codegraph_command")
@patch("src.commands.handlers.code_intelligence._get_codegraph_binary", return_value="codegraph")
def test_handle_code_explore(mock_bin, mock_run, mock_project: Path):
    mock_run.return_value = MagicMock(returncode=0, stdout="explore output", stderr="")
    args = argparse.Namespace(project="TestApp", query="UserService", path=None)
    state = LoopState(project_name="TestApp")

    code = handle_code_explore(args, state, mock_project)
    assert code == 0
    mock_run.assert_called_once()


@patch("src.commands.handlers.code_intelligence._run_codegraph_command")
@patch("src.commands.handlers.code_intelligence._get_codegraph_binary", return_value="codegraph")
def test_handle_code_impact(mock_bin, mock_run, mock_project: Path):
    mock_run.return_value = MagicMock(returncode=0, stdout="impact output", stderr="")
    args = argparse.Namespace(project="TestApp", symbol="UserLogin", path=None)
    state = LoopState(project_name="TestApp")

    code = handle_code_impact(args, state, mock_project)
    assert code == 0
    mock_run.assert_called_once()


@patch("src.commands.handlers.code_intelligence._run_codegraph_command")
@patch("src.commands.handlers.code_intelligence._get_codegraph_binary", return_value="codegraph")
def test_handle_code_status(mock_bin, mock_run, mock_project: Path):
    mock_run.return_value = MagicMock(returncode=0, stdout="status output", stderr="")
    args = argparse.Namespace(project="TestApp", path=None)
    state = LoopState(project_name="TestApp")

    code = handle_code_status(args, state, mock_project)
    assert code == 0
    mock_run.assert_called_once()
