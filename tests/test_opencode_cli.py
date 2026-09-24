"""Tests unitaires pour le bridge d'exécution OpenCode CLI (MLOOP-220-BE)."""

import argparse
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.commands.handlers.opencode import (
    handle_init,
    handle_opencode,
    handle_run,
    handle_status,
    is_opencode_available,
    generate_opencode_config,
)


@pytest.fixture
def temp_project(tmp_path: Path):
    """Fixture créant un dossier projet temporaire conforme."""
    proj = tmp_path / "Projects" / "TestProject"
    proj.mkdir(parents=True, exist_ok=True)
    return proj


def test_generate_opencode_config_structure(temp_project: Path):
    """Vérifie la structure JSON générée pour opencode.json."""
    config = generate_opencode_config("TestProject")
    assert "$schema" in config
    assert "providers" in config
    assert "litellm" in config["providers"]
    assert config["providers"]["litellm"]["endpoint"] == "http://localhost:4000/v1"
    assert "models" in config["providers"]["litellm"]
    assert "rules" in config


def test_handle_init_success(temp_project: Path):
    """Vérifie l'initialisation réussie de .opencode/opencode.json."""
    args = argparse.Namespace(project="TestProject", action="init")
    state = MagicMock()
    state.project_name = "TestProject"

    exit_code = handle_init(args, state, temp_project)
    assert exit_code == 0

    cfg_file = temp_project / ".opencode" / "opencode.json"
    assert cfg_file.exists()

    data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert data["providers"]["litellm"]["endpoint"] == "http://localhost:4000/v1"


def test_handle_init_invalid_project():
    """Vérifie le rejet d'un projet inexistant ou vide."""
    args = argparse.Namespace(project="", action="init")
    state = MagicMock()
    non_existent = Path("non_existent_dir_xyz_123")

    exit_code = handle_init(args, state, non_existent)
    assert exit_code != 0


def test_is_opencode_available_mock():
    """Vérifie la détection du binaire opencode via shutil.which."""
    with patch("shutil.which", return_value="/usr/local/bin/opencode"):
        assert is_opencode_available() is True

    with patch("shutil.which", return_value=None):
        assert is_opencode_available() is False


def test_handle_status():
    """Vérifie l'exécution du diagnostic de statut."""
    args = argparse.Namespace(project="TestProject", action="status")
    state = MagicMock()
    proj = Path(".")

    with patch("src.commands.handlers.opencode.check_litellm_connectivity", return_value=True):
        exit_code = handle_status(args, state, proj)
        assert exit_code in (0, 1)


def test_handle_run_binary_missing(temp_project: Path):
    """Vérifie que run échoue proprement si le binaire opencode est absent."""
    args = argparse.Namespace(
        project="TestProject",
        action="run",
        headless=True,
        prompt="Fais ceci",
    )
    state = MagicMock()

    with patch("shutil.which", return_value=None):
        exit_code = handle_run(args, state, temp_project)
        assert exit_code == 1


def test_handle_opencode_dispatch(temp_project: Path):
    """Vérifie le routage des actions via handle_opencode."""
    state = MagicMock()

    args_init = argparse.Namespace(project="TestProject", action="init")
    with patch("src.commands.handlers.opencode.handle_init", return_value=0) as m_init:
        code = handle_opencode(args_init, state, temp_project)
        assert code == 0
        m_init.assert_called_once()
