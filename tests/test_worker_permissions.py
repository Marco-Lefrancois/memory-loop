# -*- coding: utf-8 -*-
"""
Tests unitaires pour la gouvernance des permissions des workers Herdr (ADR-0389).

Couvre :
- Matrice des drapeaux auto-approuvés OpenCode (--auto, --agent worker).
- Matrice des drapeaux auto-approuvés Cline (--auto-approve true).
- Préservation de l'auto-approbation en mode Plan pour Cline.
- Présence du bloc permission complet dans le template de projet.
- Présence du bloc permission dans generate_opencode_config.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.commands.handlers.opencode import generate_opencode_config
from src.core._plan_act_guard import PlanActGuard
from src.core.herdr_worker_core import spawn_story_worker_impl
from src.core.worker_runtimes import get_worker_runtime


def test_opencode_flags_contain_auto_and_agent_worker():
    """Vérifie que OpenCode génère obligatoirement --auto et --agent worker."""
    spec = get_worker_runtime("opencode")
    flags = spec.build_flags()
    assert "--auto" in flags
    assert "--agent" in flags
    idx_agent = flags.index("--agent")
    assert flags[idx_agent + 1] == "worker"


def test_opencode_flags_preserve_model_with_auto():
    """Vérifie que le modèle s'ajoute sans altérer --auto et --agent worker."""
    spec = get_worker_runtime("opencode")
    flags = spec.build_flags(model="nmedia_cloud/claude-sonnet-5")
    assert flags[:3] == ["--auto", "--agent", "worker"]
    assert "--model" in flags
    assert "nmedia_cloud/claude-sonnet-5" in flags


def test_cline_flags_contain_auto_approve_true():
    """Vérifie que Cline génère obligatoirement --auto-approve true."""
    spec = get_worker_runtime("cline")
    flags = spec.build_flags()
    assert "--auto-approve" in flags
    idx = flags.index("--auto-approve")
    assert flags[idx + 1] == "true"


def test_cline_plan_mode_preserves_auto_approve():
    """En mode plan, Cline doit conserver --auto-approve true et ajouter --plan."""
    spec = get_worker_runtime("cline")
    flags = spec.build_flags()
    enforced = PlanActGuard.enforce_flags(flags, "plan")
    assert "--auto-approve" in enforced
    assert enforced[enforced.index("--auto-approve") + 1] == "true"
    assert "--plan" in enforced


def test_project_template_contains_permissions_block():
    """Vérifie que le blueprint projet contient le bloc permission complet."""
    template_path = Path("standards/blueprints/project_opencode_template.json")
    assert template_path.exists()
    data = json.loads(template_path.read_text(encoding="utf-8"))
    assert "permission" in data
    perm = data["permission"]
    assert perm.get("edit") == "allow"
    assert perm.get("read") == "allow"
    assert perm.get("external_directory") == {"*": "allow"}
    assert perm.get("bash") == {"*": "allow"}


def test_generate_opencode_config_contains_permissions_block():
    """Vérifie que generate_opencode_config inclut la section permission."""
    cfg = generate_opencode_config("MonProjetTest")
    assert "permission" in cfg
    perm = cfg["permission"]
    assert perm.get("edit") == "allow"
    assert perm.get("read") == "allow"
    assert perm.get("external_directory") == {"*": "allow"}
    assert perm.get("bash") == {"*": "allow"}


@patch("time.sleep", return_value=None)
def test_spawn_story_worker_guarantees_auto_for_opencode(mock_sleep):
    """Vérifie que spawn_story_worker_impl injecte --auto même si extra_args omis."""
    dummy = MagicMock()
    dummy.ensure_server_running = MagicMock()
    dummy._exec = MagicMock(
        return_value={"success": True, "result": {"pane": {"pane_id": "p_test"}}}
    )
    dummy.start_agent = MagicMock(return_value={"success": True})
    dummy.wait_agent = MagicMock()
    dummy.prompt_agent = MagicMock(return_value={"success": True})

    with patch("os.getcwd", return_value="C:/Memory Loop"):
        res = spawn_story_worker_impl(
            self=dummy,
            project_name="mLoop",
            story_id="MLOOP-999-PERM",
            kind="opencode",
        )

    assert res["success"] is True
    call_args = dummy.start_agent.call_args[1]
    extra = call_args["extra_args"]
    assert "--auto" in extra
    assert "--agent" in extra
    assert "worker" in extra
