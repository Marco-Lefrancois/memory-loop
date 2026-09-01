# -*- coding: utf-8 -*-
"""
Rubber Duck 2.0 Engine (mLoop Core - Devil's Advocate Architecture).

Expose les interfaces canoniques de revue contradictoire, d'analyse de cohérence
cross-récits et de remédiation chirurgicale de User Stories.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any, List

from src.engine.rubber_duck.coherence import CrossStoryCoherenceChecker, CoherenceIssue
from src.engine.rubber_duck.remediator import RubberDuckRemediator, RemediationPatch
from src.engine.rubber_duck.critic import DevilAdvocateCritic, DevilAdvocateCritique


class RubberDuckEngine:
    """Moteur canonique d'Avocat du Diable pour les User Stories."""

    @classmethod
    def evaluate_file(
        cls,
        target_file: Path | str,
        project_name: Optional[str] = None,
        project_dir: Optional[Path] = None,
        persist_evidence: bool = True,
    ) -> DevilAdvocateCritique:
        """Exécute l'audit contradictoire approfondi de fond sur un récit."""
        path_obj = Path(target_file)
        p_name = project_name or (project_dir.name if project_dir else "current_project")
        return DevilAdvocateCritic.evaluate_story(
            story_file=path_obj,
            project_name=p_name,
            project_dir=project_dir,
            persist_evidence=persist_evidence,
        )


def evaluate_story_critique(
    story_file: Path | str,
    project_name: str,
    project_dir: Optional[Path] = None,
    persist_evidence: bool = True,
) -> DevilAdvocateCritique:
    """Interface canonique d'évaluation contradictoire."""
    return RubberDuckEngine.evaluate_file(
        target_file=story_file,
        project_name=project_name,
        project_dir=project_dir,
        persist_evidence=persist_evidence,
    )


__all__ = [
    "RubberDuckEngine",
    "evaluate_story_critique",
    "DevilAdvocateCritic",
    "DevilAdvocateCritique",
    "CrossStoryCoherenceChecker",
    "CoherenceIssue",
    "RubberDuckRemediator",
    "RemediationPatch",
]
