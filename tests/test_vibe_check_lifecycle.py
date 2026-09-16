import pytest
import shutil
from pathlib import Path
from src.pipelines.vibe_check import detect_project_lifecycle_stage, run_vibe_check


@pytest.fixture
def temp_project_dir(tmp_path):
    """Crée un répertoire temporaire simulant un projet sous Projects/<nom>."""
    proj_dir = tmp_path / "Projects" / "TestLifecycleProject"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "docs" / "00-ingested").mkdir(parents=True, exist_ok=True)
    (proj_dir / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj_dir / "memory" / "evidence").mkdir(parents=True, exist_ok=True)
    yield proj_dir
    if proj_dir.exists():
        shutil.rmtree(proj_dir.parent.parent, ignore_errors=True)


def test_detect_explicit_stages(temp_project_dir):
    """Vérifie le mapping explicite des étapes vers INIT et RUN."""
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="init") == ("INIT", "STAGE_INIT")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="sow") == ("INIT", "STAGE_SOW")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="spec") == ("INIT", "STAGE_SPEC")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="tshirt") == ("INIT", "STAGE_INIT")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="plan") == ("RUN", "STAGE_PLAN_GRILL")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="build") == ("RUN", "STAGE_BUILD")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="validate") == ("RUN", "STAGE_VALIDATE")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="ship") == ("RUN", "STAGE_SHIP_SYNC")
    assert detect_project_lifecycle_stage(temp_project_dir, explicit_stage="run") == ("RUN", "STAGE_RUN")


def test_detect_auto_cold_start(temp_project_dir):
    """Vérifie l'auto-détection en mode INIT lorsqu'aucun backlog n'est créé."""
    mode, stage = detect_project_lifecycle_stage(temp_project_dir)
    assert mode == "INIT"
    assert stage == "STAGE_INIT"


def test_detect_auto_sow_phase(temp_project_dir):
    """Vérifie la détection de STAGE_SOW en présence d'un SOW sans récits."""
    sow_file = temp_project_dir / "docs" / "01-architecture" / "SOW_TestLifecycleProject.md"
    sow_file.write_text("# SOW Document", encoding="utf-8")
    mode, stage = detect_project_lifecycle_stage(temp_project_dir)
    assert mode == "INIT"
    assert stage == "STAGE_SOW"


def test_detect_auto_sow_phase_with_macro_backlog(temp_project_dir):
    """Vérifie la détection de STAGE_SOW en présence d'un SOW et d'un sprint_backlog aux statuts OPEN/BACKLOG."""
    sow_file = temp_project_dir / "docs" / "01-architecture" / "SOW_TestLifecycleProject.md"
    sow_file.write_text("# SOW Document", encoding="utf-8")
    backlog_file = temp_project_dir / "backlog" / "sprint_backlog.md"
    backlog_file.write_text(
        "# Backlog\n\n| ID | Titre | Composant | Statut |\n| :--- | :--- | :--- | :--- |\n| US-01 | Test | Auth | OPEN |\n| US-02 | Test 2 | Profil | BACKLOG |\n",
        encoding="utf-8",
    )
    mode, stage = detect_project_lifecycle_stage(temp_project_dir)
    assert mode == "INIT"
    assert stage == "STAGE_SOW"


def test_detect_auto_plan_grill_when_story_engaged_in_backlog(temp_project_dir):
    """Vérifie que la transition d'un récit vers IN_ANALYZE fait basculer le projet vers STAGE_PLAN_GRILL."""
    sow_file = temp_project_dir / "docs" / "01-architecture" / "SOW_TestLifecycleProject.md"
    sow_file.write_text("# SOW Document", encoding="utf-8")
    backlog_file = temp_project_dir / "backlog" / "sprint_backlog.md"
    backlog_file.write_text(
        "# Backlog\n\n| ID | Titre | Composant | Statut |\n| :--- | :--- | :--- | :--- |\n| US-01 | Test | Auth | IN_ANALYZE |\n",
        encoding="utf-8",
    )
    mode, stage = detect_project_lifecycle_stage(temp_project_dir)
    assert mode == "RUN"
    assert stage == "STAGE_PLAN_GRILL"


def test_detect_auto_run_with_stories(temp_project_dir):
    """Vérifie la détection du mode RUN en présence de récits physiques."""
    story_file = temp_project_dir / "backlog" / "stories" / "US-01.md"
    story_file.write_text("# Story 1", encoding="utf-8")
    mode, stage = detect_project_lifecycle_stage(temp_project_dir)
    assert mode == "RUN"
    assert stage == "STAGE_PLAN_GRILL"


def test_vibe_check_init_mode_passes_ssot():
    """Vérifie que run_vibe_check en mode INIT ne fait pas échouer l'intégrité SSOT si sprint_backlog.md est absent."""
    proj_name = "ColdStartProject"
    proj_dir = Path("Projects") / proj_name
    proj_dir.mkdir(parents=True, exist_ok=True)
    try:
        (proj_dir / "reference").mkdir(parents=True, exist_ok=True)
        (proj_dir / "docs" / "00-ingested").mkdir(parents=True, exist_ok=True)
        (proj_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
        (proj_dir / "memory" / "evidence").mkdir(parents=True, exist_ok=True)

        res = run_vibe_check(proj_name, stage="init")
        assert res["lifecycle_mode"] == "INIT"
        
        # Trouver le check SSOT
        ssot_check = next(c for c in res["checks"] if "Intégrité SSOT" in c["check"])
        assert ssot_check["status"] == "PASS"
        assert "Phase INIT" in ssot_check["check"]
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


def test_vibe_check_run_mode_fails_when_backlog_missing():
    """Vérifie que run_vibe_check en mode RUN fait échouer l'intégrité SSOT si sprint_backlog.md est manquant."""
    proj_name = "RunProjectMissingBacklog"
    proj_dir = Path("Projects") / proj_name
    proj_dir.mkdir(parents=True, exist_ok=True)
    try:
        (proj_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
        (proj_dir / "memory" / "evidence").mkdir(parents=True, exist_ok=True)

        res = run_vibe_check(proj_name, stage="run")
        assert res["lifecycle_mode"] == "RUN"
        
        # Trouver le check SSOT
        ssot_check = next(c for c in res["checks"] if "Intégrité SSOT" in c["check"])
        assert ssot_check["status"] == "FAIL"
        assert "sprint_backlog.md requis" in ssot_check["check"]
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


def test_vibe_check_fails_on_premature_stories_in_sow_phase():
    """Vérifie que run_vibe_check en phase SOW échoue fermement (Check 13) si des stories existent."""
    from src.core.lifecycle import ProjectLifecycleManager, ProjectLifecycleStage
    proj_name = "PrematureStoriesProject"
    proj_dir = Path("Projects") / proj_name
    proj_dir.mkdir(parents=True, exist_ok=True)
    try:
        (proj_dir / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
        (proj_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
        (proj_dir / "memory" / "evidence").mkdir(parents=True, exist_ok=True)

        sow_file = proj_dir / "docs" / "01-architecture" / f"SOW_{proj_name}.md"
        sow_file.write_text("# SOW", encoding="utf-8")

        # Initialiser en STAGE_1_SOW
        state = ProjectLifecycleManager.init_lifecycle(proj_dir, initial_stage=ProjectLifecycleStage.STAGE_1_SOW)

        # Créer une story prématurée sous backlog/stories/
        premature_story = proj_dir / "backlog" / "stories" / "US-01.md"
        premature_story.write_text("# Premature", encoding="utf-8")

        res = run_vibe_check(proj_name)
        phase_check = next(c for c in res["checks"] if "Interdiction de Saut de Phase" in c["check"])
        assert phase_check["status"] == "FAIL"
        assert "interdit(s) en étape 'STAGE_1_SOW'" in phase_check["check"]

        # Nettoyer les stories prématurées
        ProjectLifecycleManager.clean_premature_stories(proj_dir)

        # Re-tester le Vibe-Check -> doit maintenant passer le Check 13
        res_clean = run_vibe_check(proj_name)
        phase_check_clean = next(c for c in res_clean["checks"] if "Interdiction de Saut de Phase" in c["check"])
        assert phase_check_clean["status"] == "PASS"
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)
