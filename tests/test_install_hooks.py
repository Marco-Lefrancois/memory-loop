"""Suite de tests unitaires pour MLOOP-105-BE : Garde-Fou Cryptographique et
Hook Pre-Commit Déterministe (install-hooks / uninstall-hooks).

Couvre : installation, idempotence, désinstallation, contenu du hook généré
(dispatch code-check / struct-check, bypass souverain) et mode dégradé non-Git.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.commands.handlers.project import handle_install_hooks


def _make_args(uninstall: bool = False) -> argparse.Namespace:
    return argparse.Namespace(uninstall=uninstall)


def _make_state(project_name: str = "mLoop") -> SimpleNamespace:
    return SimpleNamespace(project_name=project_name)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Simule une racine de dépôt Git valide."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


class TestInstallHooks:
    """Scénarios Gherkin : installation idempotente et contenu du hook."""

    def test_install_creates_executable_hook(self, git_repo: Path) -> None:
        rc = handle_install_hooks(_make_args(), _make_state(), git_repo)
        assert rc == 0
        hook = git_repo / ".git" / "hooks" / "pre-commit"
        assert hook.exists()
        content = hook.read_text(encoding="utf-8")
        assert "code-check" in content
        assert "struct-check" in content
        assert "git diff --cached" in content
        assert "MLOOP_SKIP_HOOKS" in content

    def test_install_is_idempotent(self, git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert handle_install_hooks(_make_args(), _make_state(), git_repo) == 0
        assert handle_install_hooks(_make_args(), _make_state(), git_repo) == 0
        out = capsys.readouterr().out
        hook = git_repo / ".git" / "hooks" / "pre-commit"
        assert hook.exists()
        assert "pre-commit" in out

    def test_install_fails_gracefully_without_git(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.commands.handlers.project._FRAMEWORK_ROOT", tmp_path / "no_git_root")
        no_git = tmp_path / "project_no_git"
        no_git.mkdir()
        rc = handle_install_hooks(_make_args(), _make_state(), no_git)
        assert rc == 1
        assert not (no_git / ".git" / "hooks" / "pre-commit").exists()

    def test_install_does_not_clobber_foreign_hook(self, git_repo: Path) -> None:
        hook = git_repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho foreign\n", encoding="utf-8")
        rc = handle_install_hooks(_make_args(), _make_state(), git_repo)
        assert rc == 1
        assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho foreign\n"


class TestUninstallHooks:
    """Désinstallation souveraine du garde-fou."""

    def test_uninstall_removes_managed_hook(self, git_repo: Path) -> None:
        assert handle_install_hooks(_make_args(), _make_state(), git_repo) == 0
        rc = handle_install_hooks(_make_args(uninstall=True), _make_state(), git_repo)
        assert rc == 0
        assert not (git_repo / ".git" / "hooks" / "pre-commit").exists()

    def test_uninstall_refuses_to_remove_foreign_hook(self, git_repo: Path) -> None:
        hook = git_repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho foreign\n", encoding="utf-8")
        rc = handle_install_hooks(_make_args(uninstall=True), _make_state(), git_repo)
        assert rc == 1
        assert hook.exists()

    def test_uninstall_noop_when_absent(self, git_repo: Path) -> None:
        rc = handle_install_hooks(_make_args(uninstall=True), _make_state(), git_repo)
        assert rc == 0
