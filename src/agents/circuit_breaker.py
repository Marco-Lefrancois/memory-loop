"""
Circuit Breaker Financier et Temporel (MLOOP-003-BE).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Set
from src.state import LoopState, LoopStateError

logger = logging.getLogger(__name__)


class BudgetExceededError(LoopStateError):
    """Exception levée lorsque le quota de tokens LLM est dépassé."""
    pass


class SessionExpiredError(LoopStateError):
    """Exception levée lorsque la durée de session dépasse le TTL alloué."""
    pass


class PingPongRecursionError(LoopStateError):
    """
    Exception levée lorsque la récursion de délégations entre agents atteint le seuil maximal (ADR-0380 / MLOOP-070-BE).
    """

    def __init__(
        self,
        message: str,
        cycle_depth: int = 0,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message)
        self.cycle_depth = cycle_depth
        self.history = history or []


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
            except (ValueError, TypeError) as e:
                # Règle MLOOP-003-BE : Fail-open sur timestamp malformé
                logger.debug("Timestamp de session malformé (fail-open) : %s", e, exc_info=True)


class PingPongGuard:
    """
    Disjoncteur déterministe anti-boucle (ADR-0380 / MLOOP-070-BE).
    Interrompt toute chaîne de handoffs atteignant 3 transferts consécutifs sans livrable sur disque.
    """

    DEFAULT_ALLOWED_ROLES = [
        "orchestrator",
        "plan",
        "worker",
        "sentinel",
        "research",
        "explorer",
    ]

    def __init__(
        self,
        max_consecutive_handoffs: int = 3,
        allowed_roles: Optional[List[str]] = None,
    ) -> None:
        self.max_consecutive_handoffs = max_consecutive_handoffs
        self.allowed_roles: Set[str] = set(
            [r.lower() for r in (allowed_roles or self.DEFAULT_ALLOWED_ROLES)]
        )
        self.handoff_history: List[Dict[str, Any]] = []
        self.consecutive_sterile_handoffs: int = 0

    def record_handoff(
        self,
        from_agent: str,
        to_agent: str,
        produced_artifact: bool = False,
        state: Optional[LoopState] = None,
    ) -> int:
        """
        Enregistre un transfert de contrôle (handoff) entre deux agents.
        Valide les rôles et vérifie immédiatement la récursion stérile.
        """
        if not from_agent or not isinstance(from_agent, str) or not from_agent.strip():
            raise ValueError(f"Rôle d'agent source invalide ou vide : '{from_agent}'")
        if not to_agent or not isinstance(to_agent, str) or not to_agent.strip():
            raise ValueError(f"Rôle d'agent cible invalide ou vide : '{to_agent}'")

        from_clean = from_agent.strip().lower()
        to_clean = to_agent.strip().lower()

        if from_clean not in self.allowed_roles:
            raise ValueError(
                f"Rôle agent source '{from_agent}' inconnu dans la topologie autorisée : {sorted(list(self.allowed_roles))}"
            )
        if to_clean not in self.allowed_roles:
            raise ValueError(
                f"Rôle agent cible '{to_agent}' inconnu dans la topologie autorisée : {sorted(list(self.allowed_roles))}"
            )

        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "from": from_clean,
            "to": to_clean,
            "timestamp": timestamp,
            "produced_artifact": produced_artifact,
        }
        self.handoff_history.append(entry)

        if produced_artifact:
            self.consecutive_sterile_handoffs = 0
            return self.consecutive_sterile_handoffs

        self.consecutive_sterile_handoffs += 1
        self.check_recursion(state=state)
        return self.consecutive_sterile_handoffs

    def check_recursion(self, state: Optional[LoopState] = None) -> None:
        """
        Vérifie la profondeur de récursion et déclenche la disjonction si le seuil est atteint.
        """
        if self.consecutive_sterile_handoffs >= self.max_consecutive_handoffs:
            msg = (
                f"Ping-Pong Guard activé : {self.consecutive_sterile_handoffs} handoffs "
                f"consécutifs sans production de livrable (seuil max : {self.max_consecutive_handoffs}). "
                f"Arrêt d'urgence et intervention humaine requise [HITL REQUIRED]."
            )
            if state is not None:
                state.add_to_journal("circuit_breaker:ping_pong_detected", msg)
                setattr(state, "hitl_required", True)

            # Émission télémétrique d'observabilité
            try:
                from src.utils.event_logger import EventLogger
                EventLogger.log_event(
                    "circuit_breaker_tripped",
                    {
                        "breaker": "PingPongGuard",
                        "consecutive_handoffs": self.consecutive_sterile_handoffs,
                        "history": self.handoff_history[-self.max_consecutive_handoffs :],
                        "hitl_required": True,
                    },
                )
            except Exception as e:
                logger.debug("Échec non-bloquant d'émission d'événement PingPongGuard : %s", e, exc_info=True)

            raise PingPongRecursionError(
                message=msg,
                cycle_depth=self.consecutive_sterile_handoffs,
                history=self.handoff_history.copy(),
            )

    def record_artifact_production(self, file_path: Optional[str] = None) -> None:
        """
        Réinitialise le compteur lors de l'écriture effective d'un artefact sur disque (ADR-0380).
        """
        self.consecutive_sterile_handoffs = 0
        self.handoff_history.append(
            {
                "action": "artifact_produced",
                "file": str(file_path) if file_path else "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_status(self) -> Dict[str, Any]:
        """
        Restitue l'état télémétrique pour le runway de handoffs et le dashboard Cockpit.
        """
        return {
            "consecutive_sterile_handoffs": self.consecutive_sterile_handoffs,
            "max_consecutive_handoffs": self.max_consecutive_handoffs,
            "is_tripped": self.consecutive_sterile_handoffs >= self.max_consecutive_handoffs,
            "recent_history": self.handoff_history[-10:],
            "total_handoffs": len(self.handoff_history),
        }

