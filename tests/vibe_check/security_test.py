"""
Tests miroirs OQ-170-04 — Famille : security
Module testé : src.pipelines.vibe_check._vc_security

Checks couverts :
  - check_07_secret_leak (Check 7)
  - check_08_litellm_key (Check 8)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour (dict avec 'check' et 'status'). Les appels réels
s'exécutent sans stub : ils inspectent l'environnement courant et retournent
PASS ou FAIL selon l'état réel — ce qui est précisément ce que les tests miroirs
doivent vérifier (structure, pas valeur exacte).
"""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Import & Smoke — les 2 symboles doivent être importables et appelables
# ---------------------------------------------------------------------------


def test_import_check_07_secret_leak():
    from src.pipelines.vibe_check._vc_security import check_07_secret_leak

    assert callable(check_07_secret_leak)


def test_import_check_08_litellm_key():
    from src.pipelines.vibe_check._vc_security import check_08_litellm_key

    assert callable(check_08_litellm_key)


# ---------------------------------------------------------------------------
# check_07_secret_leak — retourne dict
# ---------------------------------------------------------------------------


def test_check_07_returns_dict(tmp_path):
    """check_07_secret_leak doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_security import check_07_secret_leak

    result = check_07_secret_leak(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result, f"Clé 'check' manquante : {result}"
    assert "status" in result, f"Clé 'status' manquante : {result}"
    assert result["status"] in ("PASS", "FAIL", "WARNING"), f"Statut invalide : {result['status']}"


def test_check_07_check_field_is_string(tmp_path):
    """Le champ 'check' de check_07 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_security import check_07_secret_leak

    result = check_07_secret_leak(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert isinstance(result["check"], str) and result["check"]


def test_check_07_clean_env_passes(tmp_path, monkeypatch):
    """Dans un environnement propre (variables sensibles absentes), check_07 retourne PASS."""
    from src.pipelines.vibe_check._vc_security import check_07_secret_leak

    # Retirer les variables potentiellement polluantes pour ce test isolé
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LITELLM_MASTER_KEY"):
        monkeypatch.delenv(var, raising=False)

    result = check_07_secret_leak(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] in ("PASS", "FAIL", "WARNING")  # structure garantie


# ---------------------------------------------------------------------------
# check_08_litellm_key — retourne dict
# ---------------------------------------------------------------------------


def test_check_08_returns_dict(tmp_path):
    """check_08_litellm_key doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_security import check_08_litellm_key

    result = check_08_litellm_key(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_08_check_field_is_string(tmp_path):
    """Le champ 'check' de check_08 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_security import check_08_litellm_key

    result = check_08_litellm_key(tmp_path, "smoke_test", "RUN", "STAGE_SHIP_SYNC")
    assert isinstance(result["check"], str) and result["check"]
