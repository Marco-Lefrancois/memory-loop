# -*- coding: utf-8 -*-
"""
Tests unitaires pour le Circuit-Breaker Herdr et le verrouillage Plan Mode (MLOOP-262-BE, MLOOP-263-BE).
Vérifie que :
1. En Phase 2 (plan/grill), Cline reçoit obligatoirement le flag '--plan'.
2. En cas d'échec de démarrage de Cline (erreur ou exception), Herdr bascule sur OpenCode (--yolo).
"""

from unittest.mock import MagicMock, call, patch
import pytest

from src.core.herdr_worker_core import spawn_story_worker_impl


class DummyHerdr:
    """Mock léger pour tester spawn_story_worker_impl."""
    def __init__(self):
        self.ensure_server_running = MagicMock()
        self._exec = MagicMock(return_value={"success": True, "result": {"pane": {"pane_id": "p_test_1"}}})
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
    assert "--yolo" in second_call_args["extra_args"]


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
    assert "--yolo" in dummy.start_agent.call_args_list[1][1]["extra_args"]
