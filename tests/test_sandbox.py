import pytest
from pathlib import Path
from src.engine.sandbox import SandboxRunner, SandboxMode, SandboxExecutionError


def test_sandbox_path_writability():
    runner = SandboxRunner(workspace_root=Path("C:/MyProject"), mode=SandboxMode.WORKSPACE_WRITE)
    
    # Dans le workspace -> Writable
    assert runner.is_path_writable(Path("C:/MyProject/docs/spec.md")) is True
    
    # Hors du workspace -> Non writable
    assert runner.is_path_writable(Path("C:/Windows/System32/config")) is False


def test_sandbox_read_only_mode():
    runner = SandboxRunner(workspace_root=Path("C:/MyProject"), mode=SandboxMode.READ_ONLY)
    assert runner.is_path_writable(Path("C:/MyProject/docs/spec.md")) is False


def test_sandbox_command_env_building():
    runner = SandboxRunner(workspace_root=Path("C:/MyProject"), mode=SandboxMode.READ_ONLY)
    cmd, env = runner.build_command(["python", "--version"])
    assert env.get("MLOOP_SANDBOX_MODE") == "read-only"
    assert env.get("MLOOP_SANDBOX_NETWORK_DISABLED") == "1"
