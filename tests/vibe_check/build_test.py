"""
Tests miroirs OQ-170-04 — Famille : build
Module testé : src.pipelines.vibe_check._vc_build

Checks couverts :
  - check_03_fts5          (Check 3)
  - check_06_lexical_guard (Check 6)
  - check_14_python_senior (Check 14)
  - check_17_qa_cert       (Check 17)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour (dict avec 'check' et 'status'). check_03 invoque
search_observations réelle (accès SQLite FTS5 sans stub) ; les autres checks
opèrent exclusivement sur le système de fichiers.
"""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Import & Smoke — les 4 symboles doivent être importables et appelables
# ---------------------------------------------------------------------------


def test_import_check_03_fts5():
    from src.pipelines.vibe_check._vc_build import check_03_fts5

    assert callable(check_03_fts5)


def test_import_check_06_lexical_guard():
    from src.pipelines.vibe_check._vc_build import check_06_lexical_guard

    assert callable(check_06_lexical_guard)


def test_import_check_14_python_senior():
    from src.pipelines.vibe_check._vc_build import check_14_python_senior

    assert callable(check_14_python_senior)


def test_import_check_17_qa_cert():
    from src.pipelines.vibe_check._vc_build import check_17_qa_cert

    assert callable(check_17_qa_cert)


# ---------------------------------------------------------------------------
# check_03_fts5 — retourne dict
# ---------------------------------------------------------------------------


def test_check_03_returns_dict(tmp_path):
    """check_03_fts5 doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_build import check_03_fts5

    result = check_03_fts5(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result, f"Clé 'check' manquante : {result}"
    assert "status" in result, f"Clé 'status' manquante : {result}"
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_03_check_field_is_string(tmp_path):
    """Le champ 'check' de check_03 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_build import check_03_fts5

    result = check_03_fts5(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert isinstance(result["check"], str) and result["check"]


# ---------------------------------------------------------------------------
# check_06_lexical_guard — retourne dict
# ---------------------------------------------------------------------------


def test_check_06_returns_dict(tmp_path):
    """check_06_lexical_guard doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_build import check_06_lexical_guard

    result = check_06_lexical_guard(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_06_status_is_string(tmp_path):
    """Le statut retourné par check_06 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_build import check_06_lexical_guard

    result = check_06_lexical_guard(tmp_path, "smoke_test", "RUN", "STAGE_PLAN_GRILL")
    assert isinstance(result["status"], str) and result["status"]


# ---------------------------------------------------------------------------
# check_14_python_senior — retourne dict
# ---------------------------------------------------------------------------


def test_check_14_returns_dict(tmp_path):
    """check_14_python_senior doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_build import check_14_python_senior

    result = check_14_python_senior(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_14_check_field_is_string(tmp_path):
    """Le champ 'check' de check_14 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_build import check_14_python_senior

    result = check_14_python_senior(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert isinstance(result["check"], str) and result["check"]


# ---------------------------------------------------------------------------
# check_17_qa_cert — retourne dict
# ---------------------------------------------------------------------------


def test_check_17_returns_dict(tmp_path):
    """check_17_qa_cert doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_build import check_17_qa_cert

    result = check_17_qa_cert(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_17_non_validate_stage_passes(tmp_path):
    """En dehors de STAGE_VALIDATE, check_17 ne doit pas FAIL (non applicable)."""
    from src.pipelines.vibe_check._vc_build import check_17_qa_cert

    result = check_17_qa_cert(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    # Hors phase VALIDATE, le check est non-applicable → PASS attendu
    assert result["status"] in ("PASS", "WARNING")
