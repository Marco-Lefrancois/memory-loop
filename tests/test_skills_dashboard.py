# -*- coding: utf-8 -*-
"""
tests/test_skills_dashboard.py — Tests exhaustifs pour MLOOP-243-FE (Dashboard Skills Health).
Valide la conformité ADR-0202 (<= 300 lignes), ADR-0369, ADR-0379 (Zéro CDN) et ADR-0389.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app
from scripts.generate_skills_dashboard import ensure_skills_eval_summary, verify_dashboard_html


@pytest.fixture
def client() -> TestClient:
    """Client de test FastAPI pour les endpoints du dashboard."""
    return TestClient(app)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_skills_health_page_endpoint(client: TestClient) -> None:
    """Vérifie que la route GET /skills-health retourne la page HTML statique (200 OK)."""
    response = client.get("/skills-health")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    content = response.text
    assert "<!DOCTYPE html>" in content
    assert "Cockpit de Santé des Compétences Agentiques" in content
    assert "radarSvg" in content
    assert "/api/skills/evals" in content


def test_skills_evals_api_endpoint(client: TestClient) -> None:
    """Vérifie que l'API GET /api/skills/evals retourne la matrice complète des 39 skills."""
    response = client.get("/api/skills/evals")
    assert response.status_code == 200
    data = response.json()
    assert "total_skills" in data
    assert data["total_skills"] == 39
    assert "average_score" in data
    assert "results" in data
    assert len(data["results"]) == 39

    # Vérification d'un item
    item = data["results"][0]
    assert "skill_name" in item
    assert "verdict" in item
    assert "total_score" in item
    assert "scores_breakdown" in item


def test_skills_health_html_has_zero_external_cdn(repo_root: Path) -> None:
    """Conformité ADR-0379 (Confinement Sandbox) : Zéro CDN externe dans le HTML statique."""
    html_file = repo_root / "src" / "dashboard" / "skills_health.html"
    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")

    # Interdiction des scripts externes vers des CDN (unpkg, cdnjs, jsdelivr, etc.)
    external_scripts = re.findall(r'<script[^>]+src=["\'](http[s]?://[^"\']+)["\']', content, re.IGNORECASE)
    assert len(external_scripts) == 0, f"Scripts CDN externes interdits détectés : {external_scripts}"

    external_links = re.findall(r'<link[^>]+href=["\'](http[s]?://[^"\']+)["\']', content, re.IGNORECASE)
    assert len(external_links) == 0, f"Feuilles de style CDN externes interdites détectées : {external_links}"


def test_generate_skills_dashboard_script_execution(repo_root: Path) -> None:
    """Vérifie que le script d'automatisation s'exécute sans erreur et valide les fichiers."""
    json_path = ensure_skills_eval_summary(repo_root, force_refresh=False)
    assert json_path.exists()
    html_path = verify_dashboard_html(repo_root)
    assert html_path.exists()
