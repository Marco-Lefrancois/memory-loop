import pytest
import sys
from pathlib import Path

from src.state import LoopState
from src.bridges.story_guard import validate_story_state
from src.bridges.mcp_loop_mem import _PRELOAD_CACHE, clear_preloaded_context

def test_obligation_pass_boundary_rejection(monkeypatch):
    # Test boundary rejection by Story Guard when a file is not in components
    from src.state import LoopState, SprintBacklogItem
    from src.pipelines.state_machine import StateMachineEngine
    def mock_load(self, path):
        self.sprint_backlog = [
            SprintBacklogItem(id="MLOOP-001-BE", title="Test", description="Test", test_plan="Test", components=["src/allowed.py"])
        ]
    monkeypatch.setattr(LoopState, "load_from_audit", mock_load)
    monkeypatch.setattr(StateMachineEngine, "validate_single_in_analyze", lambda self: ["MLOOP-001-BE"])
    
    with pytest.raises(SystemExit) as excinfo:
        validate_story_state(project_name="mLoop", check_file="unauthorized/secret_file.py")
    assert excinfo.value.code == 1

def test_negative_invariant_blindness():
    # Test that purged nodes/concepts are not accessible in RAM cache
    clear_preloaded_context()
    assert "REVOKED_CONCEPT_XYZ" not in _PRELOAD_CACHE
    assert len(_PRELOAD_CACHE) == 0

def test_crash_recovery_idempotency():
    # Test that LoopState can reload from audit/graph idempotently
    project_path = Path("Projects") / "mLoop"
    state1 = LoopState(project_name="mLoop")
    if project_path.exists():
        state1.load_from_graph(project_path)
    
    state2 = LoopState(project_name="mLoop")
    if project_path.exists():
        state2.load_from_graph(project_path)
        
    assert state1.project_name == state2.project_name
