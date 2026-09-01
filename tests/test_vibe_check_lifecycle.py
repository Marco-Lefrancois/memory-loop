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
