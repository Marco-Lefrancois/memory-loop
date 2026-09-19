"""
tests/test_dashboard_context_gauge.py — Banc de test unitaire pour MLOOP-073-FE.

Couvre les 4 Piliers Gherkin du récit MLOOP-073-FE :
1. Pilier 1 : Chemin Nominal (Smart Zone < 40%, vert émeraude, 25k/128k = 20%)
2. Pilier 2 : Exceptions & Seuils (Caution Zone 40-60%, ambre, 55k/128k = 43%)
3. Pilier 3 : Résilience & Dumb Zone (> 60%, écarlate clignotant, 85k/128k = 66%)
4. Pilier 4 : UX & Changement de projet (Multi-projets, calibrage dynamique)
"""
import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app
from src.dashboard.routers.overview import ContextGaugeEngine


@pytest.fixture
def client():
    return TestClient(app)


# ── PILIER 1 : CHEMIN NOMINAL (SMART ZONE 0-40%) ────────────────────────────

def test_smart_zone_nominal_calculation():
    """Vérifie le calcul déterministe en Smart Zone (< 40%)."""
    res = ContextGaugeEngine.evaluate_context(tokens_used=25000, window_size=128000)
    assert res["zone"] == "SMART"
    assert res["percentage"] == 20
    assert "SMART ZONE" in res["badge_text"]
    assert "🟢" in res["badge_text"]
    assert res["zone_color"] == "emerald"
    assert res["ratio"] == pytest.approx(25000 / 128000, rel=1e-2)


def test_smart_zone_endpoint(client):
    """Vérifie l'endpoint /api/overview/context-health en Smart Zone."""
    resp = client.get("/api/overview/context-health?tokens=25000&window=128000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "SMART"
    assert data["percentage"] == 20
    assert "🟢 SMART ZONE : 20%" in data["badge_text"]


# ── PILIER 2 : EXCEPTIONS & SEUILS (CAUTION ZONE 40-60%) ────────────────────

def test_caution_zone_calculation():
    """Vérifie le franchissement du seuil de 40% (Caution Zone)."""
    res = ContextGaugeEngine.evaluate_context(tokens_used=55000, window_size=128000)
    assert res["zone"] == "CAUTION"
    assert res["percentage"] == 43
    assert "CAUTION ZONE" in res["badge_text"]
    assert "🟡" in res["badge_text"]
    assert res["zone_color"] == "amber"
    assert "compactage" in res["recommendation"].lower()


def test_caution_zone_endpoint(client):
    """Vérifie l'endpoint /api/overview/context-health en Caution Zone."""
    resp = client.get("/api/overview/context-health?tokens=55000&window=128000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "CAUTION"
    assert data["percentage"] == 43
    assert "🟡 CAUTION ZONE : 43%" in data["badge_text"]


# ── PILIER 3 : RÉSILIENCE & DUMB ZONE (> 60%) ──────────────────────────────

def test_dumb_zone_critical_calculation():
    """Vérifie l'alerte critique lors du franchissement de la Dumb Zone (> 60%)."""
    res = ContextGaugeEngine.evaluate_context(tokens_used=85000, window_size=128000)
    assert res["zone"] == "DUMB"
    assert res["percentage"] == 66
    assert "DUMB ZONE" in res["badge_text"]
    assert "🔴" in res["badge_text"]
    assert res["zone_color"] == "rose"
    assert res["is_critical"] is True
    assert "clean-slate" in res["recommendation"].lower()


def test_dumb_zone_endpoint(client):
    """Vérifie l'endpoint /api/overview/context-health en Dumb Zone critique."""
    resp = client.get("/api/overview/context-health?tokens=85000&window=128000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "DUMB"
    assert data["percentage"] == 66
    assert "🔴 DUMB ZONE : 66%" in data["badge_text"]
    assert data["is_critical"] is True


# ── PILIER 4 : UX & MULTI-PROJETS ───────────────────────────────────────────

def test_context_health_project_resolution(client):
    """Vérifie l'évaluation de contexte pour un projet spécifique avec fallback sain."""
    resp = client.get("/api/overview/context-health?project=mLoop")
    assert resp.status_code == 200
    data = resp.json()
    assert "project_name" in data
    assert "tokens_used" in data
    assert "window_size" in data
    assert data["window_size"] == 128000
    assert data["zone"] in ("SMART", "CAUTION", "DUMB")
