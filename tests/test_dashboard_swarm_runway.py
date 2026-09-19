"""
tests/test_dashboard_swarm_runway.py — Banc de test unitaire pour MLOOP-074-FULL.

Couvre les 4 Piliers Gherkin du récit MLOOP-074-FULL :
1. Pilier 1 : Chemin Nominal (Affichage du runway de handoffs récents & Ping-Pong Guard conforme)
2. Pilier 2 : Exceptions & Seuils (Alerte visuelle et statut écarlate lors d'un cycle de récursion)
3. Pilier 3 : Résilience & Mode Dégradé (Empty State sans plantage si aucun épisode Dream RSI)
4. Pilier 4 : UX & Observabilité (Comparateur contrefactuel double colonne pi0 vs pi* avec gains explicites)
"""
import pytest
from fastapi.testclient import TestClient

from src.dashboard.server import app
from src.agents.circuit_breaker import PingPongGuard


@pytest.fixture
def client():
    return TestClient(app)


# ── PILIER 1 : CHEMIN NOMINAL (RUNWAY ACTIF & PING-PONG CONFORME) ───────────

def test_swarm_handoffs_nominal_endpoint(client):
    """Vérifie l'endpoint /api/swarm/handoffs avec des handoffs nominaux."""
    resp = client.get("/api/swarm/handoffs?project=mLoop")
    assert resp.status_code == 200
    data = resp.json()
    assert "project_name" in data
    assert "ping_pong_guard" in data
    assert "handoffs" in data
    assert isinstance(data["handoffs"], list)
    assert data["ping_pong_guard"]["max_consecutive_handoffs"] == 3
    assert "status_badge" in data["ping_pong_guard"]


# ── PILIER 2 : EXCEPTIONS & ALERTES BOUCLE PING-PONG ────────────────────────

def test_swarm_handoffs_tripped_loop_detection(client, monkeypatch):
    """Vérifie le déclenchement de l'alerte écarlate lorsque PingPongGuard est disjoncté."""
    # Simuler un guard disjoncté avec cycle A -> B -> A -> B
    guard = PingPongGuard(max_consecutive_handoffs=3)
    guard.record_handoff("orchestrator", "worker", produced_artifact=False)
    guard.record_handoff("worker", "sentinel", produced_artifact=False)
    try:
        guard.record_handoff("sentinel", "worker", produced_artifact=False)
    except Exception:
        pass  # trip attendu lorsque le seuil de 3 handoffs consécutifs est atteint

    # Forcer l'utilisation de ce guard dans le routeur swarm
    from src.dashboard.routers import swarm
    monkeypatch.setattr(swarm, "_get_project_guard", lambda proj: guard)

    resp = client.get("/api/swarm/handoffs?project=mLoop")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ping_pong_guard"]["is_tripped"] is True
    assert "ALERTE BOUCLE DÉTECTÉE" in data["ping_pong_guard"]["status_badge"]
    assert data["ping_pong_guard"]["status_color"] == "rose"
    assert len(data["handoffs"]) >= 3
    assert data["handoffs"][-1]["is_loop"] is True


# ── PILIER 3 : RÉSILIENCE & EMPTY STATE (SANS ÉPISODES) ─────────────────────

def test_dream_rsi_diff_empty_state_resilience(client, monkeypatch):
    """Vérifie le retour gracieux (empty state) si aucun épisode de replay n'est disponible."""
    from src.dashboard.routers import dream_rsi
    monkeypatch.setattr(dream_rsi.ReplaySimulator, "load_from_project", lambda p: [])

    resp = client.get("/api/dream-rsi/diff?project=EmptyProject")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_episodes"] is False
    assert data["episodes_count"] == 0
    assert "comparison" in data
    assert len(data["comparison"]) == 0
    assert "Aucun épisode" in data["message"]


# ── PILIER 4 : UX & OBSERVABILITÉ COMPARATEUR PI0 VS PI* ─────────────────────

def test_dream_rsi_diff_nominal_comparison(client):
    """Vérifie la présence et la structure du comparateur double colonne pi0 vs pi*."""
    resp = client.get("/api/dream-rsi/diff?project=mLoop")
    assert resp.status_code == 200
    data = resp.json()
    assert "project_name" in data
    assert "comparison" in data
    assert "gain_vs_pi0" in data
    assert "tokens_saved" in data
    assert "eliminated_bottleneck_reason" in data

    if data["has_episodes"]:
        assert len(data["comparison"]) > 0
        first_step = data["comparison"][0]
        assert "step_index" in first_step
        assert "pi0" in first_step
        assert "pi_star" in first_step
        assert "status" in first_step["pi0"]
        assert "status" in first_step["pi_star"]
        assert "cost_tokens" in first_step["pi0"]
