"""
src/pipelines/grill/_elicitation_flow.py — Orchestration métier de l'élicitation
Form Mode (MLOOP-213-BE).

Filet d'enchaînement entre le registre de décisions, l'état d'attente et le
cycle de vie de la tâche : publier une question, lever l'attente, écrire la
décision. Aucun souci protocolaire ici — l'enveloppe JSON-RPC et la négociation
de capacité vivent dans ``src/bridges/_mcp_elicitation.py``.

Règles servies (récit § Critères d'acceptation) :
- **AC1** : sans capacité d'élicitation la question part en repli textuel, sans
  le moindre refus ; une question sans schéma complet ni options fermées n'est
  pas émise ; une question déjà tranchée au registre n'est jamais reposée ;
- **AC2** : toute activité fait expirer les attentes dépassées ;
- **AC3** : contrôle → écriture synchrone → levée de l'attente → reprise de la
  tâche, séquence tout-ou-rien dont tout refus survient avant écriture ;
- **AC4/AC5** : un seul chemin d'écriture pour les deux provenances.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.pipelines.grill._elicitation import (
    ELICITATION_TIMEOUT_SECONDS,
    ElicitationError,
    STATUS_WAITING,
    render_fallback_markdown,
    resolve_project_dir,
    stable_elicitation_id,
    validate_content,
    validate_requested_schema,
)
from src.pipelines.grill._elicitation_registry import find_decision, record_decision
from src.pipelines.grill._elicitation_state import (
    clear_pending,
    expire_due,
    get_pending,
    resume_task,
    save_pending,
)

logger = logging.getLogger(__name__)


def create_elicitation(
    params: Any,
    *,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
    form_mode: bool = False,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Publie une question d'arbitrage en mode formulaire si l'environnement
    l'offre, en repli textuel sinon — l'absence de capacité n'est jamais un
    refus (AC5)."""
    payload_in = params if isinstance(params, Mapping) else {}
    resolved = resolve_project_dir(project_path, project)
    moment = now or datetime.now(timezone.utc)
    # Balayage systématique : toute activité fait expirer les attentes dépassées.
    expire_due(resolved, now=moment)

    message = str(payload_in.get("message") or "").strip()
    schema = payload_in.get("requestedSchema")
    reasons = ([] if message else ["message_absent"]) + validate_requested_schema(schema)
    if reasons:
        raise ElicitationError(reasons)

    story_id = str(payload_in.get("storyId") or "").strip()
    elicitation_id = str(payload_in.get("elicitationId") or "").strip() or stable_elicitation_id(
        story_id, message
    )
    existing = find_decision(elicitation_id, resolved)
    if existing is not None:
        # Preuve de réponse unique : jamais de seconde sollicitation (AC6).
        return {
            "mode": "none",
            "elicitationId": elicitation_id,
            "storyId": story_id,
            "message": message,
            "alreadyAnswered": True,
            "decision": existing,
        }

    payload: dict[str, Any] = {
        "elicitationId": elicitation_id,
        "storyId": story_id,
        "message": message,
        "requestedSchema": schema,
        "context": dict(payload_in.get("context") or {}),
    }
    task_id = str(payload_in.get("taskId") or "").strip()
    if not form_mode:
        # Repli textuel : aucun état d'attente n'est ouvert (AC5).
        clear_pending(elicitation_id, resolved)
        return {
            "mode": "text",
            **payload,
            "fallback": True,
            "question": render_fallback_markdown(payload),
        }

    timestamp = moment.isoformat()
    previous = get_pending(elicitation_id, resolved) or {}
    save_pending(
        {
            **previous,
            **payload,
            "taskId": task_id or previous.get("taskId", ""),
            "status": STATUS_WAITING,
            "createdAt": previous.get("createdAt") or timestamp,
            "emittedAt": timestamp,
        },
        resolved,
    )
    return {
        "mode": "form",
        **payload,
        "expiresInSeconds": int(ELICITATION_TIMEOUT_SECONDS),
    }


def answer_elicitation(
    message: Mapping[str, Any],
    *,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
    answered_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Traite le retour de l'élicitation (réponse JSON-RPC ou charge utile).

    Séquence tout-ou-rien (AC3) : contrôle contre le schéma → écriture
    synchrone → levée de l'attente → reprise de la tâche. Tout refus lève
    :class:`ElicitationError` **avant** toute écriture, l'attente demeurant en
    place. Une question déjà tranchée n'ajoute aucune ligne (AC4).
    """
    source = message.get("result")
    if not isinstance(source, Mapping):
        source = message.get("params") if isinstance(message.get("params"), Mapping) else message
    if not isinstance(source, Mapping):
        raise ElicitationError(["reponse_absente"])
    elicitation_id = str(source.get("elicitationId") or message.get("id") or "").strip()
    if not elicitation_id:
        raise ElicitationError(["identifiant_absent"])
    resolved = resolve_project_dir(project_path, project)

    existing = find_decision(elicitation_id, resolved)
    if existing is not None:
        return {
            "accepted": False,
            "recorded": False,
            "alreadyAnswered": True,
            "decision": existing,
        }
    if str(source.get("action") or "accept") != "accept":
        clear_pending(elicitation_id, resolved)
        return {"accepted": False, "recorded": False, "reason": "action_non_acceptee"}

    answered_by = str(source.get("answeredBy") or source.get("author") or "").strip()
    pending = get_pending(elicitation_id, resolved)
    if pending is not None:
        reasons = validate_content(pending.get("requestedSchema") or {}, source.get("content"))
        if not answered_by:
            reasons.insert(0, "auteur_absent")
        if reasons:
            raise ElicitationError(reasons)
        record = record_decision(
            elicitation_id=elicitation_id,
            story_id=str(pending.get("storyId") or ""),
            question=str(pending.get("message") or ""),
            answer=source.get("content"),
            answered_by=answered_by,
            fallback_used=False,
            adr_ref=source.get("adrRef"),
            answered_at=answered_at,
            project_path=resolved,
        )
        clear_pending(elicitation_id, resolved)
        resume_task(pending, resolved)
        return {"accepted": True, "recorded": True, "decision": record}

    # Repli textuel : réponse sans formulaire, donc sans attente à lever (AC5).
    story_id = str(source.get("storyId") or "").strip()
    question = str(source.get("question") or "").strip()
    if not story_id or not question:
        raise ElicitationError(["identifiant_inconnu"])
    answer = source.get("answer", source.get("content"))
    if not answered_by or answer is None or (isinstance(answer, str) and not answer.strip()):
        return {"accepted": False, "recorded": False, "reason": "reponse_incomplete"}
    record = record_decision(
        elicitation_id=elicitation_id,
        story_id=story_id,
        question=question,
        answer=answer,
        answered_by=answered_by,
        fallback_used=True,
        adr_ref=source.get("adrRef"),
        answered_at=answered_at,
        project_path=resolved,
    )
    return {"accepted": True, "recorded": True, "decision": record}
