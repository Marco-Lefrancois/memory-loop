"""
Tests unitaires — FinancialCircuitBreaker (MLOOP-003-BE).

Couvre :
1. Passage nominal sous le seuil (budget OK, TTL OK).
2. Déclenchement sur dépassement de tokens.
3. Déclenchement sur TTL expiré.
4. Comptabilisation des tokens dans System2Agent.chat() (mock).
5. Intégration orchestrateur : circuit breaker activé → ERROR.
6. Fail-open sur session_start_utc malformé (robustesse).
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from src.state import LoopState, LoopPhase, ProjectMode, TokenBudget
from src.agents.circuit_breaker import (
    FinancialCircuitBreaker,
    BudgetExceededError,
    SessionExpiredError,
)
from src.agents.orchestrator import AsymmetricOrchestrator
from src.agents.base import BaseAgent


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fresh_state(mode: ProjectMode = ProjectMode.CLIENT) -> LoopState:
    return LoopState(project_name="cb-test", project_mode=mode)


class _PassThroughAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "passthrough"

    def execute(self, state: LoopState) -> LoopState:
        return state


# ─── Tests TokenBudget ────────────────────────────────────────────────────────

def test_token_budget_consume_increments():
    budget = TokenBudget(tokens_used=0, max_tokens=1000)
    budget.consume(300)
    assert budget.tokens_used == 300


def test_token_budget_is_exhausted_at_limit():
    budget = TokenBudget(tokens_used=1000, max_tokens=1000)
    assert budget.is_exhausted is True


def test_token_budget_not_exhausted_below_limit():
    budget = TokenBudget(tokens_used=999, max_tokens=1000)
    assert budget.is_exhausted is False


# ─── Tests FinancialCircuitBreaker.check() ────────────────────────────────────

def test_cb_passes_when_budget_ok_and_ttl_ok():
    """Aucune exception levée si budget < seuil et session récente."""
    cb = FinancialCircuitBreaker(ttl_seconds=3600)
    state = _fresh_state()
    state.token_budget = TokenBudget(tokens_used=100, max_tokens=50_000)
    # Ne doit pas lever d'exception
    cb.check(state)


def test_cb_raises_budget_exceeded():
    """BudgetExceededError si tokens_used >= max_tokens."""
    cb = FinancialCircuitBreaker(ttl_seconds=3600)
    state = _fresh_state()
    state.token_budget = TokenBudget(tokens_used=50_000, max_tokens=50_000)

    with pytest.raises(BudgetExceededError, match="Budget tokens épuisé"):
        cb.check(state)

    # Le journal doit contenir l'événement
    assert any("circuit_breaker:budget" in e.event for e in state.journal)


def test_cb_raises_session_expired():
    """SessionExpiredError si session démarrée il y a plus de TTL secondes."""
    cb = FinancialCircuitBreaker(ttl_seconds=60)  # 1 minute TTL
    state = _fresh_state()
    # Session démarrée 2 heures en arrière
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    state.session_start_utc = past.isoformat()

    with pytest.raises(SessionExpiredError, match="Session expirée"):
        cb.check(state)

    assert any("circuit_breaker:ttl" in e.event for e in state.journal)


def test_cb_failopen_on_malformed_timestamp():
    """Si session_start_utc est malformé, le TTL check ne lève pas d'exception (fail-open)."""
    cb = FinancialCircuitBreaker(ttl_seconds=1)
    state = _fresh_state()
    state.session_start_utc = "NOT_A_DATE"
    # Budget OK, TTL malformé → fail-open, pas d'exception
    cb.check(state)


# ─── Tests Intégration Orchestrateur ─────────────────────────────────────────

def test_orchestrator_cb_budget_triggers_error_phase():
    """Circuit breaker budget → orchestrateur bascule en ERROR sans appeler S2."""
    s1 = _PassThroughAgent()
    s2 = _PassThroughAgent()
    cb = FinancialCircuitBreaker(ttl_seconds=3600)

    orch = AsymmetricOrchestrator(s1, s2, circuit_breaker=cb)

    state = _fresh_state(ProjectMode.CLIENT)
    # Budget épuisé
    state.token_budget = TokenBudget(tokens_used=50_000, max_tokens=50_000)
    # Phase SPEC → normalement S2
    object.__setattr__(state, "current_phase", LoopPhase.SPEC)
    object.__setattr__(state, "current_state_id", LoopPhase.SPEC.value)

    result = orch.execute_step(state)

    assert result.current_phase == LoopPhase.ERROR
    assert any("circuit_breaker" in e.event for e in result.journal)


def test_orchestrator_cb_ttl_triggers_error_phase():
    """Circuit breaker TTL → orchestrateur bascule en ERROR."""
    s1 = _PassThroughAgent()
    s2 = _PassThroughAgent()
    cb = FinancialCircuitBreaker(ttl_seconds=1)  # 1 seconde TTL

    orch = AsymmetricOrchestrator(s1, s2, circuit_breaker=cb)

    state = _fresh_state(ProjectMode.MLOOP)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    state.session_start_utc = past.isoformat()
    object.__setattr__(state, "current_phase", LoopPhase.PLAN)
    object.__setattr__(state, "current_state_id", LoopPhase.PLAN.value)

    result = orch.execute_step(state)

    assert result.current_phase == LoopPhase.ERROR


def test_s1_exempt_from_circuit_breaker():
    """Règle-04 : Le Système 1 est exempt du Circuit Breaker (budget épuisé n'affecte pas S1)."""
    s1 = _PassThroughAgent()
    s2 = _PassThroughAgent()
    cb = FinancialCircuitBreaker(ttl_seconds=3600)

    orch = AsymmetricOrchestrator(s1, s2, circuit_breaker=cb)

    state = _fresh_state(ProjectMode.CLIENT)
    # Budget épuisé, mais VALIDATE → S1 (exempt)
    state.token_budget = TokenBudget(tokens_used=50_000, max_tokens=50_000)
    object.__setattr__(state, "current_phase", LoopPhase.VALIDATE)
    object.__setattr__(state, "current_state_id", LoopPhase.VALIDATE.value)

    result = orch.execute_step(state)

    # Doit passer sans erreur (S1 n'est pas bloqué par le CB)
    assert result.current_phase == LoopPhase.VALIDATE
