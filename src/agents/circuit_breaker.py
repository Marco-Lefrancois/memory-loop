"""
Circuit Breaker Financier et Temporel (MLOOP-003-BE).
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from src.state import LoopState, LoopStateError


class BudgetExceededError(LoopStateError):
    """Exception levée lorsque le quota de tokens LLM est dépassé."""
    pass


class SessionExpiredError(LoopStateError):
    """Exception levée lorsque la durée de session dépasse le TTL alloué."""
    pass


class FinancialCircuitBreaker:
    """
    Garde-fou à double dimension (tokens et TTL) intercalé avant tout appel Système 2.
    """

    def __init__(self, ttl_seconds: int = 7200) -> None:
        self.ttl_seconds = ttl_seconds

    def check(self, state: LoopState) -> None:
        """
        Vérifie la consommation de tokens et le TTL de session.
        Lève BudgetExceededError ou SessionExpiredError en cas de dépassement.
        Fail-open sur timestamp malformé.
        """
        # 1. Vérification du budget de tokens
        if hasattr(state, "token_budget") and state.token_budget:
            if state.token_budget.is_exhausted or state.token_budget.tokens_used >= state.token_budget.max_tokens:
                msg = f"Budget tokens épuisé ({state.token_budget.tokens_used}/{state.token_budget.max_tokens})."
                state.add_to_journal("circuit_breaker:budget_exceeded", msg)
                raise BudgetExceededError(msg)

        # 2. Vérification du TTL de session
        session_start_raw = getattr(state, "session_start_utc", None)
        if session_start_raw:
            try:
                # Support formats ISO avec ou sans timezone
                if session_start_raw.endswith("Z"):
                    session_start_raw = session_start_raw[:-1] + "+00:00"
                start_dt = datetime.fromisoformat(session_start_raw)
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)

                now_utc = datetime.now(timezone.utc)
                if (now_utc - start_dt) > timedelta(seconds=self.ttl_seconds):
                    msg = f"Session expirée (durée > {self.ttl_seconds}s)."
                    state.add_to_journal("circuit_breaker:ttl_expired", msg)
                    raise SessionExpiredError(msg)
            except (ValueError, TypeError):
                # Règle MLOOP-003-BE : Fail-open sur timestamp malformé
                pass
