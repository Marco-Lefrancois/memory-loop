"""
Tests miroirs OQ-170-04 — Famille : agents
Module testé : src.pipelines.vibe_check._vc_agents

Checks couverts :
  - check_01_agent_parity   (Check 1)
  - check_16_agent_probe    (Check 16)
  - check_19_standards_graph (Check 19)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour sur un appel minimal avec un projet fictif.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Import & Smoke — les 3 symboles doivent être importables et appelables
# ---------------------------------------------------------------------------


def test_import_check_01_agent_parity():
    from src.pipelines.vibe_check._vc_agents import check_01_agent_parity

    assert callable(check_01_agent_parity)


def test_import_check_16_agent_probe():
    from src.pipelines.vibe_check._vc_agents import check_16_agent_probe

    assert callable(check_16_agent_probe)


def test_import_check_19_standards_graph():
    from src.pipelines.vibe_check._vc_agents import check_19_standards_graph

    assert callable(check_19_standards_graph)


# ---------------------------------------------------------------------------
# check_01_agent_parity — retourne list[dict] avec status PASS/FAIL
# ---------------------------------------------------------------------------


def test_check_01_returns_list_of_dicts(tmp_path):
    """check_01_agent_parity doit retourner une liste de dicts avec les clés 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_agents import check_01_agent_parity

    result = check_01_agent_parity(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, list), "Le retour doit être une liste"
    assert len(result) > 0, "La liste ne doit pas être vide"
    for item in result:
        assert isinstance(item, dict), f"Chaque élément doit être un dict, reçu : {type(item)}"
        assert "check" in item, f"Clé 'check' manquante dans : {item}"
        assert "status" in item, f"Clé 'status' manquante dans : {item}"
        assert item["status"] in ("PASS", "FAIL", "WARNING"), f"Statut invalide : {item['status']}"


def test_check_01_status_is_string(tmp_path):
    """Les statuts renvoyés par check_01 sont des chaînes non vides."""
    from src.pipelines.vibe_check._vc_agents import check_01_agent_parity

    results = check_01_agent_parity(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    for item in results:
        assert isinstance(item["status"], str) and item["status"]


# ---------------------------------------------------------------------------
# check_16_agent_probe — retourne dict avec status PASS/FAIL
# ---------------------------------------------------------------------------


def test_check_16_returns_dict(tmp_path):
    """check_16_agent_probe doit retourner un dict avec les clés 'check' et 'status'.

    AgentProbe est importé de façon lazy à l'intérieur de la fonction (lazy import),
    donc le patch doit cibler 'src.core.agent_probe.AgentProbe'.
    """
    from src.pipelines.vibe_check._vc_agents import check_16_agent_probe

    with patch(
        "src.core.agent_probe.AgentProbe",
        autospec=True,
    ) as MockProbe:
        instance = MockProbe.return_value
        instance.check_readiness.return_value = (True, [])

        result = check_16_agent_probe(
            project_dir=tmp_path,
            project_name="smoke_test",
            lifecycle_mode="RUN",
            stage_label="STAGE_BUILD",
        )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_16_fail_when_probe_violations(tmp_path):
    """check_16 retourne FAIL si AgentProbe signale des violations."""
    from src.pipelines.vibe_check._vc_agents import check_16_agent_probe

    with patch(
        "src.core.agent_probe.AgentProbe",
        autospec=True,
    ) as MockProbe:
        instance = MockProbe.return_value
        instance.check_readiness.return_value = (False, ["herdr absent", "opencode KO"])

        result = check_16_agent_probe(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")

    assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# check_19_standards_graph — retourne dict avec status PASS/FAIL
# ---------------------------------------------------------------------------


def test_check_19_returns_dict(tmp_path):
    """check_19_standards_graph doit retourner un dict avec les clés 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_agents import check_19_standards_graph

    result = check_19_standards_graph(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result
    assert "status" in result
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_19_status_is_string(tmp_path):
    """Le statut retourné par check_19 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_agents import check_19_standards_graph

    result = check_19_standards_graph(tmp_path, "smoke_test", "RUN", "STAGE_PLAN_GRILL")
    assert isinstance(result["status"], str) and result["status"]
