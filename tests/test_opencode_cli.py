# -*- coding: utf-8 -*-
"""
Tests unitaires pour MLOOP-254-FULL : Orchestration & Statut CLI OpenCode.
Conforme ADR-0202 (<=300L) et 4 Piliers Gherkin.
"""

import argparse
import json
from pathlib import Path
import pytest
from src.commands.handlers.opencode import (
    handle_init,
    handle_opencode,
    handle_status,
    handle_sync,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Projet temporaire avec arborescence mLoop minimale."""
    agents_dir = tmp_path / ".agents" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "worker.md").write_text(
        "---\nname: worker\nrole: Worker\nskills: [tdd]\n---\nMission worker.",
        encoding="utf-8",
    )
    return tmp_path


def test_handle_status_nominal(temp_project: Path, capsys):
    """Pilier 1 - Nominal : Affichage du statut d'environnement OpenCode."""
    args = argparse.Namespace(action="status", project="test_proj")
    code = handle_status(args, None, temp_project)

    captured = capsys.readouterr().out
    assert "État de l'Environnement OpenCode CLI" in captured
    assert "Binaire OpenCode" in captured
    assert "Proxy LiteLLM" in captured


def test_handle_sync_dry_run(temp_project: Path, capsys):
    """Pilier 3 - Résilience : Mode --dry-run sans altération du disque."""
    args = argparse.Namespace(action="sync", project="test_proj", dry_run=True)
    code = handle_sync(args, None, temp_project)

    assert code == 0
    captured = capsys.readouterr().out
    assert "Dry-Run" in captured or "Simulation" in captured

    # Aucun fichier créé
    assert not (temp_project / ".opencode" / "tools" / "fact_search.ts").exists()
    assert not (temp_project / ".opencode" / "agents" / "worker.md").exists()


def test_handle_sync_nominal(temp_project: Path, capsys):
    """Pilier 1 - Nominal : Synchronisation complète des personas et tools."""
    args = argparse.Namespace(action="sync", project="test_proj", dry_run=False)
    code = handle_sync(args, None, temp_project)

    assert code == 0
    assert (temp_project / ".opencode" / "agents" / "worker.md").exists()
    assert (temp_project / ".opencode" / "tools" / "fact_search.ts").exists()
    assert (temp_project / ".opencode" / "tools" / "vibe_check.ts").exists()
    assert (temp_project / ".opencode" / "opencode.json").exists()


def test_handle_sync_merge_preserving_and_backup(temp_project: Path):
    """Pilier 1 & 4 - Nominal & Préservation : fusion sans perte de clés personnalisées."""
    opencode_dir = temp_project / ".opencode"
    opencode_dir.mkdir(parents=True)
    cfg_file = opencode_dir / "opencode.json"
    cfg_file.write_text(
        json.dumps({"custom_plugin_key": "custom_value", "my_setting": 123}),
        encoding="utf-8",
    )

    args = argparse.Namespace(action="sync", project="test_proj", dry_run=False)
    code = handle_sync(args, None, temp_project)

    assert code == 0
    # Vérification du backup
    bak_file = opencode_dir / "opencode.json.bak"
    assert bak_file.exists()

    # Vérification de la fusion préservatrice
    new_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert new_cfg["custom_plugin_key"] == "custom_value"
    assert new_cfg["my_setting"] == 123
    assert "providers" in new_cfg
    assert "rules" in new_cfg


def test_handle_opencode_invalid_action(temp_project: Path):
    """Pilier 2 - Exception : Rejet d'une action CLI inconnue."""
    args = argparse.Namespace(action="invalid_action", project="test_proj")
    code = handle_opencode(args, None, temp_project)
    assert code == 1
