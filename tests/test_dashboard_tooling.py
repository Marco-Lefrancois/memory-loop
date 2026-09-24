"""Tests unitaires pour le routeur Dashboard Tooling (MLOOP-223-FE)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app

client = TestClient(app)


def test_get_tooling_status():
    """Vérifie que la route GET /api/tooling/status répond avec succès."""
    response = client.get("/api/tooling/status")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "tools" in data
    assert "opencode" in data["tools"]
    assert "plannotator" in data["tools"]
    assert "litellm" in data["tools"]
    assert "graphify" in data["tools"]


def test_get_tooling_status_with_project(tmp_path: Path):
    """Vérifie la détection des plans de projet via /api/tooling/status."""
    proj = tmp_path / "Projects" / "TestToolingProject"
    plan_dir = proj / "memory" / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "MLOOP-220-BE_phase_plan.annotated.md").write_text("# Plan", encoding="utf-8")

    with patch("src.dashboard.routers.tooling.resolve_project_path", return_value=proj):
        response = client.get("/api/tooling/status?project=TestToolingProject")
        assert response.status_code == 200
        data = response.json()
        assert data["tools"]["plannotator"]["plans_count"] >= 1
