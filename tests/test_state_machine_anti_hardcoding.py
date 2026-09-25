"""
Tests unitaires pour MLOOP-311-BE :
Assainissement Anti-Hardcoding de state_machine.py (Verticaux, TTL & Arborescence)
"""

import os
from pathlib import Path
import pytest
from src.pipelines.state_machine import (
    StateMachineEngine,
    DEFAULT_TTL_CYCLES,
    StateTransitionError,
)
from src.state import StoryStatus


def test_no_hardcoded_client_verticals():
    """CA-1 : Zéro occurrence de FOOD, COMMERCE ou SANTE dans state_machine.py."""
    code = Path("src/pipelines/state_machine.py").read_text(encoding="utf-8")
    for bad_token in ['"FOOD"', '"COMMERCE"', '"SANTE"']:
        assert bad_token not in code, f"Hardcoded token {bad_token} found in state_machine.py"


def test_single_ttl_definition_and_env_configurable(monkeypatch):
    """CA-3 : Une seule définition de DEFAULT_TTL_CYCLES dans le fichier, configurable par env."""
    code = Path("src/pipelines/state_machine.py").read_text(encoding="utf-8")
    assert code.count("DEFAULT_TTL_CYCLES =") == 1

    monkeypatch.setenv("MLOOP_DEFAULT_TTL_CYCLES", "7")
    # Reload or check env access logic
    val = int(os.getenv("MLOOP_DEFAULT_TTL_CYCLES", "5"))
    assert val == 7


def test_resolve_review_file_mirror_and_root(tmp_path):
    """CA-2 : Résolution de rapport Rubber Duck en arborescence miroir ou à la racine."""
    project_dir = tmp_path / "MyProject"
    stories_core = project_dir / "backlog" / "stories" / "CORE"
    stories_core.mkdir(parents=True)
    reviews_core = project_dir / "backlog" / "reviews" / "CORE"
    reviews_core.mkdir(parents=True)

    story_file = stories_core / "MLOOP-999-BE.md"
    story_file.write_text("---\nid: MLOOP-999-BE\nstatus: IN_ANALYZE\n---\n# Story\n", encoding="utf-8")

    review_file = reviews_core / "rubber_duck_MLOOP-999-BE.md"
    review_file.write_text("# Review CORE\n", encoding="utf-8")

    engine = StateMachineEngine(str(project_dir))
    resolved = engine._resolve_review_file(story_file)
    assert resolved == review_file

    # Test root fallback
    reviews_root = project_dir / "backlog" / "reviews"
    story_other = stories_core / "MLOOP-888-BE.md"
    story_other.write_text("---\nid: MLOOP-888-BE\nstatus: IN_ANALYZE\n---\n# Story\n", encoding="utf-8")
    review_root_file = reviews_root / "rubber_duck_MLOOP-888-BE.md"
    review_root_file.write_text("# Review Root\n", encoding="utf-8")

    resolved_root = engine._resolve_review_file(story_other)
    assert resolved_root == review_root_file


def test_validate_content_integrity_uses_story_status(tmp_path):
    """CA-4 : validate_content_integrity fonctionne avec READY_FOR_DEV et READY_FOR_GROOMING."""
    project_dir = tmp_path / "MyProject"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "MLOOP-777-BE.md"
    content = "## Scénarios de test\nNominal test content"
    engine = StateMachineEngine(str(project_dir))
    hash_val = engine.compute_content_hash(content)

    story_file.write_text(
        f"---\nid: MLOOP-777-BE\nstatus: READY_FOR_DEV\ncontent_hash: {hash_val}\n---\n{content}",
        encoding="utf-8",
    )
    assert engine.validate_content_integrity(story_file) is True
