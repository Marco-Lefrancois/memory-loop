# -*- coding: utf-8 -*-
"""
Tests unitaires du registre SSOT multi-runtimes des workers Herdr (ADR-0346 / ADR-0389).

Ground truth :
- opencode : one-shot via --auto et --agent worker (ADR-0389), pas de modèle par défaut ;
- cline 3.x : auto-approbation explicite (--auto-approve true), sélection modèle
  -m/--model, binaire npm .exe requis sous Windows ;
- pi / omp : mode interactif historique (--dangerously-skip-permissions +
  --model) préservé à l'identique.
"""

from unittest.mock import patch

import pytest

from src.core.herdr_worker import HerdrWorkerMixin
from src.core.herdr_worker_core import TASK_MODEL_MAP
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
    """OpenCode : --auto et --agent worker (ADR-0389), puis --model ajouté si absent."""
    spec = get_worker_runtime("opencode")
    assert spec.build_flags() == ["--auto", "--agent", "worker"]
    assert spec.build_flags(model="nmedia_cloud/claude-opus-4.8") == [
        "--auto",
        "--agent",
        "worker",
        "--model",
        "nmedia_cloud/claude-opus-4.8",
    ]


def test_opencode_extra_args_merge_model():
    """OpenCode : extra_args explicites + modèle absent -> modèle ajouté après."""
    spec = get_worker_runtime("opencode")
    assert spec.build_flags(model="nmedia_cloud/claude-sonnet-5", extra_args=["--verbose"]) == [
        "--verbose",
        "--model",
        "nmedia_cloud/claude-sonnet-5",
    ]
    assert spec.build_flags(model="m", extra_args=["-m", "deja-present"]) == [
        "-m",
        "deja-present",
    ]


def test_opencode_has_no_default_model():
    """OpenCode : pas de modèle par défaut (la sélection reste TASK_MODEL_MAP)."""
    assert get_worker_runtime("opencode").default_model is None


def test_task_model_map_build_uses_free_opencode_model():
    """ADR-0388 : la mission 'build' bascule sur le free tier natif OpenCode
    pour faciliter le développement et worker-spawn, sans coût LiteLLM.
    Les portes qualité (deepening/validation/deepsearch/compaction) restent
    inchangées sur leurs modèles LiteLLM nmedia_cloud.
    """
    assert TASK_MODEL_MAP["build"] == "opencode/mimo-v2.6-flash-free"
    assert TASK_MODEL_MAP["deepening"] == "nmedia_cloud/claude-opus-4.8"
    assert TASK_MODEL_MAP["validation"] == "nmedia_cloud/gpt-5.6-terra-thinking"
    assert TASK_MODEL_MAP["deepsearch"] == "nmedia_cloud/claude-sonnet-5"
    assert TASK_MODEL_MAP["compaction"] == "nmedia_cloud/gemini-3.8-flash"


def test_task_model_map_core_mixin_parity():
    """Le doublon historique HerdrWorkerMixin.TASK_MODEL_MAP doit rester en
    parité stricte avec le SSOT src.core.herdr_worker_core.TASK_MODEL_MAP.
    """
    assert HerdrWorkerMixin.TASK_MODEL_MAP == TASK_MODEL_MAP


def test_cline_one_shot_native_auto_approve():
    """Cline 3.x : auto-approbation explicite (--auto-approve true, ADR-0389)."""
    spec = get_worker_runtime("cline")
    assert spec.one_shot_flags == ["--auto-approve", "true"]
    assert spec.build_flags() == ["--auto-approve", "true"]


def test_cline_default_model_is_glm():
    """Cline : modèle par défaut gratuit natif (DeepSeek-V4.1-Flash via Cline Free)."""
    spec = get_worker_runtime("cline")
    assert spec.default_model == DEFAULT_CLINE_MODEL == "cline-free/deepseek-v4.1-flash"
    assert spec.build_flags(model=DEFAULT_CLINE_MODEL) == [
        "--auto-approve",
        "true",
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


def test_resolve_npm_windows_binary_falls_back_to_cmd_shim(tmp_path, monkeypatch):
    """Cline-like : aucun .exe npm -> le shim .cmd est résolu (topologie npm réelle).

    Ground truth locale : `cline` n'installe que `cline`/`cline.cmd`/`cline.ps1`
    (aucun `.exe`), contrairement à opencode. Le `.cmd` reste exécutable par
    l'opérateur d'appel PowerShell `&` utilisé par le fallback pane-run.
    """
    fake_cmd = tmp_path / "npm" / "cline.cmd"
    fake_cmd.parent.mkdir()
    fake_cmd.write_text("@ECHO off\r\n", encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert _resolve_npm_windows_binary("cline") == str(fake_cmd)


def test_resolve_npm_windows_binary_prefers_exe_over_cmd(tmp_path, monkeypatch):
    """Si les deux existent, le .exe natif prime sur le shim .cmd."""
    npm_dir = tmp_path / "npm"
    npm_dir.mkdir()
    exe = npm_dir / "cline.exe"
    exe.write_bytes(b"MZ")
    (npm_dir / "cline.cmd").write_text("@ECHO off\r\n", encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert _resolve_npm_windows_binary("cline") == str(exe)


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
    custom = WorkerRuntimeSpec(kind="futur-cli", one_shot_flags=["--auto"], model_flag="--model")
    assert custom.build_flags(model="x") == ["--auto", "--model", "x"]


def test_needs_pane_run_fallback_for_cmd_shim(tmp_path, monkeypatch):
    """Shim .cmd (Cline) : court-circuit vers pane-run (Herdr échoue/volet fantôme)."""
    fake_cmd = tmp_path / "npm" / "cline.cmd"
    fake_cmd.parent.mkdir()
    fake_cmd.write_text("@ECHO off\r\n", encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert get_worker_runtime("cline").needs_pane_run_fallback() is True


def test_needs_pane_run_fallback_false_for_native_exe(tmp_path, monkeypatch):
    """Exe natif (OpenCode) : lancement Herdr natif conservé (pas de court-circuit)."""
    fake_exe = tmp_path / "npm" / "opencode.exe"
    fake_exe.parent.mkdir()
    fake_exe.write_bytes(b"MZ")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert get_worker_runtime("opencode").needs_pane_run_fallback() is False


def test_needs_pane_run_fallback_false_without_resolver():
    """Runtime sans résolveur déclaré (pi/omp) : décision False."""
    assert get_worker_runtime("pi").needs_pane_run_fallback() is False
