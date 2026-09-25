# -*- coding: utf-8 -*-
"""
tests/test_skill_eval_cli.py — Tests exhaustifs pour MLOOP-244-FULL (CLI skill-eval & Check 23 Vibe-Check).
Valide la conformité ADR-0202 (<= 300 lignes), ADR-0369, ADR-0370 et ADR-0389.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.commands.handlers.skill_eval import handle_skill_eval
from src.pipelines.vibe_check._vc_agents import check_23_skills_health


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_cli_skill_eval_all_nominal() -> None:
    """Vérifie l'exécution nominale de 'mloop skill-eval --all' (exit code 0)."""
    args = argparse.Namespace(
        all=True,
        skill=None,
        fast=True,
        flywheel=False,
        apply_patch=None,
        json=False,
        batch=True,
    )
    exit_code = handle_skill_eval(args)
    assert exit_code == 0


def test_cli_skill_eval_single_skill() -> None:
    """Vérifie l'exécution ciblée sur une compétence unique existante."""
    args = argparse.Namespace(
        all=False,
        skill="grill",
        fast=True,
        flywheel=False,
        apply_patch=None,
        json=False,
        batch=True,
    )
    exit_code = handle_skill_eval(args)
    assert exit_code == 0


def test_cli_skill_eval_unknown_skill_returns_error() -> None:
    """Vérifie qu'une compétence introuvable retourne un exit code 1."""
    args = argparse.Namespace(
        all=False,
        skill="non_existent_skill_xyz",
        fast=True,
        flywheel=False,
        apply_patch=None,
        json=False,
        batch=True,
    )
    exit_code = handle_skill_eval(args)
    assert exit_code == 1


def test_cli_skill_eval_json_output() -> None:
    """Vérifie que l'option --json produit un payload JSON valide sur stdout."""
    args = argparse.Namespace(
        all=False,
        skill="grill",
        fast=True,
        flywheel=False,
        apply_patch=None,
        json=True,
        batch=True,
    )
    captured = io.StringIO()
    with patch("sys.stdout", captured):
        exit_code = handle_skill_eval(args)

    assert exit_code == 0
    raw_output = captured.getvalue()
    # Recherche du bloc JSON
    json_start = raw_output.find("{")
    assert json_start != -1
    parsed = json.loads(raw_output[json_start:])
    assert "evaluation" in parsed
    assert parsed["evaluation"]["total_skills"] == 1


def test_vibe_check_check_23_nominal(repo_root: Path) -> None:
    """Vérifie que Check 23 du Vibe-Check s'exécute et retourne PASS sur les 39 compétences saines."""
    proj_dir = repo_root / "Projects" / "mLoop"
    res = check_23_skills_health(proj_dir, "mLoop", "RUN", "STAGE_BUILD")

    assert res["status"] == "PASS"
    assert "Check 23" in res["check"]
    assert "score" in res
    assert res["failed_count"] == 0


def test_vibe_check_check_23_warning_on_degraded_state(repo_root: Path) -> None:
    """Vérifie que Check 23 retourne un WARNING non bloquant en cas de compétence dégradée."""
    mock_summary = {
        "total_skills": 39,
        "average_score": 68.0,
        "failed": 2,
        "warning": 5,
        "passed": 32,
    }
    with patch("src.pipelines.skill_eval.SkillEvalEngine.evaluate_all_skills", return_value=mock_summary):
        proj_dir = repo_root / "Projects" / "mLoop"
        res = check_23_skills_health(proj_dir, "mLoop", "RUN", "STAGE_BUILD")

        # Conforme ADR-0384 : le verdict doit être WARNING (jamais FAIL bloquant)
        assert res["status"] == "WARNING"
        assert res["failed_count"] == 2


def test_cli_apply_patch_nonexistent_returns_error() -> None:
    """Vérifie que --apply-patch sur un patch inexistant retourne un code d'erreur 1."""
    args = argparse.Namespace(
        all=False,
        skill=None,
        fast=False,
        flywheel=False,
        apply_patch="nonexistent_skill",
        json=False,
        batch=True,
    )
    exit_code = handle_skill_eval(args)
    assert exit_code == 1
