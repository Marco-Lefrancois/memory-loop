"""
Tests pour le calcul du Task Graph et de la Frontier Herdr (implement-spec).
"""
import pytest
from pathlib import Path
from src.pipelines.task_graph import TaskGraph, get_ready_frontier


def test_task_graph_frontier_calculation(tmp_path):
    """Vérifie le calcul exact du DAG et de la Frontier des User Stories débloquées."""
    stories_dir = tmp_path / "stories"
    stories_dir.mkdir(parents=True)

    # Story 1 : Racine terminée
    (stories_dir / "US-001.md").write_text("""# US-001 : Base Database
Statut : DONE
""", encoding="utf-8")

    # Story 2 : Prête car dépend uniquement de US-001
    (stories_dir / "US-002.md").write_text("""# US-002 : Auth API
Statut : TODO
Blocked-By: US-001
""", encoding="utf-8")

    # Story 3 : Bloquée car dépend de US-002 (qui est TODO)
    (stories_dir / "US-003.md").write_text("""# US-003 : User Profile UI
Statut : TODO
Blocked-By: US-002
""", encoding="utf-8")

    # Story 4 : Indépendante et prête
    (stories_dir / "US-004.md").write_text("""# US-004 : Logging Framework
Statut : IN_PROGRESS
""", encoding="utf-8")

    graph = TaskGraph(tmp_path)
    graph.load_stories()
    frontier = graph.get_frontier()

    # La frontière doit contenir US-002 et US-004 (car US-001 est DONE, et US-003 attend US-002)
    assert "US-002" in frontier
    assert "US-004" in frontier
    assert "US-001" not in frontier  # Déjà DONE
    assert "US-003" not in frontier  # Bloquée par US-002
