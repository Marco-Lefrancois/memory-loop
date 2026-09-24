"""
Tests miroirs OQ-170-04 — Famille : frontend
Module testé : src.pipelines.vibe_check._vc_frontend

Checks couverts :
  - check_21_visual_anchor (Check 21)

Stratégie : smoke tests — import du symbole + assertion callable + vérification
de la structure de retour (dict avec 'check' et 'status'). Tests comportementaux
sur des stories frontend avec et sans ancrage visuel pour valider la logique
de WARNING (ADR-0384 — Ancrage Visuel / Contrat Visuel Premier).
"""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Import & Smoke — le symbole doit être importable et appelable
# ---------------------------------------------------------------------------


def test_import_check_21_visual_anchor():
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    assert callable(check_21_visual_anchor)


# ---------------------------------------------------------------------------
# check_21_visual_anchor — retourne dict
# ---------------------------------------------------------------------------


def test_check_21_returns_dict(tmp_path):
    """check_21_visual_anchor doit retourner un dict avec 'check' et 'status'."""
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    result = check_21_visual_anchor(
        project_dir=tmp_path,
        project_name="smoke_test",
        lifecycle_mode="INIT",
        stage_label="STAGE_INIT",
    )

    assert isinstance(result, dict), f"Attendu dict, reçu {type(result)}"
    assert "check" in result, f"Clé 'check' manquante : {result}"
    assert "status" in result, f"Clé 'status' manquante : {result}"
    assert result["status"] in ("PASS", "FAIL", "WARNING")


def test_check_21_init_mode_passes(tmp_path):
    """En mode INIT (hors Phase ≥ 2), check_21 retourne PASS (non applicable)."""
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    result = check_21_visual_anchor(tmp_path, "smoke_test", "INIT", "STAGE_INIT")
    assert result["status"] == "PASS"


def test_check_21_run_no_stories_passes(tmp_path):
    """En mode RUN sans stories, check_21 retourne PASS (rien à auditer)."""
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    (tmp_path / "backlog" / "stories").mkdir(parents=True)
    result = check_21_visual_anchor(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert result["status"] == "PASS"


def test_check_21_run_frontend_story_without_anchor_warns(tmp_path):
    """
    En mode RUN, une story frontend sans référence de maquette déclenche WARNING.
    La story doit avoir layer: frontend dans le frontmatter.
    """
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    stories_dir = tmp_path / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    story = stories_dir / "FE-001.md"
    story.write_text(
        "---\n"
        "id: FE-001\n"
        "layer: frontend\n"
        "status: READY_FOR_DEV\n"
        "---\n"
        "# Titre sans maquette\n\n"
        "Description sans référence visuelle.\n",
        encoding="utf-8",
    )

    result = check_21_visual_anchor(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert result["status"] == "WARNING", (
        f"Une story frontend sans maquette doit déclencher WARNING, reçu : {result['status']}"
    )


def test_check_21_run_frontend_story_with_anchor_passes(tmp_path):
    """
    En mode RUN, une story frontend avec référence de maquette retourne PASS.
    """
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    stories_dir = tmp_path / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    story = stories_dir / "FE-002.md"
    story.write_text(
        "---\n"
        "id: FE-002\n"
        "layer: frontend\n"
        "status: READY_FOR_DEV\n"
        "---\n"
        "# Titre avec maquette\n\n"
        "Voir maquette : docs/05-assets/maquettes/ecran_login.svg\n",
        encoding="utf-8",
    )

    result = check_21_visual_anchor(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert result["status"] == "PASS"


def test_check_21_backend_story_excluded(tmp_path):
    """Les stories backend doivent être exclues du contrôle d'ancrage visuel."""
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    stories_dir = tmp_path / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    story = stories_dir / "BE-001.md"
    story.write_text(
        "---\n"
        "id: BE-001\n"
        "layer: backend\n"
        "status: READY_FOR_DEV\n"
        "---\n"
        "# Story Backend sans maquette\n\n"
        "Logique serveur pure, aucune maquette requise.\n",
        encoding="utf-8",
    )

    result = check_21_visual_anchor(tmp_path, "smoke_test", "RUN", "STAGE_BUILD")
    assert result["status"] == "PASS", (
        f"Les stories backend doivent être exclues du check visuel, reçu : {result['status']}"
    )


def test_check_21_check_field_is_string(tmp_path):
    """Le champ 'check' de check_21 est une chaîne non vide."""
    from src.pipelines.vibe_check._vc_frontend import check_21_visual_anchor

    result = check_21_visual_anchor(tmp_path, "smoke_test", "RUN", "STAGE_PLAN_GRILL")
    assert isinstance(result["check"], str) and result["check"]
