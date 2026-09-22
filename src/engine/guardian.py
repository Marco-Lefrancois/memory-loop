"""
mLoop Guardian Auto-Reviewer.
Inspiré du Guardian et de l'Auto-Review d'OpenAI Codex.

Évalue les requêtes de dépassement de bac à sable (accès hors-workspace, commandes sensibles, réseau)
sans bloquer l'humain sur des micro-actions triviales, tout en appliquant un Circuit Breaker strict
pour interrompre immédiatement les agents en boucle.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
from src.utils.logger import get_logger

logger = get_logger("engine.guardian")


@dataclass
class ReviewDecision:
    allowed: bool
    rationale: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    requires_human_gate: bool = False


@dataclass
class GuardianCircuitBreaker:
    max_consecutive_denials: int = 3
    max_rolling_denials: int = 10
    rolling_window_size: int = 50
    consecutive_denials: int = 0
    denials_history: List[bool] = field(default_factory=list)

    def record_decision(self, allowed: bool) -> bool:
        """
        Enregistre la décision et retourne True si le disjoncteur saute (Trip).
        """
        self.denials_history.append(not allowed)
        if len(self.denials_history) > self.rolling_window_size:
            self.denials_history.pop(0)

        if not allowed:
            self.consecutive_denials += 1
        else:
            self.consecutive_denials = 0

        # Vérification des seuils
        if self.consecutive_denials >= self.max_consecutive_denials:
            return True  # Circuit Breaker tripped
        
        rolling_denials_count = sum(1 for d in self.denials_history if d)
        if rolling_denials_count >= self.max_rolling_denials:
            return True  # Circuit Breaker tripped

        return False

    def reset(self):
        self.consecutive_denials = 0
        self.denials_history.clear()


class GuardianAutoReviewer:
    """
    Agent Reviewer d'approbations d'actions sous bac à sable.
    """

    def __init__(self):
        self.circuit_breaker = GuardianCircuitBreaker()
        self.audit_log: List[Dict[str, Any]] = []

    def evaluate_action(
        self,
        action_type: str,
        target: str,
        context: Dict[str, Any]
    ) -> ReviewDecision:
        """
        Évalue une action et décide si elle est autorisée, refusée ou nécessite une porte humaine.
        """
        decision = self._apply_policy(action_type, target, context)
        
        # Mise à jour du disjoncteur
        tripped = self.circuit_breaker.record_decision(decision.allowed)
        
        log_entry = {
            "timestamp": time.time(),
            "action_type": action_type,
            "target": target,
            "allowed": decision.allowed,
            "risk_level": decision.risk_level,
            "rationale": decision.rationale,
            "tripped": tripped
        }
        self.audit_log.append(log_entry)

        if tripped:
            decision.allowed = False
            decision.requires_human_gate = True
            decision.rationale = (
                f"🛑 [CIRCUIT BREAKER ACTIVÉ] Trop de refus consécutifs ou cumulés "
                f"({self.circuit_breaker.consecutive_denials} refus consécutifs). "
                f"L'agent est suspendu pour éviter une boucle infinie. Approbation humaine requise."
            )

        return decision

    def _apply_policy(self, action_type: str, target: str, context: Dict[str, Any]) -> ReviewDecision:
        target_lower = target.lower()

        # Règle 1 : Fuite de secrets / tokens / .env
        if any(secret in target_lower for secret in [".env", "id_rsa", "credentials", "secrets", ".git/config"]):
            if action_type in ["read_external", "network_send", "file_export"]:
                return ReviewDecision(
                    allowed=False,
                    rationale="Tentative d'accès ou d'exfiltration de fichiers sensibles/secrets.",
                    risk_level="CRITICAL",
                    requires_human_gate=True
                )

        # Règle 2 : Commandes destructrices
        if action_type == "shell_exec":
            from src.core.hooks import DANGEROUS_PATTERNS
            import re
            for pattern, reason in DANGEROUS_PATTERNS:
                if re.search(pattern, target, re.IGNORECASE):
                    return ReviewDecision(
                        allowed=False,
                        rationale=f"Commande destructrice interdite : {reason}",
                        risk_level="CRITICAL",
                        requires_human_gate=True
                    )

        # Règle 3 : Accès fichiers hors workspace
        if action_type == "fs_write":
            allowed_roots = context.get("writable_roots", [])
            from pathlib import Path
            target_path = Path(target).resolve()
            is_inside = False
            for r in allowed_roots:
                try:
                    target_path.relative_to(Path(r).resolve())
                    is_inside = True
                    break
                except ValueError as e:
                    logger.debug(
                        "Chemin hors racines autorisées, racine suivante testée",
                        exc_info=True,
                        extra={
                            "component": "engine.guardian",
                            "operation": "is_path_allowed",
                            "error": str(e),
                        },
                    )
            
            if not is_inside:
                return ReviewDecision(
                    allowed=False,
                    rationale=f"Tentative d'écriture en dehors du workspace autorisé : {target}",
                    risk_level="HIGH",
                    requires_human_gate=True
                )

        # Règle 4 : Lecture de documentation autorisée
        if action_type in ["fs_read", "search", "fact_search"]:
            return ReviewDecision(
                allowed=True,
                rationale="Opération de lecture / exploration documentaire non mutante autorisée.",
                risk_level="LOW"
            )

        # Par défaut pour les actions ordinaires en workspace
        return ReviewDecision(
            allowed=True,
            rationale="Action conforme aux politiques standards du bac à sable.",
            risk_level="LOW"
        )
