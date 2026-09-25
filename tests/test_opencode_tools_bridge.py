# -*- coding: utf-8 -*-
"""
Tests unitaires pour MLOOP-251-BE : Bridge d'Outils Natifs TypeScript OpenCode.
Conforme ADR-0202 (<=300L) et 4 Piliers Gherkin.
"""

from pathlib import Path
import pytest
from src.bridges.opencode.tools_bridge import OpenCodeToolsBridge


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Espace temporaire pour tester le déploiement d'outils."""
    (tmp_path / ".opencode").mkdir(parents=True)
    return tmp_path


def test_generate_fact_search_tool_content():
    """Pilier 1 - Nominal : génération du code TypeScript fact_search.ts."""
    bridge = OpenCodeToolsBridge()
    content = bridge.generate_fact_search_ts()

    assert "export default tool({" in content or "tool(" in content
    assert "fact_search" in content
    assert "query" in content
    assert "python" in content
    assert "swarm.py" in content
    assert "fact-search" in content


def test_generate_vibe_check_tool_content():
    """Pilier 1 - Nominal : génération du code TypeScript vibe_check.ts."""
    bridge = OpenCodeToolsBridge()
    content = bridge.generate_vibe_check_ts()

    assert "vibe_check" in content
    assert "vibe-check" in content
    assert "fast" in content
    assert "TIMEOUT" in content or "timeout" in content


def test_deploy_tools_idempotent(temp_workspace: Path):
    """Pilier 1 & 4 - Nominal & Idempotence : écriture idempotente dans .opencode/tools/."""
    bridge = OpenCodeToolsBridge(workspace_root=temp_workspace)
    res1 = bridge.deploy_tools()

    assert res1["deployed"] == 2
    assert res1["skipped"] == 0

    fact_ts = temp_workspace / ".opencode" / "tools" / "fact_search.ts"
    vibe_ts = temp_workspace / ".opencode" / "tools" / "vibe_check.ts"
    assert fact_ts.exists()
    assert vibe_ts.exists()

    # Deuxième exécution sans modification
    res2 = bridge.deploy_tools()
    assert res2["deployed"] == 0
    assert res2["skipped"] == 2


def test_check_tools_installed(temp_workspace: Path):
    """Pilier 2 - Exception : détection de présence / absence des outils."""
    bridge = OpenCodeToolsBridge(workspace_root=temp_workspace)
    assert bridge.check_tools_installed() is False

    bridge.deploy_tools()
    assert bridge.check_tools_installed() is True

    # Suppression d'un outil
    (temp_workspace / ".opencode" / "tools" / "fact_search.ts").unlink()
    assert bridge.check_tools_installed() is False


def test_custom_target_directory(tmp_path: Path):
    """Pilier 3 - Résilience : déploiement dans un répertoire personnalisé."""
    custom_dir = tmp_path / "custom_tools"
    bridge = OpenCodeToolsBridge(target_dir=custom_dir)
    res = bridge.deploy_tools()

    assert res["deployed"] == 2
    assert (custom_dir / "fact_search.ts").exists()
    assert (custom_dir / "vibe_check.ts").exists()
