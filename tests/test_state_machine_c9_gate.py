"""
Tests TDD pour le Gate C9 (Dossier de Preuves) sur la Machine à États (Phase 2 —
Plan d'Implémentation Framework Enforcement Déterministe du Grounding Visuel & Épistémique).

Décision actée avec le PO : le gate est en WARNING pendant la période de transition
(ne bloque pas les stories existantes déjà READY_FOR_DEV sans dossier), et devient
BLOCKING uniquement en mode strict=True (CI/audit explicite).
"""

import pytest
from pathlib import Path

from src.pipelines.state_machine import StateMachineEngine, StateTransitionError


def _write_story(
    tmp_path: Path, status: str = "READY_FOR_DEV", story_id: str = "US-01-TEST"
) -> Path:
    project_dir = tmp_path / "TestProjectGate"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    story_file = stories_dir / f"{story_id}.md"
    story_file.write_text(
        f"""---
id: {story_id}
status: {status}
---
# Story de Test

## Scénarios de test
""",
        encoding="utf-8",
    )
    return story_file


def test_c9_gate_warning_when_dossier_missing_non_strict(tmp_path, capsys):
    """Mode non-strict (défaut) : dossier manquant -> WARNING affiché, aucune exception levée."""
    story_file = _write_story(tmp_path)
    engine = StateMachineEngine(str(story_file.parents[2]))

    result = engine.validate_fact_dossier_gate(story_file, strict=False)
    assert result is True  # Non bloquant : la transition peut continuer.


def test_c9_gate_blocking_when_dossier_missing_and_strict(tmp_path):
    """Mode strict=True : dossier manquant -> StateTransitionError levée (BLOCKING)."""
    story_file = _write_story(tmp_path)
    engine = StateMachineEngine(str(story_file.parents[2]))

    with pytest.raises(StateTransitionError, match="Dossier de Preuves"):
        engine.validate_fact_dossier_gate(story_file, strict=True)


def test_c9_gate_passes_when_dossier_exists(tmp_path):
    """Dossier de preuves présent sous memory/evidence/<STORY_ID>_fact_dossier.md -> passe même en strict."""
    story_file = _write_story(tmp_path)
    project_dir = story_file.parents[2]
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "US-01-TEST_fact_dossier.md").write_text(
        "# Dossier de Preuves\n", encoding="utf-8"
    )

    engine = StateMachineEngine(str(project_dir))
    result = engine.validate_fact_dossier_gate(story_file, strict=True)
    assert result is True


def test_c9_gate_only_applies_to_ready_statuses(tmp_path):
    """Un récit en IN_ANALYZE (hors périmètre du gate) ne doit jamais lever, même en strict."""
    story_file = _write_story(tmp_path, status="IN_ANALYZE")
    engine = StateMachineEngine(str(story_file.parents[2]))

    result = engine.validate_fact_dossier_gate(story_file, strict=True)
    assert result is True
