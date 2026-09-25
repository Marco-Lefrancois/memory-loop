"""
src/pipelines/grill/_elicitation_state.py — État d'attente régénérable et
cycle de vie 5 minutes (MLOOP-213-BE).

- **Attente** (``Projects/<projet>/memory/evidence/elicitation_pending.json``) :
  identifiant, énoncé, schéma et contexte — rien d'autre. Aucun état d'interface
  n'est persistant ; l'attente est supprimée dès réception de la réponse, et un
  retour du client la régénère **à l'identique** (même identifiant, même schéma,
  même contexte).
- **Bornage à 5 minutes** (macro ADR-004 Q3) : une attente dépassée passe en
  attente de saisie (``input_required``) — jamais en échec, jamais en abandon —
  et demeure récupérable à la reconnexion.
- **Seam de cycle de vie** : le passage au repos et la reprise sont délégués,
  s'ils existent, à l'extension de tâches (récit MLOOP-211-BE, seam
  :class:`TaskLifecycle`). Tant qu'aucun pont n'est enregistré, l'état reste
  lisible dans l'attente sans qu'aucune erreur ne soit produite.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol

from src.pipelines.grill._elicitation import (
    ELICITATION_TIMEOUT_SECONDS,
    PENDING_FILE,
    STATUS_INPUT_REQUIRED,
    resolve_project_dir,
)

logger = logging.getLogger(__name__)


def pending_state_path(project_path: Optional[Path] = None, project: Optional[str] = None) -> Path:
    return resolve_project_dir(project_path, project) / "memory" / "evidence" / PENDING_FILE


def _read_pending(
    project_path: Optional[Path] = None, project: Optional[str] = None
) -> list[dict[str, Any]]:
    path = pending_state_path(project_path, project)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        logger.debug(
            "pending_elicitation_corrompu_reinitialise",
            exc_info=True,
            extra={
                "component": "pipelines.grill.elicitation.state",
                "operation": "read_pending",
                "path": str(path),
            },
        )
        return []
    return [entry for entry in data if isinstance(entry, dict)] if isinstance(data, list) else []


def _write_pending(
    entries: list[dict[str, Any]],
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> None:
    path = pending_state_path(project_path, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)


def get_pending(
    elicitation_id: str,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    for entry in _read_pending(project_path, project):
        if entry.get("elicitationId") == elicitation_id:
            return entry
    return None


def save_pending(
    entry: Mapping[str, Any],
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> dict[str, Any]:
    """Conserve l'attente d'un identifiant, à l'identique si elle existait déjà."""
    stored = dict(entry)
    entries = [
        existing
        for existing in _read_pending(project_path, project)
        if existing.get("elicitationId") != stored.get("elicitationId")
    ]
    entries.append(stored)
    _write_pending(entries, project_path, project)
    return stored


def clear_pending(
    elicitation_id: str,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> bool:
    """Supprime l'attente dès réception de la réponse (jamais avant)."""
    entries = _read_pending(project_path, project)
    kept = [entry for entry in entries if entry.get("elicitationId") != elicitation_id]
    if len(kept) == len(entries):
        return False
    _write_pending(kept, project_path, project)
    return True


# ──────────────────────────────────────────────────────────────────────────
# CYCLE DE VIE : EXPIRATION 5 MIN → ATTENTE DE SAISIE, PUIS REPRISE
# ──────────────────────────────────────────────────────────────────────────


class TaskLifecycle(Protocol):
    """Seam vers l'extension de tâches (récit MLOOP-211-BE, hors périmètre).

    Contrat attendu lorsque le pont de tâches est en service ; tant qu'aucun
    n'est enregistré, l'expiration reste lisible dans l'état d'attente sans
    qu'aucune erreur ne soit produite.
    """

    def suspend_for_input(
        self, *, task_id: str, elicitation_id: str, story_id: str, project: str
    ) -> None: ...

    def resume_from_input(
        self, *, task_id: str, elicitation_id: str, story_id: str, project: str
    ) -> None: ...


_TASK_LIFECYCLE: Optional[TaskLifecycle] = None


def set_task_lifecycle(lifecycle: Optional[TaskLifecycle]) -> None:
    """Installe (ou retire) le pont vers l'extension de tâches."""
    global _TASK_LIFECYCLE
    _TASK_LIFECYCLE = lifecycle


def _notify_lifecycle(action: str, entry: Mapping[str, Any], project: str) -> None:
    task_id = str(entry.get("taskId") or "")
    if _TASK_LIFECYCLE is None or not task_id:
        logger.debug(
            "elicitation_task_lifecycle_absent",
            extra={
                "component": "pipelines.grill.elicitation.state",
                "operation": action,
                "elicitation_id": entry.get("elicitationId"),
                "task_id": task_id,
                "project": project,
            },
        )
        return
    arguments = {
        "task_id": task_id,
        "elicitation_id": str(entry.get("elicitationId") or ""),
        "story_id": str(entry.get("storyId") or ""),
        "project": project,
    }
    try:
        getattr(_TASK_LIFECYCLE, action)(**arguments)
    except Exception:  # noqa: BLE001 — jamais de silence (ADR-0369 §4)
        logger.debug(
            "elicitation_task_lifecycle_echec",
            exc_info=True,
            extra={
                "component": "pipelines.grill.elicitation.state",
                "operation": action,
                "elicitation_id": arguments["elicitation_id"],
                "task_id": task_id,
                "project": project,
            },
        )


def resume_task(
    entry: Mapping[str, Any],
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> None:
    """Remet en route la tâche ciblée, **après** l'écriture synchrone de la
    décision et la levée de l'attente (AC3) — jamais avant."""
    resolved = resolve_project_dir(project_path, project)
    _notify_lifecycle("resume_from_input", entry, resolved.name)


def _parse_instant(raw: Any) -> Optional[datetime]:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def expire_due(
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
    now: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """Faites expirer les attentes dépassées : la tâche ciblée passe en attente
    de saisie, l'attente demeure **intacte** (ni échec ni abandon) et le
    formulaire sera régénéré à la reconnexion. Aucun rejet n'est produit."""
    resolved = resolve_project_dir(project_path, project)
    moment = now or datetime.now(timezone.utc)
    entries = _read_pending(resolved)
    expired: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("status") == STATUS_INPUT_REQUIRED:
            continue
        emitted = _parse_instant(entry.get("emittedAt") or entry.get("createdAt"))
        if emitted is None or (moment - emitted).total_seconds() < ELICITATION_TIMEOUT_SECONDS:
            continue
        entry["status"] = STATUS_INPUT_REQUIRED
        entry["suspendedAt"] = moment.isoformat()
        expired.append(entry)
    if expired:
        _write_pending(entries, resolved)
        for entry in expired:
            _notify_lifecycle("suspend_for_input", entry, resolved.name)
    return expired
