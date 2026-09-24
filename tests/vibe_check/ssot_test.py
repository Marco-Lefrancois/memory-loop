"""
Tests miroirs OQ-170-04 — Famille : ssot
Module testé : src.pipelines.vibe_check._vc_ssot

Checks couverts :
  - check_04_ssot_backlog    (Check 4)
  - check_15_guide_parity    (Check 15)
  - check_20_directives_ssot (Check 20)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour (dict avec 'check' et 'status') sur des répertoires
temporaires sans dépendances externes.
"""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Import & Smoke — les 3 symboles doivent être importables et appelables
# ---------------------------------------------------------------------------


def test_import_check_04_ssot_backlog():
    from src.pipelines.vibe_check._vc_ssot import check_04_ssot_backlog

    assert callable(check_04_ssot_backlog)


def test_import_check_15_guide_parity():
    from src.pipelines.vibe_check._vc_ssot import check_15_guide_parity

    assert callable(check_15_guide_parity)


def test_import_check_20_directives_ssot():
    from src.pipelines.vibe_check._vc_ssot import check_20_directives_ssot

    assert callable(check_20_directives_ssot)


# ---------------------------------------------------------------------------
# check_04_ssot_backlog — retourne dict
# ---------------------------------------------------------------------------


def test_check_04_returns_dict(tmp_path):
    """check_04_ssot_backlog doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_ssot import check_04_ssot_backlog

    result = check_04_ssot_backlog(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result, f"Clé 'check' manquante : {result}"
    assert "status" in result, f"Clé 'status' manquante : {result}"
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_04_init_mode_no_backlog_passes(tmp_path):
    """En mode INIT sans sprint_backlog.md, le check doit retourner PASS (pas requis)."""
    from src.pipelines.vibe_check._vc_ssot import check_04_ssot_backlog

    result = check_04_ssot_backlog(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    # En mode INIT le backlog n'est pas exigé — PASS attendu
    assert result["status"] == "PASS"


def test_check_04_run_mode_missing_backlog_fails(tmp_path):
    """En mode RUN sans sprint_backlog.md, le check doit retourner FAIL."""
    from src.pipelines.vibe_check._vc_ssot import check_04_ssot_backlog

    (tmp_path / "backlog").mkdir()
    result = check_04_ssot_backlog(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert result["status"] == "FAIL"


def test_check_04_run_mode_with_backlog_passes(tmp_path):
    """En mode RUN avec sprint_backlog.md présent, le check doit retourner PASS."""
    from src.pipelines.vibe_check._vc_ssot import check_04_ssot_backlog

    backlog_dir = tmp_path / "backlog"
    backlog_dir.mkdir()
    (backlog_dir / "sprint_backlog.md").write_text("# Backlog\n", encoding="utf-8")

    result = check_04_ssot_backlog(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# check_15_guide_parity — retourne dict
# ---------------------------------------------------------------------------


def test_check_15_returns_dict(tmp_path):
    """check_15_guide_parity doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_ssot import check_15_guide_parity

    result = check_15_guide_parity(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="RUN",
        stage_label="STAGE_BUILD",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_15_status_is_string(tmp_path):
    """Le statut retourné par check_15 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_ssot import check_15_guide_parity

    result = check_15_guide_parity(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert isinstance(result["status"], str) and result["status"]


# ---------------------------------------------------------------------------
# check_20_directives_ssot — retourne dict
# ---------------------------------------------------------------------------


def test_check_20_returns_dict(tmp_path):
    """check_20_directives_ssot doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_ssot import check_20_directives_ssot

    result = check_20_directives_ssot(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_20_status_is_string(tmp_path):
    """Le statut retourné par check_20 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_ssot import check_20_directives_ssot

    result = check_20_directives_ssot(tmp_path, "smoke_test", "RUN", "STAGE_PLAN_GRILL")
    assert isinstance(result["status"], str) and result["status"]
