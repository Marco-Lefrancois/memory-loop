"""
Tests pytest pour le garde-fou anti-aggravation RULE-AST-01-DELTA (MLOOP-171-BE / OQ-171-02).

Couvre les 4 Piliers Gherkin :
  Pilier 1 — Nominal   : fichier déjà >300L qui RÉTRÉCIT ou reste neutre → PASS
  Pilier 2 — Rejet     : fichier déjà >300L qui GROSSIT → FAIL | conforme→>300L → FAIL
  Pilier 3 — Résilience : fallback sans git (fichier nouveau) | CodeGraph indispo → méthode annotée
  Pilier 4 — Audit MLOOP_SKIP_HOOKS : bypass → exit 0 + ligne d'audit écrite

ADR-0369 : parametrize sur les cas limites, aucun except silencieux.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest

from src.pipelines.ast_delta_checker import (
    MAX_BYTES,
    MAX_LINES,
    DeltaResult,
    GitRunner,
    check_staged_file_delta,
    record_skip_hooks_audit,
)


# ─── Fixtures & helpers ───────────────────────────────────────────────────────


def _make_py_file(lines: int, tmp_path: Path, name: str = "module.py") -> Path:
    """Crée un fichier Python factice avec `lines` lignes physiques."""
    p = tmp_path / name
    content = "\n".join(f"# ligne {i}" for i in range(lines))
    p.write_text(content, encoding="utf-8")
    return p


class _FakeGitRunner:
    """GitRunner injectable retournant un contenu HEAD contrôlé."""

    def __init__(self, head_lines: Optional[int]) -> None:
        # None → fichier inconnu de HEAD (nouveau)
        self._head_lines = head_lines

    def show_head(self, filepath: str, root: Path) -> Optional[str]:
        if self._head_lines is None:
            return None
        return "\n".join(f"# ligne {i}" for i in range(self._head_lines))


# ─── PILIER 1 — Chemin Nominal ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "head_l,staged_l",
    [
        (400, 390),  # Réduit : HEAD 400 → stagé 390 ✓
        (400, 400),  # Neutre : HEAD 400 → stagé 400 ✓
        (301, 300),  # Réduit juste sous le plafond ✓
    ],
)
def test_delta_oversized_shrinks_or_neutral_is_pass(head_l, staged_l, tmp_path):
    """Fichier déjà >300L en HEAD qui rétrécit ou reste identique → delta_ok=True."""
    staged = _make_py_file(staged_l, tmp_path)
    runner = _FakeGitRunner(head_lines=head_l)

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is True, (
        f"Attendu PASS pour HEAD={head_l}→staged={staged_l}: {result.violation_reason}"
    )
    assert result.is_already_oversized is True
    assert result.violation_reason is None


def test_delta_compliant_file_stays_compliant_is_pass(tmp_path):
    """Fichier conforme en HEAD qui reste conforme → PASS."""
    staged = _make_py_file(150, tmp_path)
    runner = _FakeGitRunner(head_lines=150)

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is True
    assert result.is_already_oversized is False


# ─── PILIER 2 — Exceptions & Rejets ──────────────────────────────────────────


@pytest.mark.parametrize(
    "head_l,staged_l",
    [
        (400, 401),  # Grossit de 1 ligne → rejet
        (400, 500),  # Grossit massivement → rejet
        (301, 310),  # Légèrement au-dessus, grossit encore → rejet
    ],
)
def test_delta_oversized_grows_is_fail(head_l, staged_l, tmp_path):
    """Fichier déjà >300L en HEAD qui grossit → delta_ok=False avec RULE-AST-01-DELTA."""
    staged = _make_py_file(staged_l, tmp_path)
    runner = _FakeGitRunner(head_lines=head_l)

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is False
    assert result.violation_reason is not None
    assert "RULE-AST-01-DELTA" in result.violation_reason
    assert result.is_already_oversized is True


def test_delta_compliant_becomes_oversized_is_fail(tmp_path):
    """Fichier conforme en HEAD qui passe >300L après staging → FAIL (comportement standard)."""
    staged = _make_py_file(MAX_LINES + 5, tmp_path)
    runner = _FakeGitRunner(head_lines=200)  # conforme en HEAD

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is False
    assert result.violation_reason is not None
    assert "RULE-AST-01" in result.violation_reason
    assert result.is_already_oversized is False


def test_delta_new_file_oversized_is_fail(tmp_path):
    """Nouveau fichier (HEAD=None) qui démarre déjà >300L → FAIL."""
    staged = _make_py_file(MAX_LINES + 10, tmp_path)
    runner = _FakeGitRunner(head_lines=None)  # fichier nouveau

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is False
    assert result.head_lines is None


# ─── PILIER 3 — Résilience & mode dégradé ────────────────────────────────────


def test_delta_new_file_compliant_is_pass(tmp_path):
    """Nouveau fichier (HEAD=None) conforme → PASS, méthode annotée ast_line_count."""
    staged = _make_py_file(100, tmp_path)
    runner = _FakeGitRunner(head_lines=None)

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is True
    assert result.head_lines is None
    assert result.method == "ast_line_count"


def test_delta_git_unavailable_fallback(tmp_path, monkeypatch):
    """
    Si git est indisponible (DefaultGitRunner retourne None) → fichier traité
    comme nouveau, méthode annotée ast_line_count — pas de crash.
    (Pilier 3 / OQ-171-03 fallback déterministe)
    """
    import subprocess as _sp

    staged = _make_py_file(200, tmp_path)

    # Simule git absent en patchant subprocess.run pour lever FileNotFoundError
    original_run = _sp.run

    def _no_git(*args, **kwargs):
        if args and isinstance(args[0], list) and args[0][0] == "git":
            raise FileNotFoundError("git not found")
        return original_run(*args, **kwargs)

    monkeypatch.setattr(_sp, "run", _no_git)

    from src.pipelines.ast_delta_checker import DefaultGitRunner

    runner = DefaultGitRunner()
    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    # Fichier conforme (200L) et git absent → traité comme nouveau conforme → PASS
    assert result.delta_ok is True
    assert result.head_lines is None


# ─── PILIER 4 — Audit MLOOP_SKIP_HOOKS ───────────────────────────────────────


def test_skip_hooks_audit_writes_log(tmp_path, monkeypatch):
    """MLOOP_SKIP_HOOKS=1 → ligne horodatée écrite dans mloop_skip_hooks_audit.log."""
    monkeypatch.setenv("MLOOP_SKIP_HOOKS", "1")
    monkeypatch.setenv("MLOOP_SKIP_HOOKS_REASON", "test urgence pilier-4")
    monkeypatch.setenv("USERNAME", "pytest_user")

    # Rediriger le chemin d'audit vers tmp_path
    audit_rel = "Projects/mLoop/memory/evidence/mloop_skip_hooks_audit.log"
    audit_path = tmp_path / audit_rel
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    import src.pipelines.ast_delta_checker as _mod

    original_rel = _mod._AUDIT_LOG_REL
    monkeypatch.setattr(_mod, "_AUDIT_LOG_REL", audit_rel)

    record_skip_hooks_audit(tmp_path)

    monkeypatch.setattr(_mod, "_AUDIT_LOG_REL", original_rel)

    assert audit_path.exists(), "Le fichier d'audit doit être créé"
    content = audit_path.read_text(encoding="utf-8")
    assert "MLOOP_SKIP_HOOKS=1" in content
    assert "test urgence pilier-4" in content
    assert "pytest_user" in content


def test_skip_hooks_audit_no_env_does_not_write(tmp_path, monkeypatch):
    """Sans MLOOP_SKIP_HOOKS → aucun fichier d'audit créé."""
    monkeypatch.delenv("MLOOP_SKIP_HOOKS", raising=False)

    import src.pipelines.ast_delta_checker as _mod

    audit_rel = "Projects/mLoop/memory/evidence/mloop_skip_hooks_audit_absent.log"
    monkeypatch.setattr(_mod, "_AUDIT_LOG_REL", audit_rel)

    record_skip_hooks_audit(tmp_path)

    assert not (tmp_path / audit_rel).exists()


@pytest.mark.parametrize("skip_val", ["1", "true", "True", "yes", "YES"])
def test_skip_hooks_audit_all_bypass_values(skip_val, tmp_path, monkeypatch):
    """Toutes les valeurs de bypass reconnues → audit écrit."""
    monkeypatch.setenv("MLOOP_SKIP_HOOKS", skip_val)
    monkeypatch.delenv("MLOOP_SKIP_HOOKS_REASON", raising=False)

    import src.pipelines.ast_delta_checker as _mod

    audit_rel = f"Projects/mLoop/memory/evidence/mloop_skip_hooks_{skip_val}.log"
    (tmp_path / audit_rel).parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_mod, "_AUDIT_LOG_REL", audit_rel)

    record_skip_hooks_audit(tmp_path)

    assert (tmp_path / audit_rel).exists(), f"Audit non écrit pour MLOOP_SKIP_HOOKS={skip_val}"


# ─── Cas limites supplémentaires (ADR-0369 parametrize) ──────────────────────


@pytest.mark.parametrize(
    "head_l,staged_l,expect_ok",
    [
        (300, 300, True),  # Exactement au seuil → conforme (300 = OK)
        (300, 301, False),  # Conforme HEAD, 301 staged → rejet standard
        (301, 301, True),  # Déjà >300, neutre → OK
        (301, 302, False),  # Déjà >300, grossit → rejet DELTA
        (299, 301, False),  # Conforme HEAD (299), dépasse en staging → rejet standard
    ],
)
def test_delta_boundary_cases(head_l, staged_l, expect_ok, tmp_path):
    """Cas limites autour du seuil 300L (ADR-0369 parametrize)."""
    staged = _make_py_file(staged_l, tmp_path, name=f"mod_{head_l}_{staged_l}.py")
    runner = _FakeGitRunner(head_lines=head_l)

    result = check_staged_file_delta(staged, tmp_path, git_runner=runner)

    assert result.delta_ok is expect_ok, (
        f"HEAD={head_l} staged={staged_l}: attendu delta_ok={expect_ok}, "
        f"obtenu {result.delta_ok} — {result.violation_reason}"
    )
