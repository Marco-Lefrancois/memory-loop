"""
_mcp_protocol_fallback.py — Politique de repli unifiée + observabilité (MLOOP-210-BE).

Politique macro ADR-004 Q1 : **une seule application par requête**, effectuée par
la couche transport (HTTP/SSE : endpoint `/messages` ; stdio : processeur de
messages). Le repli n'a jamais le droit de rejeter — seul le registre de
versions tranche le refus dur -32600.

Journaux structurés destinés au monitoring et aux harnais de certification :
- `protocol_version_obsolete` : révision connue mais non cible déclarée ;
- `protocol_fallback_decision` : mode armé + non-conformités d'en-tête ;
- adoption `modern`/`legacy` : basée sur la présence de l'en-tête de version.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any, Sequence

from src.bridges._mcp_protocol_core import (
    FALLBACK_POLICY,
    HEADER_PROTOCOL_VERSION,
    PROTOCOL_VERSION_TARGET,
    SUPPORTED_PROTOCOL_VERSIONS,
    VersionDecision,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FallbackOutcome:
    """Décision de repli appliquée à une requête (jamais un rejet)."""

    armed: bool
    mode: str
    reasons: tuple[str, ...]
    policy_id: str


_OBSERVABILITY_LOCK = threading.Lock()
_OBSOLETE_ALERTS: deque[dict[str, Any]] = deque(maxlen=200)
_FALLBACK_JOURNAL: deque[dict[str, Any]] = deque(maxlen=200)
_ADOPTION: dict[str, int] = {"modern": 0, "legacy": 0}


def apply_fallback_policy(
    decision: VersionDecision,
    *,
    transport: str,
    method: str | None = None,
    tool_name: str | None = None,
    header_present: bool | None = None,
    declared_in_message: bool = False,
    nonconformities: Sequence[str] = (),
) -> FallbackOutcome:
    """
    Applique la politique de repli par requête, dans le même traitement.

    - version connue ≠ cible  → alerte structurée `protocol_version_obsolete`
      (uniquement lorsqu'elle est déclarée dans le message) + repli armé ;
    - version non déclarée     → client hérité + repli armé (mode standard) ;
    - version inconnue         → jamais de repli (le refus -32600 prime) ;
    - en-tête absent (HTTP)    → compté comme client hérité, jamais rejeté.
    """
    reasons: list[str] = []
    if decision.status == "unknown":
        # Rejeter par politique de repli est interdit : le registre tranche.
        logger.error(
            "fallback_policy_skipped_unknown_version",
            extra={
                "event": "fallback_policy_skipped_unknown_version",
                "transport": transport,
                "declared_version": decision.requested,
                "supported": list(SUPPORTED_PROTOCOL_VERSIONS),
            },
        )
        return FallbackOutcome(
            False, FALLBACK_POLICY["mode_when_degraded"], (), FALLBACK_POLICY["policy_id"]
        )

    if decision.status == "absent":
        reasons.append("legacy_client")
    elif decision.status == "obsolete":
        reasons.append("obsolete_version")

    armed = bool(reasons)
    outcome = FallbackOutcome(
        armed=armed,
        mode=FALLBACK_POLICY["mode_when_degraded"] if armed else "modern",
        reasons=tuple(reasons),
        policy_id=FALLBACK_POLICY["policy_id"],
    )

    if decision.status == "obsolete" and declared_in_message:
        _record_obsolete_alert(decision, transport=transport, method=method, tool_name=tool_name)

    if header_present is not None:
        with _OBSERVABILITY_LOCK:
            _ADOPTION["modern" if header_present else "legacy"] += 1

    if armed or nonconformities:
        entry = {
            "event": "protocol_fallback_decision",
            "transport": transport,
            "method": method,
            "toolName": tool_name,
            "declaredVersion": decision.requested,
            "negotiatedVersion": decision.negotiated,
            "mode": outcome.mode,
            "reasons": list(outcome.reasons),
            "nonconformities": list(nonconformities),
            "policy_id": outcome.policy_id,
        }
        with _OBSERVABILITY_LOCK:
            _FALLBACK_JOURNAL.append(entry)
        logger.info("protocol_fallback_decision", extra=entry)
        if nonconformities:
            logger.warning(
                "header_routing_nonconformant",
                extra={
                    "event": "header_routing_nonconformant",
                    "transport": transport,
                    "method": method,
                    "toolName": tool_name,
                    "nonconformities": list(nonconformities),
                },
            )
    return outcome


def _record_obsolete_alert(
    decision: VersionDecision,
    *,
    transport: str,
    method: str | None,
    tool_name: str | None,
) -> None:
    entry = {
        "event": "protocol_version_obsolete",
        "transport": transport,
        "method": method,
        "toolName": tool_name,
        "declaredVersion": decision.requested,
        "targetVersion": PROTOCOL_VERSION_TARGET,
        "negotiatedVersion": decision.negotiated,
    }
    with _OBSERVABILITY_LOCK:
        _OBSOLETE_ALERTS.append(entry)
    logger.warning("protocol_version_obsolete", extra=entry)


def get_obsolete_alerts() -> list[dict[str, Any]]:
    """Journal des alertes d'obsolescence structurées."""
    with _OBSERVABILITY_LOCK:
        return list(_OBSOLETE_ALERTS)


def get_fallback_journal() -> list[dict[str, Any]]:
    """Journal des décisions de repli protocolaire."""
    with _OBSERVABILITY_LOCK:
        return list(_FALLBACK_JOURNAL)


def get_adoption_metrics() -> dict[str, Any]:
    """Métrique d'adoption de l'en-tête de version (modernes vs hérités)."""
    with _OBSERVABILITY_LOCK:
        modern, legacy = _ADOPTION["modern"], _ADOPTION["legacy"]
    total = modern + legacy
    return {
        "modern": modern,
        "legacy": legacy,
        "total": total,
        "adoption_ratio": round(modern / total, 4) if total else 0.0,
        "header": HEADER_PROTOCOL_VERSION,
        "target_version": PROTOCOL_VERSION_TARGET,
    }


def reset_protocol_observability() -> None:
    """Remise à zéro des compteurs (tests & harnais de certification)."""
    with _OBSERVABILITY_LOCK:
        _OBSOLETE_ALERTS.clear()
        _FALLBACK_JOURNAL.clear()
        _ADOPTION["modern"] = 0
        _ADOPTION["legacy"] = 0
