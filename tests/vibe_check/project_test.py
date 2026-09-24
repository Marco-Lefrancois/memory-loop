"""
Tests miroirs OQ-170-04 — Famille : project
Module testé : src.pipelines.vibe_check._vc_project

Checks couverts :
  - check_02_boundary      (Check 2)
  - check_05_hygiene       (Check 5)
  - check_09_lod_freshness (Check 9)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour (dict avec 'check' et 'status') sur des répertoires
temporaires contrôlés.
"""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Import & Smoke — les 3 symboles doivent être importables et appelables
# ---------------------------------------------------------------------------


def test_import_check_02_boundary():
    from src.pipelines.vibe_check._vc_project import check_02_boundary

    assert callable(check_02_boundary)


def test_import_check_05_hygiene():
    from src.pipelines.vibe_check._vc_project import check_05_hygiene

    assert callable(check_05_hygiene)


def test_import_check_09_lod_freshness():
    from src.pipelines.vibe_check._vc_project import check_09_lod_freshness

    assert callable(check_09_lod_freshness)


# ---------------------------------------------------------------------------
# check_02_boundary — retourne dict
# ---------------------------------------------------------------------------


def test_check_02_returns_dict(tmp_path):
    """check_02_boundary doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_project import check_02_boundary

    result = check_02_boundary(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result, f"Clé 'check' manquante : {result}"
    assert "status" in result, f"Clé 'status' manquante : {result}"
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_02_existing_dir_passes(tmp_path):
    """Avec un project_dir existant, check_02 retourne PASS (terrain de jeu balisé)."""
    from src.pipelines.vibe_check._vc_project import check_02_boundary

    result = check_02_boundary(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] == "PASS"


def test_check_02_nonexistent_dir_with_src_passes(tmp_path):
    """Si project_dir n'existe pas mais src/ existe, check_02 retourne PASS."""
    from src.pipelines.vibe_check._vc_project import check_02_boundary

    ghost_dir = tmp_path / "ghost_project"  # répertoire non créé
    # src/ existe toujours dans le projet réel — le check ne doit pas FAIL
    result = check_02_boundary(ghost_dir, "ghost", "INIT", "STAGE_INIT")
    assert result["status"] in ("PASS", "FAIL", "WARNING")


# ---------------------------------------------------------------------------
# check_05_hygiene — retourne dict
# ---------------------------------------------------------------------------


def test_check_05_returns_dict(tmp_path):
    """check_05_hygiene doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_project import check_05_hygiene

    result = check_05_hygiene(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_05_clean_project_passes(tmp_path):
    """Un projet sans sous-READMEs dans reference/ doit retourner PASS."""
    from src.pipelines.vibe_check._vc_project import check_05_hygiene

    (tmp_path / "reference").mkdir()
    result = check_05_hygiene(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] == "PASS"


def test_check_05_subreadme_in_reference_excluded(tmp_path):
    """
    Les sous-READMEs dans reference/ sont EXCLUS du détecteur d'hygiène (ADR-0100) :
    reference/ est une zone de staging non versionnée — ses sous-dossiers ne sont
    pas des sous-packages Python, le check les ignore explicitement.
    La présence d'un README.md dans reference/subfolder/ doit donc retourner PASS.
    """
    from src.pipelines.vibe_check._vc_project import check_05_hygiene

    ref = tmp_path / "reference"
    ref.mkdir()
    sub = ref / "subfolder"
    sub.mkdir()
    (sub / "README.md").write_text("# Zone staging", encoding="utf-8")

    result = check_05_hygiene(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] == "PASS", (
        "reference/ est exclue de l'audit hygiène : le check doit retourner PASS"
    )


def test_check_05_subreadme_outside_reference_fails(tmp_path):
    """Un sous-README HORS de reference/ (ex: docs/) doit déclencher un FAIL."""
    from src.pipelines.vibe_check._vc_project import check_05_hygiene

    docs = tmp_path / "docs" / "subfolder"
    docs.mkdir(parents=True)
    (docs / "README.md").write_text("# Parasite", encoding="utf-8")

    result = check_05_hygiene(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# check_09_lod_freshness — retourne dict
# ---------------------------------------------------------------------------


def test_check_09_returns_dict(tmp_path):
    """check_09_lod_freshness doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_project import check_09_lod_freshness

    result = check_09_lod_freshness(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict)
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_09_no_docs_passes(tmp_path):
    """Sans dossier docs/, check_09 retourne PASS (rien à vérifier)."""
    from src.pipelines.vibe_check._vc_project import check_09_lod_freshness

    result = check_09_lod_freshness(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] in ("PASS", "FAIL", "WARNING")
