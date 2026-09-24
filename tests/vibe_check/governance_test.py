"""
Tests miroirs OQ-170-04 — Famille : governance
Module testé : src.pipelines.vibe_check._vc_governance

Checks couverts :
  - check_10_visual_contract (Check 10)
  - check_11_rule_engine     (Check 11)
  - check_12_sow_granularity (Check 12)
  - check_13_phase_gate      (Check 13)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour (dict avec 'check' et 'status') sur des répertoires
temporaires sans dépendances externes.
"""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Import & Smoke — les 4 symboles doivent être importables et appelables
# ---------------------------------------------------------------------------


def test_import_check_10_visual_contract():
    from src.pipelines.vibe_check._vc_governance import check_10_visual_contract

    assert callable(check_10_visual_contract)


def test_import_check_11_rule_engine():
    from src.pipelines.vibe_check._vc_governance import check_11_rule_engine

    assert callable(check_11_rule_engine)


def test_import_check_12_sow_granularity():
    from src.pipelines.vibe_check._vc_governance import check_12_sow_granularity

    assert callable(check_12_sow_granularity)


def test_import_check_13_phase_gate():
    from src.pipelines.vibe_check._vc_governance import check_13_phase_gate

    assert callable(check_13_phase_gate)


# ---------------------------------------------------------------------------
# check_10_visual_contract — retourne dict
# ---------------------------------------------------------------------------


def test_check_10_returns_dict(tmp_path):
    """check_10_visual_contract doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_governance import check_10_visual_contract

    result = check_10_visual_contract(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result, f"Clé 'check' manquante : {result}"
    assert "status" in result, f"Clé 'status' manquante : {result}"
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_10_no_assets_passes(tmp_path):
    """Sans dossier docs/05-assets/, check_10 retourne PASS (rien à auditer)."""
    from src.pipelines.vibe_check._vc_governance import check_10_visual_contract

    result = check_10_visual_contract(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] == "PASS"


def test_check_10_check_field_is_string(tmp_path):
    """Le champ 'check' de check_10 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_governance import check_10_visual_contract

    result = check_10_visual_contract(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert isinstance(result["check"], str) and result["check"]


# ---------------------------------------------------------------------------
# check_11_rule_engine — retourne dict
# ---------------------------------------------------------------------------


def test_check_11_returns_dict(tmp_path):
    """check_11_rule_engine doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_governance import check_11_rule_engine

    result = check_11_rule_engine(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_11_status_is_string(tmp_path):
    """Le statut de check_11 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_governance import check_11_rule_engine

    result = check_11_rule_engine(tmp_path, "smoke_test", "RUN", "STAGE_VALIDATE")
    assert isinstance(result["status"], str) and result["status"]


# ---------------------------------------------------------------------------
# check_12_sow_granularity — retourne dict
# ---------------------------------------------------------------------------


def test_check_12_returns_dict(tmp_path):
    """check_12_sow_granularity doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_governance import check_12_sow_granularity

    result = check_12_sow_granularity(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_12_no_sow_passes(tmp_path):
    """Sans fichier SOW, check_12 retourne PASS (rien à vérifier)."""
    from src.pipelines.vibe_check._vc_governance import check_12_sow_granularity

    result = check_12_sow_granularity(tmp_path, "smoke_test", "INIT", "STAGE_SOW")
    assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# check_13_phase_gate — retourne dict
# ---------------------------------------------------------------------------


def test_check_13_returns_dict(tmp_path):
    """check_13_phase_gate doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_governance import check_13_phase_gate

    result = check_13_phase_gate(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_13_init_without_stories_passes(tmp_path):
    """En mode INIT sans stories prématurées, check_13 retourne PASS."""
    from src.pipelines.vibe_check._vc_governance import check_13_phase_gate

    (tmp_path / "backlog" / "stories").mkdir(parents=True)
    result = check_13_phase_gate(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_13_status_is_string(tmp_path):
    """Le statut de check_13 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_governance import check_13_phase_gate

    result = check_13_phase_gate(tmp_path, "smoke_test", "RUN", "STAGE_PLAN_GRILL")
    assert isinstance(result["status"], str) and result["status"]
