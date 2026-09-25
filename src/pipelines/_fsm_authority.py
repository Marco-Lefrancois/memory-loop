"""
FSM Authority Guard — mLoop (ADR-0393 / MLOOP-322-BE).

Verrou d'autorité nominative humaine exclusive pour la Gate 2 (READY_FOR_DEV).

Ce module isole l'exception dédiée `LifecycleAuthorityError` et la validation
stricte des métadonnées d'autorité, afin de respecter le plafond de 300 lignes
par fichier (ADR-0202) sur `state_machine.py` et `grill/_engine.py`.

Principe Fail-Closed strict : toute tentative de promotion vers `READY_FOR_DEV`
sans signature humaine nominative valide (`validated_by`) et horodatage ISO-8601
(`validated_at`) est rejetée par une exception bloquante.
"""

from __future__ import annotations

from datetime import datetime

from src.pipelines.state_machine import StateTransitionError
from src.utils.logger import get_logger

logger = get_logger("pipelines.fsm_authority")


class LifecycleAuthorityError(StateTransitionError):
    """
    Exception levée lorsqu'une machine (agent conversationnel ou script autonome)
    tente de contourner l'autorité humaine exclusive requise pour la Gate 2
    (promotion vers `READY_FOR_DEV`) ou de muter des récits en scope transverse.

    Sous-type de `StateTransitionError` pour rétrocompatibilité des gestionnaires
    d'erreurs existants du pipeline FSM.
    """

    pass


# ─── Constantes de gouvernance ─────────────────────────────────────────────────
# Statuts dont la promotion est INTERDITE à toute machine (agent/script autonome).
# Seule l'autorité humaine nominative (Gate 2) peut y faire transiter un récit.
MACHINE_BLOCKED_STATUSES = frozenset({"READY_FOR_DEV"})

# Signatures interdites dans `validated_by` : identifient un processus non-humain.
_BOT_SIGNATURE_PATTERNS = (
    "bot",
    "agent",
    "system",
    "auto",
    "pipeline",
)


def _is_bot_signature(validated_by: str) -> bool:
    """Retourne True si la signature ressemble à un processus non-humain."""
    lowered = validated_by.strip().lower()
    return any(pattern in lowered for pattern in _BOT_SIGNATURE_PATTERNS)


def _is_valid_iso8601(value: str) -> bool:
    """Vérifie qu'une chaîne est un horodatage ISO-8601 parsable."""
    candidate = value.strip()
    if not candidate:
        return False
    # `datetime.fromisoformat` accepte le suffixe 'Z' depuis Python 3.11 ;
    # normalisation défensive pour les runtimes antérieurs.
    normalized = candidate.replace("Z", "+00:00") if candidate.endswith("Z") else candidate
    try:
        datetime.fromisoformat(normalized)
        return True
    except ValueError:
        logger.debug(
            "Horodatage validated_at non conforme ISO-8601",
            extra={
                "component": "pipelines.fsm_authority",
                "operation": "is_valid_iso8601",
                "value": candidate,
            },
        )
        return False


def validate_gate2_authority(frontmatter: dict, story_id: str) -> None:
    """
    Valide l'autorité nominative humaine requise pour la transition vers
    `READY_FOR_DEV` (Gate 2).

    Règles (Fail-Closed strict) :
      - `validated_by` : présent, non vide, et sans signature de bot/agent/script.
      - `validated_at` : présent et au format ISO-8601 valide.

    Lève `LifecycleAuthorityError` (sous-type de `StateTransitionError`) si l'une
    des conditions n'est pas satisfaite, en détaillant les champs manquants.
    """
    missing: list[str] = []

    validated_by = str(frontmatter.get("validated_by", "") or "").strip()
    validated_at = str(frontmatter.get("validated_at", "") or "").strip()

    if not validated_by:
        missing.append("validated_by (signature humaine nominative absente)")
    elif _is_bot_signature(validated_by):
        missing.append(f"validated_by (signature non-humaine détectée : « {validated_by} »)")

    if not validated_at:
        missing.append("validated_at (horodatage ISO-8601 absent)")
    elif not _is_valid_iso8601(validated_at):
        missing.append(f"validated_at (format ISO-8601 invalide : « {validated_at} »)")

    if missing:
        details = "\n  - ".join(missing)
        raise LifecycleAuthorityError(
            f"[GATE 2 — AUTORITÉ NOMINATIVE BLOQUANTE] Promotion du récit "
            f"'{story_id}' vers READY_FOR_DEV refusée : autorité humaine "
            f"exclusive non prouvée.\n"
            f"Champs non conformes :\n  - {details}\n"
            f"➡ L'état READY_FOR_DEV exige une signature humaine nominative "
            f"(validated_by) et un horodatage ISO-8601 (validated_at). "
            f"Aucun agent conversationnel ou script autonome ne peut la fournir."
        )
