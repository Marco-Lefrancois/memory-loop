# -*- coding: utf-8 -*-
"""
Tests unitaires pour MLOOP-250-BE : Parité Miroir des Personas OpenCode.
Conforme ADR-0202 (<=300L) et 4 Piliers Gherkin.
"""

from pathlib import Path
import pytest
from src.bridges.opencode.mirror_sync import PersonasSyncEngine, PersonasSyncError


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Crée un espace de travail temporaire avec agents mLoop canoniques."""
    agents_dir = tmp_path / ".agents" / "agents"
    agents_dir.mkdir(parents=True)

    # Worker (Craftsman)
    (agents_dir / "worker.md").write_text(
        """---
name: worker
role: Implementation Worker
description: Agent d'implémentation physique
skills:
  - incremental-implementation
  - test-driven-development
---
# MISSION
Tu es l'agent Worker.""",
        encoding="utf-8",
    )

    # Explorer (avec canary interdit)
    (agents_dir / "explorer.md").write_text(
        """---
name: explorer
role: Knowledge Cartographer
description: Cartographe de l'information brute
skills:
  - fact-search
  - graphify
  - forbidden-skill-canary
---
# MISSION
Tu es l'agent Explorer.""",
        encoding="utf-8",
    )

    # Critic
    (agents_dir / "critic.md").write_text(
        """---
name: critic
role: Quality Reviewer
description: Relecteur contradictoire
skills:
  - code-review
---
# MISSION
Tu es le critique.""",
        encoding="utf-8",
    )

    return tmp_path


def test_parse_agent_manifest_valid(temp_workspace: Path):
    """Pilier 1 - Nominal : parsing correct du frontmatter et du corps."""
    engine = PersonasSyncEngine(workspace_root=temp_workspace)
    worker_file = temp_workspace / ".agents" / "agents" / "worker.md"
    parsed = engine.parse_agent_manifest(worker_file)

    assert parsed["name"] == "worker"
    assert parsed["role"] == "Implementation Worker"
    assert "incremental-implementation" in parsed["skills"]
    assert "Tu es l'agent Worker." in parsed["body"]


def test_render_primary_and_subagent_roles(temp_workspace: Path):
    """Pilier 1 - Nominal : craftsman/worker en primary, autres en subagent."""
    engine = PersonasSyncEngine(workspace_root=temp_workspace)

    worker_meta = {
        "name": "worker",
        "role": "Worker",
        "description": "Implementation",
        "skills": ["tdd"],
        "body": "Body Worker",
    }
    rendered_worker = engine.render_opencode_agent(worker_meta)
    assert "mode: primary" in rendered_worker
    assert "subagent_depth" not in rendered_worker

    critic_meta = {
        "name": "critic",
        "role": "Critic",
        "description": "Review",
        "skills": ["review"],
        "body": "Body Critic",
    }
    rendered_critic = engine.render_opencode_agent(critic_meta)
    assert "mode: subagent" in rendered_critic
    assert "subagent_depth: 1" in rendered_critic


def test_confinement_strips_forbidden_skills(temp_workspace: Path):
    """Pilier 3 - Résilience : la compétence forbidden-skill-canary est filtrée."""
    engine = PersonasSyncEngine(workspace_root=temp_workspace)
    explorer_file = temp_workspace / ".agents" / "agents" / "explorer.md"
    parsed = engine.parse_agent_manifest(explorer_file)
    rendered = engine.render_opencode_agent(parsed)

    assert "forbidden-skill-canary" not in rendered
    assert "fact-search" in rendered
    assert "graphify" in rendered


def test_sync_all_creates_files_idempotently(temp_workspace: Path):
    """Pilier 1 & 4 - Nominal & Idempotence : création et idempotence."""
    engine = PersonasSyncEngine(workspace_root=temp_workspace)
    res1 = engine.sync_all()

    assert res1["synced"] == 3
    assert res1["skipped"] == 0
    assert (temp_workspace / ".opencode" / "agents" / "worker.md").exists()
    assert (temp_workspace / ".opencode" / "agents" / "explorer.md").exists()
    assert (temp_workspace / ".opencode" / "agents" / "critic.md").exists()

    # Deuxième passe sans changement -> skipped
    res2 = engine.sync_all()
    assert res2["synced"] == 0
    assert res2["skipped"] == 3


def test_check_mirror_parity_detects_missing(temp_workspace: Path):
    """Pilier 2 - Exception : détection de désynchronisation miroir."""
    engine = PersonasSyncEngine(workspace_root=temp_workspace)
    engine.sync_all()

    is_sync, missing = engine.check_mirror_parity()
    assert is_sync is True
    assert len(missing) == 0

    # Suppression d'un agent miroir
    (temp_workspace / ".opencode" / "agents" / "critic.md").unlink()
    is_sync_after, missing_after = engine.check_mirror_parity()
    assert is_sync_after is False
    assert "critic" in missing_after


def test_corrupted_manifest_handled_gracefully(temp_workspace: Path):
    """Pilier 2 - Exception : gestion défensive des fichiers corrompus."""
    corrupt_file = temp_workspace / ".agents" / "agents" / "corrupt.md"
    corrupt_file.write_text("No frontmatter here at all", encoding="utf-8")

    engine = PersonasSyncEngine(workspace_root=temp_workspace)
    res = engine.sync_all()

    assert "corrupt.md" in res["errors"]
    assert res["synced"] == 3  # Les 3 autres sont synchronisés sans problème
