"""Contrats dual-context de swarm.py + codes de sortie de safe_run_entrypoint (MLOOP-105-BE)."""

import pytest

from src.swarm import resolve_project_name, get_project_context, root_dir
from src.core.safe_exec import safe_run_entrypoint


@pytest.fixture(autouse=True)
def _no_stdio_rewrap(monkeypatch):
    # setup_utf8_environment est orthogonale aux contrats testés (exit codes)
    # et pollute pytest-capture : neutralisée en test.
    monkeypatch.setattr("src.core.safe_exec.setup_utf8_environment", lambda: None)


def _boom():
    raise ValueError("simulated CLI failure")


def _interrupt():
    raise KeyboardInterrupt


class TestDualContextResolution:
    def test_resolve_from_foreign_cwd_falls_back_to_framework_root(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        assert resolve_project_name("mLoop") == "mLoop"

    def test_get_project_context_is_framework_anchored(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        state, project_path = get_project_context("mLoop")
        assert project_path == root_dir / "Projects" / "mLoop"
        assert state.project_name == "mLoop"
        # ecriture SSOT globale ancrée : aucun memory/active_project.json parasite dans le cwd
        assert not (tmp_path / "memory" / "active_project.json").exists()

    def test_resolve_unknown_project_still_raises(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            resolve_project_name("projet_totalement_inexistant_xyz_140")

    def test_resolve_from_root_cwd_unchanged(self):
        # regression baseline : resolution depuis la racine framework (cwd natif des tests)
        assert resolve_project_name("mLoop") == "mLoop"


class TestSafeEntrypointExitCodes:
    def test_exception_exits_nonzero(self):
        with pytest.raises(SystemExit) as exc:
            safe_run_entrypoint(_boom)
        assert exc.value.code == 1

    def test_keyboard_interrupt_exits_130(self):
        with pytest.raises(SystemExit) as exc:
            safe_run_entrypoint(_interrupt)
        assert exc.value.code == 130
