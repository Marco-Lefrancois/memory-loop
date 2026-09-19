"""
Tests Déterministes du Disjoncteur Anti-Boucle Ping-Pong Guard (MLOOP-070-BE / ADR-0380).
Couverture rigoureuse des 4 Piliers Gherkin :
1. Nominal : Délégations linéaires sous le seuil maximal (N < 3).
2. Exceptions : Détection de cycle alterné (N >= 3) et rejet de rôles invalides.
3. Résilience : Réinitialisation sur écriture d'artefact et armement HITL.
4. UX / Observabilité : Payload télémétrique et traçabilité événementielle.
"""
import pytest
from src.state import LoopState
from src.agents.circuit_breaker import PingPongGuard, PingPongRecursionError


# ─── PILIER 1 : CHEMIN NOMINAL (Happy Path & Délégations Linéaires) ───

def test_linear_delegation_under_threshold():
    """Vérifie que 2 handoffs consécutifs s'exécutent sans déclencher le disjoncteur."""
    guard = PingPongGuard(max_consecutive_handoffs=3)

    # 1er handoff : Orchestrator -> Plan
    c1 = guard.record_handoff("orchestrator", "plan")
    assert c1 == 1
    assert guard.consecutive_sterile_handoffs == 1

    # 2e handoff : Plan -> Worker
    c2 = guard.record_handoff("plan", "worker")
    assert c2 == 2
    assert guard.consecutive_sterile_handoffs == 2
    assert not guard.get_status()["is_tripped"]


def test_handoff_with_produced_artifact_resets_immediately():
    """Vérifie qu'un handoff avec produced_artifact=True remet le compteur à 0."""
    guard = PingPongGuard(max_consecutive_handoffs=3)
    guard.record_handoff("orchestrator", "plan")
    assert guard.consecutive_sterile_handoffs == 1

    c2 = guard.record_handoff("plan", "worker", produced_artifact=True)
    assert c2 == 0
    assert guard.consecutive_sterile_handoffs == 0


# ─── PILIER 2 : EXCEPTIONS & REJETS MÉTIER (Détection de Cycle Stérile) ───

def test_alternating_ping_pong_cycle_trips_and_raises():
    """Vérifie qu'une boucle alternée Worker <-> Sentinel disjoncte au 3e transfert sans artefact."""
    guard = PingPongGuard(max_consecutive_handoffs=3)
    state = LoopState(project_name="test_proj")

    # 1. Worker -> Sentinel
    guard.record_handoff("worker", "sentinel", state=state)
    # 2. Sentinel -> Worker
    guard.record_handoff("sentinel", "worker", state=state)

    # 3. Worker -> Sentinel (3e handoff consécutif stérile -> Disjonction)
    with pytest.raises(PingPongRecursionError) as exc_info:
        guard.record_handoff("worker", "sentinel", state=state)

    err = exc_info.value
    assert err.cycle_depth == 3
    assert "Ping-Pong Guard activé" in str(err)
    assert "[HITL REQUIRED]" in str(err)
    assert guard.get_status()["is_tripped"] is True


def test_invalid_agent_roles_rejected():
    """Vérifie le rejet strict des rôles hors topologie et des chaînes vides."""
    guard = PingPongGuard(max_consecutive_handoffs=3)

    with pytest.raises(ValueError, match="inconnu dans la topologie"):
        guard.record_handoff("unknown_hacker", "worker")

    with pytest.raises(ValueError, match="inconnu dans la topologie"):
        guard.record_handoff("worker", "ghost_agent")

    with pytest.raises(ValueError, match="invalide ou vide"):
        guard.record_handoff("", "worker")

    with pytest.raises(ValueError, match="invalide ou vide"):
        guard.record_handoff("worker", "   ")


# ─── PILIER 3 : RÉSILIENCE TECHNIQUE (Réinitialisation & Armement HITL) ───

def test_artifact_production_explicit_reset():
    """Vérifie que la persistance physique d'un livrable déverrouille le disjoncteur."""
    guard = PingPongGuard(max_consecutive_handoffs=3)
    guard.record_handoff("orchestrator", "plan")
    guard.record_handoff("plan", "worker")
    assert guard.consecutive_sterile_handoffs == 2

    # L'agent produit un fichier concret sur disque
    guard.record_artifact_production("src/engine/feature.py")
    assert guard.consecutive_sterile_handoffs == 0

    # De nouveaux handoffs sont autorisés sans disjonction immédiate
    c = guard.record_handoff("worker", "sentinel")
    assert c == 1
    assert not guard.get_status()["is_tripped"]


def test_loop_state_hitl_flag_and_journal_mutation():
    """Vérifie que le déclenchement du disjoncteur mute LoopState.hitl_required et le journal."""
    guard = PingPongGuard(max_consecutive_handoffs=3)
    state = LoopState(project_name="mLoop")
    assert state.hitl_required is False

    guard.record_handoff("orchestrator", "plan", state=state)
    guard.record_handoff("plan", "sentinel", state=state)

    with pytest.raises(PingPongRecursionError):
        guard.record_handoff("sentinel", "worker", state=state)

    # Invariants d'état vérifiés
    assert state.hitl_required is True
    journal_events = [j.event for j in state.journal]
    assert "circuit_breaker:ping_pong_detected" in journal_events


# ─── PILIER 4 : UX & OBSERVABILITÉ (Télémétrie Cockpit & Runway) ───

def test_runway_telemetry_payload_conformance():
    """Vérifie que get_status() fournit la structure attendue par l'onglet Swarm."""
    guard = PingPongGuard(max_consecutive_handoffs=3)
    guard.record_handoff("orchestrator", "plan")
    guard.record_handoff("plan", "worker")

    status = guard.get_status()
    assert isinstance(status, dict)
    assert status["consecutive_sterile_handoffs"] == 2
    assert status["max_consecutive_handoffs"] == 3
    assert status["is_tripped"] is False
    assert status["total_handoffs"] == 2
    assert len(status["recent_history"]) == 2
    assert status["recent_history"][0]["from"] == "orchestrator"
    assert status["recent_history"][0]["to"] == "plan"
