"""
Unit tests for Story Guard physical write boundary and SCC verification (MLOOP-020-BE).
Conforme ADR-0369 et ADR-0381.
"""
import pytest
from pathlib import Path
from unittest.mock import patch
from src.bridges.story_guard import validate_story_state
from src.state import LoopState, SprintBacklogItem


def test_story_guard_nominal_authorized_file(tmp_path: Path, monkeypatch):
    """Vérifie que l'écriture d'un fichier conforme au SCC est autorisée sans erreur."""
    project_name = "TestProj"
    proj_dir = tmp_path / "Projects" / project_name
    (proj_dir / "graphify-out").mkdir(parents=True, exist_ok=True)
    (proj_dir / "graphify-out" / "graph.json").write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLOOP_ACTIVE_STORY_ID", "MLOOP-020-BE")

    test_item = SprintBacklogItem(
        id="MLOOP-020-BE",
        title="Story Guard",
        description="Confinement physique",
        components=["src/bridges", "tests"]
    )

    class MockLoopState:
        def __init__(self, project_name: str):
            self.project_name = project_name
            self.sprint_backlog = [test_item]

        def load_from_audit(self, p_path):
            pass

    with patch("src.bridges.story_guard.LoopState", MockLoopState), \
         patch("src.pipelines.state_machine.StateMachineEngine.validate_single_in_analyze", return_value=["MLOOP-020-BE"]):
        
        # Ne doit pas lever SystemExit
        validate_story_state(project_name, check_file="src/bridges/story_guard.py")


def test_story_guard_rejects_unauthorized_file(tmp_path: Path, monkeypatch):
    """Vérifie que l'écriture hors des composants SCC est interceptée avec code 1."""
    project_name = "TestProj"
    proj_dir = tmp_path / "Projects" / project_name
    (proj_dir / "graphify-out").mkdir(parents=True, exist_ok=True)
    (proj_dir / "graphify-out" / "graph.json").write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLOOP_ACTIVE_STORY_ID", "MLOOP-020-BE")

    test_item = SprintBacklogItem(
        id="MLOOP-020-BE",
        title="Story Guard",
        description="Confinement physique",
        components=["src/bridges"]
    )

    class MockLoopState:
        def __init__(self, project_name: str):
            self.project_name = project_name
            self.sprint_backlog = [test_item]

        def load_from_audit(self, p_path):
            pass

    with patch("src.bridges.story_guard.LoopState", MockLoopState), \
         patch("src.pipelines.state_machine.StateMachineEngine.validate_single_in_analyze", return_value=["MLOOP-020-BE"]):
        
        with pytest.raises(SystemExit) as exc_info:
            validate_story_state(project_name, check_file="src/core/lifecycle.py")
        assert exc_info.value.code == 1


def test_story_guard_bypass_when_no_components_declared(tmp_path: Path, monkeypatch):
    """Vérifie la tolérance lorsque la story n'impose pas de restriction SCC."""
    project_name = "TestProj"
    proj_dir = tmp_path / "Projects" / project_name
    (proj_dir / "graphify-out").mkdir(parents=True, exist_ok=True)
    (proj_dir / "graphify-out" / "graph.json").write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLOOP_ACTIVE_STORY_ID", "MLOOP-020-BE")

    test_item = SprintBacklogItem(
        id="MLOOP-020-BE",
        title="Story Guard",
        description="Confinement physique",
        components=[]
    )

    class MockLoopState:
        def __init__(self, project_name: str):
            self.project_name = project_name
            self.sprint_backlog = [test_item]

        def load_from_audit(self, p_path):
            pass

    with patch("src.bridges.story_guard.LoopState", MockLoopState), \
         patch("src.pipelines.state_machine.StateMachineEngine.validate_single_in_analyze", return_value=["MLOOP-020-BE"]):
        
        validate_story_state(project_name, check_file="src/anywhere/file.py")
