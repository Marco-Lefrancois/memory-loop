"""
Tests unitaires pour les handlers Plannotator (review, annotate, guide-export).
"""
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.commands.handlers.plannotator import (
    _get_plannotator_binary,
    _resolve_annotation_target,
    handle_annotate,
    handle_guide_export,
    handle_review,
)
from src.state import LoopState


@pytest.fixture
def mock_project(tmp_path: Path):
    proj = tmp_path / "Projects" / "TestProject"
    stories_dir = proj / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    (stories_dir / "US-042.md").write_text("# US-042 Story Content", encoding="utf-8")
    (proj / "memory").mkdir(parents=True)
    return proj


def test_get_plannotator_binary():
    with patch("shutil.which", return_value="C:/fake/plannotator.exe"):
        assert _get_plannotator_binary() == "C:/fake/plannotator.exe"

    with patch("shutil.which", return_value=None):
        with patch("pathlib.Path.exists", return_value=True):
            binary = _get_plannotator_binary()
            assert binary is not None
            assert "plannotator" in binary


def test_resolve_annotation_target_url(mock_project: Path):
    args = argparse.Namespace(url="http://localhost:3000", story=None, adr=None, file=None, target=None)
    state = LoopState(project_name="TestProject")
    target = _resolve_annotation_target(args, state, mock_project)
    assert target == "http://localhost:3000"


def test_resolve_annotation_target_story(mock_project: Path):
    args = argparse.Namespace(url=None, story="US-042", adr=None, file=None, target=None)
    state = LoopState(project_name="TestProject")
    target = _resolve_annotation_target(args, state, mock_project)
    assert target is not None
    assert target.endswith("US-042.md")


def test_resolve_annotation_target_file(mock_project: Path):
    test_file = mock_project / "readme.txt"
    test_file.write_text("hello", encoding="utf-8")
    args = argparse.Namespace(url=None, story=None, adr=None, file=str(test_file), target=None)
    state = LoopState(project_name="TestProject")
    target = _resolve_annotation_target(args, state, mock_project)
    assert target == str(test_file)


@patch("src.commands.handlers.plannotator.subprocess.run")
@patch("src.commands.handlers.plannotator._get_plannotator_binary", return_value="plannotator")
def test_handle_review_git(mock_bin, mock_run, mock_project: Path):
    mock_run.return_value = MagicMock(returncode=0)
    args = argparse.Namespace(pr=None, tailscale=False, no_local=False)
    state = LoopState(project_name="TestProject")

    code = handle_review(args, state, mock_project)
    assert code == 0
    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd == ["plannotator", "review", "--git"]


@patch("src.commands.handlers.plannotator.subprocess.run")
@patch("src.commands.handlers.plannotator._get_plannotator_binary", return_value="plannotator")
def test_handle_review_pr(mock_bin, mock_run, mock_project: Path):
    mock_run.return_value = MagicMock(returncode=0)
    args = argparse.Namespace(pr="https://github.com/org/repo/pull/42", tailscale=True, no_local=True)
    state = LoopState(project_name="TestProject")

    code = handle_review(args, state, mock_project)
    assert code == 0
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd == [
        "plannotator",
        "review",
        "https://github.com/org/repo/pull/42",
        "--no-local",
        "--tailscale",
    ]


@patch("src.commands.handlers.plannotator.subprocess.run")
@patch("src.commands.handlers.plannotator._get_plannotator_binary", return_value="plannotator")
def test_handle_annotate_story(mock_bin, mock_run, mock_project: Path):
    mock_run.return_value = MagicMock(returncode=0)
    args = argparse.Namespace(
        story="US-042",
        url=None,
        adr=None,
        file=None,
        target=None,
        no_gate=False,
        require_approval=True,
        json=True,
        result_file="decision.json",
        tailscale=False,
    )
    state = LoopState(project_name="TestProject")

    code = handle_annotate(args, state, mock_project)
    assert code == 0
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == "plannotator"
    assert called_cmd[1] == "annotate"
    assert "US-042.md" in called_cmd[2]
    assert "--gate" in called_cmd
    assert "--require-approval" in called_cmd
    assert "--json" in called_cmd
    assert "--result-file" in called_cmd


def test_handle_approve_headless(mock_project: Path):
    """Vérifie l'approbation headless sans binaire ni UI."""
    from src.commands.handlers.plannotator import handle_approve

    plan_dir = mock_project / "memory" / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "MLOOP-221-BE_phase_plan.md"
    plan_file.write_text("# Plan MLOOP-221-BE\nContenu initial", encoding="utf-8")

    args = argparse.Namespace(
        story="MLOOP-221-BE",
        approve=True,
        file=str(plan_file),
    )
    state = LoopState(project_name="TestProject")

    code = handle_approve(args, state, mock_project)
    assert code == 0

    annotated = plan_dir / "MLOOP-221-BE_phase_plan.annotated.md"
    assert annotated.exists()
    content = annotated.read_text(encoding="utf-8")
    assert "Plannotator Approved (Headless CI/CD Mode)" in content
    assert "Contenu initial" in content


def test_handle_plannotator_status(mock_project: Path):
    """Vérifie le diagnostic de statut Plannotator."""
    from src.commands.handlers.plannotator import handle_plannotator

    args = argparse.Namespace(action="status")
    state = LoopState(project_name="TestProject")
    code = handle_plannotator(args, state, mock_project)
    assert code == 0


def test_zero_orphan_root_invariant():
    """Vérifie qu'aucun répertoire plannotator/ n'existe à la racine du framework."""
    assert not Path("plannotator").exists()

