"""
tests/vibe_check/extraction_test.py — Tests miroirs du check 22 : Protocole d'Extraction Modulaire.

Couvre :
  - PASS : aucun fichier en dépassement stagé
  - PASS : plan présent + fumée simulée verte
  - WARNING : plan présent + fumée non verte
  - WARNING : plan absent + fumée verte
  - FAIL : plan absent + fumée rouge
  - Phase non-BUILD : PASS immédiat (bypass)
  - check_smoke_check : import direct du module fonctionnel

Conforme ADR-0369 : timeout=, with, zéro except pass nu.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Ajout du répertoire racine au path si nécessaire ─────────────────────────
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pipelines.vibe_check._vc_extraction import (
    _count_lines,
    _get_staged_files,
    _has_extraction_plan,
    _run_smoke_check,
    check_22_extraction_protocol,
)


# ── Fixtures & helpers ────────────────────────────────────────────────────────


@pytest.fixture()
def ctx_build(tmp_path):
    """Contexte de base pour check_22 en phase BUILD."""
    project_dir = tmp_path / "Projects" / "mLoop"
    project_dir.mkdir(parents=True)
    return project_dir, "mLoop", "RUN", "STAGE_BUILD"


@pytest.fixture()
def plan_dir(tmp_path):
    """Crée un répertoire memory/plan/ avec un plan d'extraction."""
    p = tmp_path / "Projects" / "mLoop" / "memory" / "plan"
    p.mkdir(parents=True)
    return p


# ── Tests check_22_extraction_protocol ───────────────────────────────────────


class TestCheck22ExtractionProtocol:
    """Suite de tests pour check_22_extraction_protocol."""

    def test_pass_no_staged_oversized_files(self, ctx_build):
        """PASS si aucun fichier >300L n'est stagé."""
        project_dir, project_name, mode, stage = ctx_build
        with (
            patch(
                "src.pipelines.vibe_check._vc_extraction._get_staged_files",
                return_value=["src/small.py"],
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._count_lines",
                return_value=50,
            ),
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        assert result["status"] == "PASS"

    def test_pass_no_staged_files_at_all(self, ctx_build):
        """PASS si le working tree est propre (aucun fichier stagé)."""
        project_dir, project_name, mode, stage = ctx_build
        with patch(
            "src.pipelines.vibe_check._vc_extraction._get_staged_files",
            return_value=[],
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        assert result["status"] == "PASS"

    def test_pass_plan_present_smoke_green(self, ctx_build, tmp_path, plan_dir):
        """PASS si plan présent ET fumée verte."""
        project_dir, project_name, mode, stage = ctx_build
        # Créer un plan d'extraction
        (plan_dir / "implementation_plan_mymodule_extraction.md").write_text(
            "plan", encoding="utf-8"
        )

        with (
            patch(
                "src.pipelines.vibe_check._vc_extraction._get_staged_files",
                return_value=["src/bigmodule.py"],
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._count_lines",
                return_value=500,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._has_extraction_plan",
                return_value=True,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._run_smoke_check",
                return_value=(True, "✅ Aucun symbole non résolu détecté."),
            ),
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        assert result["status"] == "PASS"

    def test_warning_plan_present_smoke_not_green(self, ctx_build):
        """WARNING si plan présent mais fumée non verte."""
        project_dir, project_name, mode, stage = ctx_build
        with (
            patch(
                "src.pipelines.vibe_check._vc_extraction._get_staged_files",
                return_value=["src/bigmodule.py"],
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._count_lines",
                return_value=500,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._has_extraction_plan",
                return_value=True,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._run_smoke_check",
                return_value=(False, "❌ Symbole non résolu : foo"),
            ),
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        assert result["status"] == "WARNING"

    def test_warning_plan_absent_smoke_green(self, ctx_build):
        """WARNING si plan absent mais fumée verte."""
        project_dir, project_name, mode, stage = ctx_build
        with (
            patch(
                "src.pipelines.vibe_check._vc_extraction._get_staged_files",
                return_value=["src/bigmodule.py"],
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._count_lines",
                return_value=500,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._has_extraction_plan",
                return_value=False,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._run_smoke_check",
                return_value=(True, "✅ Aucun symbole non résolu détecté."),
            ),
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        assert result["status"] == "WARNING"

    def test_fail_plan_absent_smoke_rouge(self, ctx_build):
        """FAIL si plan absent ET fumée rouge."""
        project_dir, project_name, mode, stage = ctx_build
        with (
            patch(
                "src.pipelines.vibe_check._vc_extraction._get_staged_files",
                return_value=["src/bigmodule.py"],
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._count_lines",
                return_value=500,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._has_extraction_plan",
                return_value=False,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._run_smoke_check",
                return_value=(False, "❌ Module non importable"),
            ),
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        assert result["status"] == "FAIL"

    @pytest.mark.parametrize(
        "stage_label", ["STAGE_INIT", "STAGE_SOW", "STAGE_SPEC", "STAGE_PLAN_GRILL"]
    )
    def test_pass_bypass_non_build_stages(self, ctx_build, stage_label):
        """PASS immédiat pour les phases hors BUILD (pas d'évaluation)."""
        project_dir, project_name, _, _ = ctx_build
        # Mode INIT : bypass immédiat
        result = check_22_extraction_protocol(project_dir, project_name, "INIT", stage_label)
        assert result["status"] == "PASS"

    def test_multiple_oversized_files_uses_first(self, ctx_build):
        """La fumée est exécutée sur le premier fichier en dépassement."""
        project_dir, project_name, mode, stage = ctx_build
        with (
            patch(
                "src.pipelines.vibe_check._vc_extraction._get_staged_files",
                return_value=["src/alpha.py", "src/beta.py"],
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._count_lines",
                return_value=400,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._has_extraction_plan",
                return_value=True,
            ),
            patch(
                "src.pipelines.vibe_check._vc_extraction._run_smoke_check",
                return_value=(True, "✅"),
            ) as mock_smoke,
        ):
            result = check_22_extraction_protocol(project_dir, project_name, mode, stage)
        mock_smoke.assert_called_once_with("src/alpha.py")
        assert result["status"] == "PASS"


# ── Tests helpers internes ────────────────────────────────────────────────────


class TestHelpers:
    """Tests des fonctions utilitaires internes."""

    def test_count_lines_existing_file(self, tmp_path):
        """_count_lines retourne le bon nombre de lignes."""
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\n", encoding="utf-8")
        assert _count_lines(str(f)) == 3

    def test_count_lines_missing_file(self):
        """_count_lines retourne 0 pour un fichier inexistant."""
        assert _count_lines("/nonexistent/path.py") == 0

    def test_has_extraction_plan_true(self, tmp_path):
        """_has_extraction_plan retourne True si un plan existe."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        (plan_dir / "implementation_plan_critic_extraction.md").write_text("plan", encoding="utf-8")
        assert _has_extraction_plan(plan_dir) is True

    def test_has_extraction_plan_false_empty(self, tmp_path):
        """_has_extraction_plan retourne False si le répertoire est vide."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        assert _has_extraction_plan(plan_dir) is False

    def test_has_extraction_plan_false_missing(self, tmp_path):
        """_has_extraction_plan retourne False si le répertoire n'existe pas."""
        assert _has_extraction_plan(tmp_path / "nonexistent") is False

    def test_has_extraction_plan_non_matching_file(self, tmp_path):
        """_has_extraction_plan retourne False si le fichier ne matche pas le glob."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        (plan_dir / "implementation_plan_MLOOP-170-BE.md").write_text("plan", encoding="utf-8")
        # Ne contient pas 'extraction' dans le nom
        assert _has_extraction_plan(plan_dir) is False

    def test_get_staged_files_git_unavailable(self):
        """_get_staged_files retourne [] si git est indisponible."""
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = _get_staged_files()
        assert result == []

    def test_get_staged_files_git_timeout(self):
        """_get_staged_files retourne [] en cas de timeout git."""
        import subprocess as sp

        with patch("subprocess.run", side_effect=sp.TimeoutExpired("git", 10)):
            result = _get_staged_files()
        assert result == []

    def test_run_smoke_check_timeout(self):
        """_run_smoke_check retourne (False, msg) en cas de timeout."""
        import subprocess as sp

        with patch("subprocess.run", side_effect=sp.TimeoutExpired("python", 30)):
            ok, msg = _run_smoke_check("src/fake.py")
        assert ok is False
        assert "Timeout" in msg

    def test_run_smoke_check_module_not_found(self):
        """_run_smoke_check retourne (False, msg) si le module est introuvable."""
        with patch("subprocess.run", side_effect=FileNotFoundError("python not found")):
            ok, msg = _run_smoke_check("src/fake.py")
        assert ok is False
        assert "introuvable" in msg


# ── Tests d'intégration smoke check module ────────────────────────────────────


class TestImportSmokeCheckModule:
    """Tests d'intégration légers sur import_smoke_check.py."""

    def test_import_smoke_check_importable(self):
        """Le module import_smoke_check est importable sans erreur."""
        import importlib

        mod = importlib.import_module("src.pipelines.import_smoke_check")
        assert hasattr(mod, "run_smoke_check")
        assert hasattr(mod, "main")
        assert hasattr(mod, "find_callers")
        assert hasattr(mod, "can_import_module")

    def test_path_to_module_name(self):
        """path_to_module_name convertit correctement un chemin en nom de module."""
        from src.pipelines.import_smoke_check import path_to_module_name

        result = path_to_module_name(Path("src/pipelines/vibe_check.py"), src_root=Path("."))
        assert result == "src.pipelines.vibe_check"

    def test_can_import_real_module(self):
        """can_import_module réussit pour un module réel."""
        from src.pipelines.import_smoke_check import can_import_module

        ok, err = can_import_module("src.pipelines.vibe_check")
        assert ok is True
        assert err == ""

    def test_can_import_nonexistent_module(self):
        """can_import_module échoue pour un module inexistant."""
        from src.pipelines.import_smoke_check import can_import_module

        ok, err = can_import_module("src.nonexistent.fake_module_xyz")
        assert ok is False
        assert err != ""

    def test_extract_imported_symbols(self, tmp_path):
        """extract_imported_symbols extrait correctement les symboles."""
        from src.pipelines.import_smoke_check import extract_imported_symbols

        caller = tmp_path / "caller.py"
        caller.write_text(
            "from src.pipelines.vibe_check import run_vibe_check, detect_project_lifecycle_stage\n",
            encoding="utf-8",
        )
        symbols = extract_imported_symbols(caller, "src.pipelines.vibe_check")
        assert "run_vibe_check" in symbols
        assert "detect_project_lifecycle_stage" in symbols

    def test_extract_imported_symbols_no_match(self, tmp_path):
        """extract_imported_symbols retourne [] si aucun import ne correspond."""
        from src.pipelines.import_smoke_check import extract_imported_symbols

        caller = tmp_path / "caller.py"
        caller.write_text("import os\nimport sys\n", encoding="utf-8")
        symbols = extract_imported_symbols(caller, "src.pipelines.vibe_check")
        assert symbols == []
