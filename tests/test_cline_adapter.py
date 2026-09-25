# -*- coding: utf-8 -*-
"""
Tests unitaires de l'adaptateur runtime Cline CLI (ADR-0346 — Délégation Dual-Track).
Ground truth : cline 3.0.62 — one-shot auto-apprové par défaut (pas de --yolo),
sélection modèle via -m/--model, binaire npm .exe requis sous Windows.
"""

from pathlib import Path
from unittest.mock import patch

from src.core.agent_probe import AGENT_CATALOG
from src.core.cline_adapter import DEFAULT_CLINE_MODEL, build_cline_flags, resolve_cline_binary
from src.core.herdr_adapter import HerdrAdapter


def test_cline_agent_in_catalog():
    """ADR-0346 : 'cline' est sondé par la sonde d'agents aval (doctor --agents)."""
    definition = AGENT_CATALOG["cline"]
    assert definition.bin_name == "cline"
    assert "STAGE_BUILD" in definition.critical_in_stages


def test_build_cline_flags_model():
    """Un modèle explicite produit -m <model-id> (surface CLI réelle 3.0.62)."""
    flags = build_cline_flags(model="nmedia_cloud/glm-5.3-flash")
    assert flags == ["--auto-approve", "true", "--model", "nmedia_cloud/glm-5.3-flash"]


def test_build_cline_flags_default_model():
    """Sans modèle explicite, la mission route vers le modèle Cline par défaut."""
    flags = build_cline_flags(model=DEFAULT_CLINE_MODEL)
    assert flags == ["--auto-approve", "true", "--model", DEFAULT_CLINE_MODEL]


def test_build_cline_flags_extra_args_priority():
    """extra_args explicites court-circuitent la construction par défaut (contrat herdr_adapter)."""
    assert build_cline_flags(extra_args=["--thinking", "high"]) == ["--thinking", "high"]
    assert build_cline_flags(model="x", extra_args=[]) == ["--auto-approve", "true", "--model", "x"]


def test_resolve_cline_binary_prefers_appdata_exe(tmp_path, monkeypatch):
    """Windows : le .exe npm ($APPDATA/npm/cline.exe) prime sur les shims .ps1/.cmd."""
    fake_exe = tmp_path / "npm" / "cline.exe"
    fake_exe.parent.mkdir()
    fake_exe.write_bytes(b"MZ")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert resolve_cline_binary() == str(fake_exe)


def test_resolve_cline_binary_returns_none_without_exe(tmp_path, monkeypatch):
    """Aucun .exe trouvé -> None (le fallback Herdr retombera sur le nom brut)."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert resolve_cline_binary() is None

