"""
Tests TDD pour l'archivage réversible et la sécurité anti-perte de données de clean_premature_stories.
Conformité : ADR-0339 (Quality Gates) et ADR-0369 (Standards de Robustesse Senior).
Lacune : L-08 (Perte de données par unlink destructif).
"""

import shutil
from pathlib import Path
import pytest

from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
)


@pytest.fixture
def sow_project_with_stories(tmp_path: Path) -> Path:
    """Crée un projet en STAGE_1_SOW avec des stories et des preuves prématurées."""
    proj = tmp_path / "Projects" / "SowCleanupTestProject"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "01-architecture").mkdir(parents=True, exist_ok=True)
    (proj / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (proj / "memory" / "evidence").mkdir(parents=True, exist_ok=True)

    # Initialisation en STAGE_1_SOW
    sow_file = proj / "docs" / "01-architecture" / "SOW_Test.md"
    sow_file.write_text("# SOW Validé", encoding="utf-8")
    state = ProjectLifecycleManager.init_lifecycle(proj)
    assert state.current_stage == ProjectLifecycleStage.STAGE_1_SOW

    # Fichiers de stories prématurées
    s1 = proj / "backlog" / "stories" / "SHOP-101.md"
    s1.write_text("# Contenu Précieux Story 101", encoding="utf-8")
    s2 = proj / "backlog" / "stories" / "SHOP-102.md"
    s2.write_text("# Contenu Précieux Story 102", encoding="utf-8")
    readme = proj / "backlog" / "stories" / "README.md"
    readme.write_text("# Documentation Backlog", encoding="utf-8")

    # Fichiers de preuves prématurées
    e1 = proj / "memory" / "evidence" / "SHOP-101_evidence.json"
    e1.write_text('{"evidence": "data_101"}', encoding="utf-8")
    d1 = proj / "memory" / "evidence" / "SHOP-101_fact_dossier.md"
    d1.write_text("# Fact Dossier 101", encoding="utf-8")

    yield proj

    if proj.exists():
        shutil.rmtree(proj.parent.parent, ignore_errors=True)


def test_premature_stories_are_archived_not_unlinked(sow_project_with_stories: Path) -> None:
    """Vérifie que les stories et EvidencePacks sont déplacés dans memory/archive/ et non détruits."""
    res = ProjectLifecycleManager.clean_premature_stories(sow_project_with_stories, confirm=True)

    # Vérifier le retour
    assert len(res["deleted_stories"]) == 2
    assert len(res["deleted_evidence"]) == 2
    assert "archive_dir" in res

    archive_dir = Path(res["archive_dir"])
    assert archive_dir.exists()
    assert archive_dir.is_dir()

    # 1. Vérifier que les fichiers d'origine ont bien été déplacés (n'existent plus dans backlog)
    assert not (sow_project_with_stories / "backlog" / "stories" / "SHOP-101.md").exists()
    assert not (sow_project_with_stories / "backlog" / "stories" / "SHOP-102.md").exists()
    assert not (sow_project_with_stories / "memory" / "evidence" / "SHOP-101_evidence.json").exists()
    assert not (sow_project_with_stories / "memory" / "evidence" / "SHOP-101_fact_dossier.md").exists()

    # 2. Le README.md n'a PAS été déplacé
    assert (sow_project_with_stories / "backlog" / "stories" / "README.md").exists()

    # 3. Vérifier la présence et l'intégrité du contenu dans l'archive
    archived_s1 = archive_dir / "SHOP-101.md"
    archived_s2 = archive_dir / "SHOP-102.md"
    archived_e1 = archive_dir / "SHOP-101_evidence.json"
    archived_d1 = archive_dir / "SHOP-101_fact_dossier.md"

    assert archived_s1.exists()
    assert archived_s1.read_text(encoding="utf-8") == "# Contenu Précieux Story 101"

    assert archived_s2.exists()
    assert archived_s2.read_text(encoding="utf-8") == "# Contenu Précieux Story 102"

    assert archived_e1.exists()
    assert archived_e1.read_text(encoding="utf-8") == '{"evidence": "data_101"}'

    assert archived_d1.exists()
    assert archived_d1.read_text(encoding="utf-8") == "# Fact Dossier 101"


def test_no_archive_when_stage_is_phase2_or_higher(sow_project_with_stories: Path) -> None:
    """Vérifie que rien n'est touché ni déplacé si le projet est en Phase 2 ou supérieure."""
    # Simuler progression en STAGE_2_PLAN_GRILL
    state = ProjectLifecycleManager.get_state(sow_project_with_stories)
    state.current_stage = ProjectLifecycleStage.STAGE_2_PLAN_GRILL
    ProjectLifecycleManager.save_state(sow_project_with_stories, state, allow_regression=True)

    res = ProjectLifecycleManager.clean_premature_stories(sow_project_with_stories, confirm=True)
    assert len(res["deleted_stories"]) == 0
    assert len(res["deleted_evidence"]) == 0

    # Les fichiers sont restés intacts
    assert (sow_project_with_stories / "backlog" / "stories" / "SHOP-101.md").exists()
    assert (sow_project_with_stories / "backlog" / "stories" / "SHOP-102.md").exists()


def test_cleanup_refused_without_confirmation(sow_project_with_stories: Path) -> None:
    """Vérifie qu'un appel avec confirm=False refuse l'opération pour empêcher toute suppression accidentelle."""
    res = ProjectLifecycleManager.clean_premature_stories(sow_project_with_stories, confirm=False)
    assert res.get("status") == "refused"
    assert len(res.get("deleted_stories", [])) == 0

    # Rien n'a été déplacé
    assert (sow_project_with_stories / "backlog" / "stories" / "SHOP-101.md").exists()
