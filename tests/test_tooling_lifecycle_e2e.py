"""
Harnais de Certification E2E du Cycle Tooling (MLOOP-224-FULL / ADR-014).

Valide le cycle de vie outillage complet sur un projet test isolé :
  1. Cartographie Wayfinder (Destination, Frontière, Résolution de ticket HITL/AFK).
  2. Initialisation déclarative OpenCode (.opencode/opencode.json).
  3. Génération et validation headless Plannotator (memory/plan/*.annotated.md).
  4. Absence absolue de fichiers ou répertoires orphelins à la racine de Memory Loop.
  5. Télémétrie Dashboard (/api/tooling/status).

Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.commands.handlers.opencode import handle_init, handle_status
from src.commands.handlers.plannotator import handle_approve, handle_plannotator
from src.dashboard.server import app
from src.pipelines.wayfinder import WayfinderEngine
from src.state import LoopState


@pytest.fixture
def isolated_tooling_project(tmp_path: Path):
    """Prépare un environnement de projet isolé pour la certification E2E."""
    project_root = tmp_path / "Projects" / "TestToolingProject"
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "memory" / "plan").mkdir(parents=True, exist_ok=True)
    (project_root / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    return project_root


def test_tooling_e2e_full_lifecycle(isolated_tooling_project: Path):
    """Exécute la boucle E2E complète de l'écosystème outillage."""
    proj = isolated_tooling_project
    state = LoopState(project_name="TestToolingProject")

    # ── Étape 1 : Cartographie Wayfinder ───────────────────────────
    wf = WayfinderEngine(proj)
    map_file = wf.init_map("Initiative E2E Tooling", goal="Certification souveraine de l'outillage")
    assert map_file.exists()
    assert map_file == proj / "memory" / "wayfinder" / "wayfinder_map.md"

    wf.add_ticket("T-01", "Choix du modèle de prompt", "Arbitrage HITL pour LiteLLM", kind="HITL")
    wf.add_ticket("T-02", "Mesure latence", "Recherche AFK", kind="AFK", blocked_by=["T-01"])

    frontier_step1 = wf.get_frontier()
    assert len(frontier_step1) == 1
    assert frontier_step1[0]["id"] == "T-01"

    # Résolution du ticket à la frontière
    resolved = wf.resolve_ticket("T-01", "Modèle standardisé sur LiteLLM port 4000")
    assert resolved is True

    frontier_step2 = wf.get_frontier()
    assert len(frontier_step2) == 1
    assert frontier_step2[0]["id"] == "T-02"
    assert frontier_step2[0]["kind"] == "AFK"

    # ── Étape 2 : Configuration OpenCode ───────────────────────────
    args_opencode = argparse.Namespace(project="TestToolingProject", action="init")
    code_init = handle_init(args_opencode, state, proj)
    assert code_init == 0

    cfg_path = proj / ".opencode" / "opencode.json"
    assert cfg_path.exists()
    cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg_data["providers"]["litellm"]["endpoint"] == "http://localhost:4000/v1"

    # ── Étape 3 : Validation Headless Plannotator ───────────────────
    plan_dir = proj / "memory" / "plan"
    initial_plan = plan_dir / "MLOOP-220-BE_phase_plan.md"
    initial_plan.write_text("# Plan de Phase MLOOP-220-BE\nSpécifications techniques", encoding="utf-8")

    args_plannotator = argparse.Namespace(
        project="TestToolingProject",
        story="MLOOP-220-BE",
        approve=True,
        file=str(initial_plan),
        action="approve",
    )
    code_approve = handle_approve(args_plannotator, state, proj)
    assert code_approve == 0

    annotated_plan = plan_dir / "MLOOP-220-BE_phase_plan.annotated.md"
    assert annotated_plan.exists()
    annotated_content = annotated_plan.read_text(encoding="utf-8")
    assert "Plannotator Approved (Headless CI/CD Mode)" in annotated_content

    # ── Étape 4 : Invariant Zéro-Orphelin à la racine ──────────────
    assert not Path("plannotator").exists()

    # ── Étape 5 : API Dashboard & Télémétrie ──────────────────────
    client = TestClient(app)
    with patch("src.dashboard.routers.tooling.resolve_project_path", return_value=proj):
        res = client.get("/api/tooling/status?project=TestToolingProject")
        assert res.status_code == 200
        payload = res.json()
        assert payload["status"] == "ok"
        assert payload["tools"]["opencode"]["configured"] is True
        assert payload["tools"]["plannotator"]["plans_count"] >= 1
