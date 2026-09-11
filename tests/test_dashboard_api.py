# -*- coding: utf-8 -*-
"""Tests unitaires et d'intégration pour le Dashboard d'Observabilité mLoop."""

import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app

client = TestClient(app)


def test_dashboard_health():
    """Vérifie que l'endpoint de santé répond avec les drapeaux souverains."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["engine"] == "Memory Loop (mLoop)"
    assert data["docker_free"] is True
    assert "active_project" in data


def test_dashboard_projects():
    """Vérifie que la liste des projets inclut au moins le projet cadre mLoop."""
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert "active_project" in data
    assert isinstance(data["projects"], list)
    assert len(data["projects"]) > 0
    assert any(p in data["projects"] for p in ("Memory Loop", "mLoop"))


def test_dashboard_metrics():
    """Vérifie la structure des métriques de jetons et coûts agrégés."""
    response = client.get("/api/metrics?project=Memory%20Loop")
    assert response.status_code == 200
    data = response.json()
    assert "total_tokens" in data
    assert "total_cost_usd" in data
    assert "models_breakdown" in data
    assert "top_actions" in data
    assert "recent_interactions" in data
    assert isinstance(data["total_tokens"], int)
    assert isinstance(data["total_cost_usd"], float)


def test_dashboard_events():
    """Vérifie l'extraction du journal d'événements live."""
    response = client.get("/api/events?limit=20")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data
    assert isinstance(data["events"], list)
    assert data["count"] <= 20


def test_dashboard_stories():
    """Vérifie le scan des User Stories du backlog et des EvidencePacks."""
    response = client.get("/api/stories?project=Memory%20Loop")
    assert response.status_code == 200
    data = response.json()
    assert "stories" in data
    assert "total_stories" in data
    assert "status_counts" in data
    assert isinstance(data["stories"], list)


def test_dashboard_graph():
    """Vérifie la restitution des métriques du graphe de connaissances."""
    response = client.get("/api/graph?project=Memory%20Loop")
    assert response.status_code == 200
    data = response.json()
    assert "total_nodes" in data
    assert "total_edges" in data
    assert isinstance(data["total_nodes"], int)
    assert isinstance(data["total_edges"], int)


def test_dashboard_state():
    """Vérifie que l'état des 6 phases du cycle est correctement formaté."""
    response = client.get("/api/state?project=Memory%20Loop")
    assert response.status_code == 200
    data = response.json()
    assert "phases" in data
    assert "pipeline" in data
    assert len(data["phases"]) == 6


def test_dashboard_html_index():
    """Vérifie que la route racine sert bien l'interface HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "mLoop Sovereign Observability Hub" in response.text


def test_dashboard_project_select():
    """Vérifie la persistance du projet sélectionné via l'API."""
    response = client.post("/api/project/select", json={"project": "BoireFrere_Segment2"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["active_project"] == "BoireFrere_Segment2"

    # Vérifier que GET /api/projects reflète la mise à jour
    r_check = client.get("/api/projects")
    assert r_check.status_code == 200
    assert r_check.json()["active_project"] == "BoireFrere_Segment2"

