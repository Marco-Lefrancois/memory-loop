"""
Tests TDD pour le pont OCR SVG vectorisé (Phase 1 — Plan d'Implémentation Framework
Enforcement Déterministe du Grounding Visuel & Épistémique).

Le bridge encapsule l'appel à render_svg.js (Chromium headless) puis ocr_png.ps1
(Windows.Media.Ocr natif). Il doit se dégrader gracieusement (retourner None)
si les outils sont indisponibles, en timeout, ou désactivés par variable d'env —
jamais bloquant pour le pipeline d'ingestion.
"""

import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.converters.svg_ocr_bridge import ocr_vectorized_svg, is_svg_ocr_enabled


def _mock_completed(returncode=0, stdout="", stderr=""):
    proc = MagicMock(spec=subprocess.CompletedProcess)
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


def test_svg_ocr_disabled_via_env(monkeypatch, tmp_path):
    """MLOOP_SVG_OCR=0 doit court-circuiter tout appel subprocess."""
    monkeypatch.setenv("MLOOP_SVG_OCR", "0")
    svg_file = tmp_path / "vectorized.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")

    with patch("src.converters.svg_ocr_bridge.subprocess.run") as mock_run:
        result = ocr_vectorized_svg(svg_file, work_dir=tmp_path)
        assert result is None
        mock_run.assert_not_called()


def test_svg_ocr_enabled_by_default(monkeypatch):
    monkeypatch.delenv("MLOOP_SVG_OCR", raising=False)
    assert is_svg_ocr_enabled() is True


def test_svg_ocr_success_path(monkeypatch, tmp_path):
    """Rendu Chromium OK + OCR natif OK -> texte reconnu retourné."""
    monkeypatch.delenv("MLOOP_SVG_OCR", raising=False)
    svg_file = tmp_path / "vectorized.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")
    out_png = tmp_path / "ocr_work" / "vectorized.png"

    def fake_run(cmd, *args, **kwargs):
        # Premier appel : node render_svg.js -> simule la création du PNG
        if cmd[0] == "node" or (
            isinstance(cmd, list) and "render_svg.js" in " ".join(cmd)
        ):
            out_png.parent.mkdir(parents=True, exist_ok=True)
            out_png.write_bytes(b"\x89PNG\r\n")
            return _mock_completed(0, stdout=f"OK {out_png}\n")
        # Second appel : ocr_png.ps1 -> simule la sortie OCR
        return _mock_completed(
            0,
            stdout=f"==================== vectorized.png ====================\nHeure réelle\nConfirmer\n",
        )

    with patch("src.converters.svg_ocr_bridge.subprocess.run", side_effect=fake_run):
        result = ocr_vectorized_svg(svg_file, work_dir=tmp_path / "ocr_work")

    assert result is not None
    assert "Heure réelle" in result
    assert "Confirmer" in result


def test_svg_ocr_render_failure_returns_none(monkeypatch, tmp_path):
    """Si Chromium/Playwright n'est pas disponible (returncode != 0), dégradation gracieuse."""
    monkeypatch.delenv("MLOOP_SVG_OCR", raising=False)
    svg_file = tmp_path / "vectorized.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")

    with patch(
        "src.converters.svg_ocr_bridge.subprocess.run",
        return_value=_mock_completed(1, stderr="ERREUR : playwright introuvable"),
    ):
        result = ocr_vectorized_svg(svg_file, work_dir=tmp_path / "ocr_work")

    assert result is None


def test_svg_ocr_tool_missing_returns_none(monkeypatch, tmp_path):
    """Si node/powershell sont absents du PATH (FileNotFoundError), dégradation gracieuse."""
    monkeypatch.delenv("MLOOP_SVG_OCR", raising=False)
    svg_file = tmp_path / "vectorized.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")

    with patch(
        "src.converters.svg_ocr_bridge.subprocess.run",
        side_effect=FileNotFoundError("node introuvable"),
    ):
        result = ocr_vectorized_svg(svg_file, work_dir=tmp_path / "ocr_work")

    assert result is None


def test_svg_ocr_timeout_returns_none(monkeypatch, tmp_path):
    """Un timeout subprocess ne doit jamais lever d'exception non gérée."""
    monkeypatch.delenv("MLOOP_SVG_OCR", raising=False)
    svg_file = tmp_path / "vectorized.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")

    with patch(
        "src.converters.svg_ocr_bridge.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="node", timeout=30),
    ):
        result = ocr_vectorized_svg(svg_file, work_dir=tmp_path / "ocr_work")

    assert result is None
