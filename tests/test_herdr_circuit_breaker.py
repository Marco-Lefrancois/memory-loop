# -*- coding: utf-8 -*-
"""
Tests unitaires pour le Circuit-Breaker Herdr et le verrouillage Plan Mode (MLOOP-262-BE, MLOOP-263-BE).
Vérifie que :
1. En Phase 2 (plan/grill), Cline reçoit obligatoirement le flag '--plan'.
2. En cas d'échec de démarrage de Cline (erreur ou exception), Herdr bascule sur OpenCode (--auto).
"""

from pathlib import Path
from unittest.mock import MagicMock, call, patch
import pytest

from src.core.herdr_worker_core import spawn_story_worker_impl
from src.core._plan_act_guard import PlanActGuard, resolve_story_path


class DummyHerdr:
    """Mock léger pour tester spawn_story_worker_impl."""

    def __init__(self):
        self.ensure_server_running = MagicMock()
        self._exec = MagicMock(
            return_value={"success": True, "result": {"pane": {"pane_id": "p_test_1"}}}
        )
        self.start_agent = MagicMock(return_value={"success": True})
        self.wait_agent = MagicMock()
        self.send_keys = MagicMock()
        self.prompt_agent = MagicMock(return_value={"success": True})


@patch("time.sleep", return_value=None)
def test_cline_plan_mode_lock_enforced_in_plan_phase(mock_sleep):
    """Vérifie que '--plan' est injecté quand task_type est 'plan' pour Cline."""
    dummy = DummyHerdr()
    with patch("os.getcwd", return_value="C:/Memory Loop"):
        spawn_story_worker_impl(
            self=dummy,
            project_name="mLoop",
            story_id="MLOOP-260-BE",
            kind="cline",
            task_type="plan",
        )

    dummy.start_agent.assert_called_once()
    _, kwargs = dummy.start_agent.call_args
    assert kwargs["kind"] == "cline"
    assert "--plan" in kwargs["extra_args"]


@patch("time.sleep", return_value=None)
def test_circuit_breaker_triggers_on_cline_failure_dict(mock_sleep):
    """Vérifie que Herdr bascule sur OpenCode si start_agent(cline) retourne success=False."""
    dummy = DummyHerdr()
    # Premier appel (cline) échoue, second appel (opencode) réussit
    dummy.start_agent.side_effect = [
        {"success": False, "error": "Quota cline-free épuisé (429)"},
        {"success": True, "agent_id": "worker_mloop_260_be"},
    ]

    with patch("os.getcwd", return_value="C:/Memory Loop"):
        spawn_story_worker_impl(
            self=dummy,
            project_name="mLoop",
            story_id="MLOOP-260-BE",
            kind="cline",
            task_type="build",
        )

    assert dummy.start_agent.call_count == 2
    first_call_args = dummy.start_agent.call_args_list[0][1]
    second_call_args = dummy.start_agent.call_args_list[1][1]

    assert first_call_args["kind"] == "cline"
    assert second_call_args["kind"] == "opencode"
    assert "--auto" in second_call_args["extra_args"]


@patch("time.sleep", return_value=None)
def test_circuit_breaker_triggers_on_cline_exception(mock_sleep):
    """Vérifie que Herdr bascule sur OpenCode si start_agent(cline) lève une Exception."""
    dummy = DummyHerdr()
    dummy.start_agent.side_effect = [
        RuntimeError("%1 n'est pas une application Win32 valide"),
        {"success": True, "agent_id": "worker_mloop_260_be"},
    ]

    with patch("os.getcwd", return_value="C:/Memory Loop"):
        spawn_story_worker_impl(
            self=dummy,
            project_name="mLoop",
            story_id="MLOOP-260-BE",
            kind="cline",
            task_type="build",
        )

    assert dummy.start_agent.call_count == 2
    assert dummy.start_agent.call_args_list[0][1]["kind"] == "cline"
    assert dummy.start_agent.call_args_list[1][1]["kind"] == "opencode"
    assert "--auto" in dummy.start_agent.call_args_list[1][1]["extra_args"]


# ─── Tests unitaires du guard Plan/Act extrait (MLOOP-262-BE) ──────────────────


def _write_story(tmp_path: Path, story_id: str, status: str, grill: str) -> Path:
    """Crée un récit hermétique avec frontmatter minimal sous backlog/stories/."""
    stories_dir = tmp_path / "Projects" / "mLoop" / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    story_file = stories_dir / f"{story_id}.md"
    story_file.write_text(
        f"---\nid: {story_id}\nstatus: {status}\ngrill_me: {grill}\n---\n\n# {story_id}\n",
        encoding="utf-8",
    )
    return story_file


def test_plan_act_guard_evaluate_mode_act_when_ready_and_grilled(tmp_path: Path):
    """READY_FOR_DEV + grill_me DONE => mode 'act'."""
    story = _write_story(tmp_path, "MLOOP-260-BE", "READY_FOR_DEV", "DONE")
    assert PlanActGuard.evaluate_mode(str(story)) == "act"


def test_plan_act_guard_evaluate_mode_plan_when_draft(tmp_path: Path):
    """DRAFT (non certifié) => mode 'plan' (confinement Phase 2)."""
    story = _write_story(tmp_path, "MLOOP-263-BE", "DRAFT", "PENDING")
    assert PlanActGuard.evaluate_mode(str(story)) == "plan"


def test_plan_act_guard_evaluate_mode_plan_when_ready_but_not_grilled(tmp_path: Path):
    """READY_FOR_DEV mais grill_me non DONE => 'plan' (les deux conditions requises)."""
    story = _write_story(tmp_path, "MLOOP-262-BE", "READY_FOR_DEV", "PENDING")
    assert PlanActGuard.evaluate_mode(str(story)) == "plan"


def test_plan_act_guard_evaluate_mode_fail_closed_on_missing_file(tmp_path: Path):
    """Fichier introuvable ou chemin None => 'plan' fail-closed, aucune exception."""
    assert PlanActGuard.evaluate_mode(str(tmp_path / "inexistant.md")) == "plan"
    assert PlanActGuard.evaluate_mode(None) == "plan"


def test_plan_act_guard_enforce_flags_injects_plan():
    """Mode 'plan' injecte '--plan' s'il est absent (idempotent)."""
    assert "--plan" in PlanActGuard.enforce_flags([], "plan")
    # Idempotence : ne duplique pas si déjà présent
    assert PlanActGuard.enforce_flags(["--plan"], "plan").count("--plan") == 1
    # Respecte l'alias court '-p'
    assert PlanActGuard.enforce_flags(["-p"], "plan").count("--plan") == 0


def test_plan_act_guard_enforce_flags_purges_plan_in_act_mode():
    """Mode 'act' purge tout résidu '--plan' / '-p'."""
    result = PlanActGuard.enforce_flags(["--auto", "--plan", "-p"], "act")
    assert "--plan" not in result and "-p" not in result
    assert "--auto" in result


def test_resolve_story_path_finds_story(tmp_path: Path):
    """resolve_story_path localise le récit sous Projects/<p>/backlog/stories/."""
    story = _write_story(tmp_path, "MLOOP-261-BE", "DRAFT", "PENDING")
    resolved = resolve_story_path("mLoop", "MLOOP-261-BE", root=tmp_path)
    assert resolved is not None and resolved.resolve() == story.resolve()


def test_resolve_story_path_returns_none_when_absent(tmp_path: Path):
    """resolve_story_path retourne None si le récit n'existe pas (=> plan fail-closed)."""
    assert resolve_story_path("mLoop", "MLOOP-999-XX", root=tmp_path) is None
