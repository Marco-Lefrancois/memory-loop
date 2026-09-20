# -*- coding: utf-8 -*-
"""
Tests unitaires du registre SSOT multi-runtimes des workers Herdr (ADR-0346).

Ground truth :
- opencode : one-shot via --yolo, pas de modèle par défaut (sémantique
  historique intangible) ;
- cline 3.0.62 : one-shot auto-apprové natif (pas de --yolo), sélection modèle
  -m/--model, binaire npm .exe requis sous Windows ;
- pi / omp : mode interactif historique (--dangerously-skip-permissions +
  --model) préservé à l'identique.
"""

from unittest.mock import patch

import pytest

from src.core.worker_runtimes import (
    DEFAULT_CLINE_MODEL,
    WORKER_RUNTIMES,
    WorkerRuntimeSpec,
    _resolve_npm_windows_binary,
    get_worker_runtime,
)


def test_registry_contains_core_runtimes():
    """OpenCode, Cline, pi et omp sont enregistrés comme runtimes workers."""
    assert {"opencode", "cline", "pi", "omp"}.issubset(WORKER_RUNTIMES)


def test_unknown_kind_raises_keyerror():
    """Un kind non enregistré lève KeyError avec la liste des runtimes valides."""
    with pytest.raises(KeyError) as excinfo:
        get_worker_runtime("runtime-inexistant")
    assert "opencode" in str(excinfo.value)


def test_opencode_one_shot_flags_historical_semantics():
    """OpenCode : --yolo seul, puis --model ajouté si absent (comportement historique)."""
    spec = get_worker_runtime("opencode")
    assert spec.build_flags() == ["--yolo"]
    assert spec.build_flags(model="nmedia_cloud/claude-opus-4.8") == [
        "--yolo",
        "--model",
        "nmedia_cloud/claude-opus-4.8",
    ]


def test_opencode_extra_args_merge_model():
    """OpenCode : extra_args explicites + modèle absent -> modèle ajouté après."""
    spec = get_worker_runtime("opencode")
    assert spec.build_flags(
        model="nmedia_cloud/claude-sonnet-5", extra_args=["--verbose"]
    ) == ["--verbose", "--model", "nmedia_cloud/claude-sonnet-5"]
    assert spec.build_flags(model="m", extra_args=["-m", "deja-present"]) == [
        "-m",
        "deja-present",
    ]


def test_opencode_has_no_default_model():
    """OpenCode : pas de modèle par défaut (la sélection reste TASK_MODEL_MAP)."""
    assert get_worker_runtime("opencode").default_model is None


def test_cline_one_shot_native_auto_approve():
    """Cline 3.x : aucun flag one-shot requis (auto-apprové par défaut)."""
    spec = get_worker_runtime("cline")
    assert spec.one_shot_flags == []
    assert spec.build_flags() == []


def test_cline_default_model_is_glm():
    """Cline : modèle par défaut glm-5.3-flash (choix humain, route nmedia_cloud)."""
    spec = get_worker_runtime("cline")
    assert spec.default_model == DEFAULT_CLINE_MODEL == "nmedia_cloud/glm-5.3-flash"
    assert spec.build_flags(model=DEFAULT_CLINE_MODEL) == [
        "--model",
        DEFAULT_CLINE_MODEL,
    ]


def test_pi_omp_interactive_historical_semantics():
    """pi/omp : --dangerously-skip-permissions + --model (comportement historique)."""
    for kind in ("pi", "omp"):
        spec = get_worker_runtime(kind)
        assert spec.build_flags(model="nmedia_cloud/gemini-3.8-flash") == [
            "--dangerously-skip-permissions",
            "--model",
            "nmedia_cloud/gemini-3.8-flash",
        ]


def test_resolve_npm_windows_binary_prefers_appdata_exe(tmp_path, monkeypatch):
    """Windows : le .exe npm ($APPDATA/npm/<bin>.exe) prime sur les shims .ps1/.cmd."""
    fake_exe = tmp_path / "npm" / "cline.exe"
    fake_exe.parent.mkdir()
    fake_exe.write_bytes(b"MZ")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert _resolve_npm_windows_binary("cline") == str(fake_exe)


def test_resolve_npm_windows_binary_returns_none_without_exe(tmp_path, monkeypatch):
    """Aucun .exe trouvé -> None (le fallback Herdr retombera sur le nom brut)."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert _resolve_npm_windows_binary("opencode") is None


def test_spec_without_resolver_returns_none():
    """Un runtime sans résolveur déclaré (pi/omp) retourne None (passthrough)."""
    assert get_worker_runtime("pi").resolve_binary() is None


def test_cline_spec_resolves_binary(tmp_path, monkeypatch):
    """La spec Cline délègue la résolution shim->exe au helper générique."""
    fake_exe = tmp_path / "npm" / "cline.exe"
    fake_exe.parent.mkdir()
    fake_exe.write_bytes(b"MZ")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert get_worker_runtime("cline").resolve_binary() == str(fake_exe)


def test_spec_is_extensible_without_branches():
    """Un nouveau CLI = une entrée de registre (contrat d'extension ADR-0346)."""
    custom = WorkerRuntimeSpec(
        kind="futur-cli", one_shot_flags=["--auto"], model_flag="--model"
    )
    assert custom.build_flags(model="x") == ["--auto", "--model", "x"]
