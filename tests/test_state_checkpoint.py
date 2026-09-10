import time
from pathlib import Path
from src.state import LoopState, ProjectMode, LoopPhase, SavepointManager

def test_savepoint_manager_lifecycle(tmp_path):
    # Test directory creation and saving
    proj_dir = tmp_path / "test_proj"
    state_dict = {"project_name": "test_proj", "current_phase": "spec"}
    
    cp1 = SavepointManager.save_checkpoint(state_dict, project_path=proj_dir, reason="step_1")
    assert cp1.exists()
    assert "checkpoint_" in cp1.name
    
    # Test loading
    loaded = SavepointManager.load_latest_checkpoint(project_path=proj_dir)
    assert loaded is not None
    assert loaded["project_name"] == "test_proj"
    assert loaded["current_phase"] == "spec"
    
    # Test FIFO pruning (MAX_RETAINED = 3)
    time.sleep(0.01)
    cp2 = SavepointManager.save_checkpoint(state_dict, project_path=proj_dir, reason="step_2")
    time.sleep(0.01)
    cp3 = SavepointManager.save_checkpoint(state_dict, project_path=proj_dir, reason="step_3")
    time.sleep(0.01)
    cp4 = SavepointManager.save_checkpoint(state_dict, project_path=proj_dir, reason="step_4")
    
    cps = SavepointManager.list_checkpoints(project_path=proj_dir)
    assert len(cps) == 3
    assert not cp1.exists()  # Oldest pruned
    assert cp4.exists()

def test_loop_state_in_flight_checkpointing(tmp_path):
    proj_dir = tmp_path / "test_proj"
    state = LoopState(project_name="test_proj", project_mode=ProjectMode.MLOOP)
    
    # Initially should not checkpoint if interval is 60s
    state.checkpoint_interval_seconds = 60
    assert not state.should_checkpoint()
    
    # Force checkpoint
    saved = state.checkpoint(project_path=proj_dir, force=True, reason="forced_test")
    assert saved is not None
    assert saved.exists()
    
    # Simulate time passing > 60s
    state.last_checkpoint_timestamp = time.time() - 65
    assert state.should_checkpoint()
    
    # Automatic checkpoint when should_checkpoint is true
    saved_auto = state.checkpoint(project_path=proj_dir, force=False, reason="timed_test")
    assert saved_auto is not None
    assert saved_auto.exists()
    
    # Mutate state and test restore
    state.current_phase = LoopPhase.PLAN
    state.jira_project_key = "MUTATED"
    
    restored = state.restore_latest_checkpoint(project_path=proj_dir)
    assert restored is True
    # Restored to spec
    assert state.current_phase == LoopPhase.SPEC
    assert state.jira_project_key is None
