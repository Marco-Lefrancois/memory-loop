"""
task_lifecycle.py - Transitions d'etat des handles de tache (MLOOP-211-BE).

Une seule porte d'ecriture d'etat : `transition_record` ecrit l'etat et son
echeance en tout-ou-rien, pose l'entree de journal et pousse **une seule**
notification de transition. Toute transition vers un etat terminal recalcule
l'echeance a partir de l'horodatage d'ouverture (jamais de la date de la
transition) ; les etats actifs conservent une echeance nulle.

Le registre `LIVE_HANDLES` materialise le **cycle de suivi** : seul un
sous-processus qui y figure peut etre arrete, jamais un processus etranger.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Protocol

from src.core.task_handles import (
    TaskError,
    TaskRecord,
    TaskStore,
    is_terminal,
    is_valid_state,
    utc_now,
)

logger = logging.getLogger("mloop.task_lifecycle")

# Registre partage du cycle de suivi (spawner -> service -> lifecycle hooks).
LIVE_HANDLES: dict[str, "LaunchHandle"] = {}
_LIVE_LOCK = threading.Lock()
_STORE_LOCK = threading.Lock()

Notifier = Callable[[TaskRecord], None]
_NOTIFIER: Notifier | None = None


class LaunchHandle(Protocol):
    """Poignee de sous-processus rattache au cycle de suivi."""

    subprocess_id: str

    def terminate(self, timeout_s: float) -> bool:
        """Arret borne du sous-processus ; True si l'extinction est confirmee."""
        ...


def set_notifier(notifier: Notifier | None) -> None:
    """Branche la poussee de notifications (pont MCP) sur le cycle de vie."""
    global _NOTIFIER
    _NOTIFIER = notifier


def emit_notification(record: TaskRecord) -> None:
    """Une notification par transition reelle - jamais deux."""
    if _NOTIFIER is None:
        logger.debug(
            "Notification de transition non branchee",
            extra={"task_id": record.task_id, "status": record.status},
        )
        return
    try:
        _NOTIFIER(record)
    except Exception as exc:
        logger.debug(
            "Poussee de notification de tache echouee",
            exc_info=True,
            extra={"task_id": record.task_id, "error": str(exc)},
        )


def register_handle(task_id: str, handle: LaunchHandle) -> None:
    with _LIVE_LOCK:
        LIVE_HANDLES[task_id] = handle


def get_handle(task_id: str) -> LaunchHandle | None:
    with _LIVE_LOCK:
        return LIVE_HANDLES.get(task_id)


def pop_handle(task_id: str) -> LaunchHandle | None:
    with _LIVE_LOCK:
        return LIVE_HANDLES.pop(task_id, None)


def tracked_subprocess(task_id: str) -> str | None:
    handle = get_handle(task_id)
    return getattr(handle, "subprocess_id", None) if handle else None


def retention_expires_at(record: TaskRecord) -> datetime:
    """Echeance = horodatage d'ouverture + duree du registre protocolaire partage."""
    from src.bridges._mcp_protocol_core import TASK_HANDLE_TTL_DAYS  # SSOT partagee

    return record.created_at + timedelta(days=TASK_HANDLE_TTL_DAYS)


def transition_record(
    store: TaskStore,
    task_id: str,
    status: str,
    *,
    payload: dict[str, Any] | None = None,
    message: str | None = None,
    allow_terminal_to_terminal: bool = False,
    notify: bool = True,
) -> TaskRecord:
    """Applique une transition d'etat unique, atomique et notifiee une fois."""
    if not is_valid_state(status):
        raise TaskError("invalid_status", f"Etat hors du vocabulaire ferme: {status!r}")
    with _STORE_LOCK:
        record = store.load(task_id)
        if record is None:
            raise TaskError("task_not_found", f"Tache inconnue ou emportee: {task_id}")
        if record.status == status:
            # Meme etat : ni ecriture ni deuxieme notification pour la transition.
            return record
        if is_terminal(record.status) and not allow_terminal_to_terminal:
            raise TaskError(
                "task_already_terminal",
                f"Verdict deja rendu ({record.status}) : la transition est refusee.",
            )
        record.status = status
        record.updated_at = utc_now()
        # Echeance recalculee a chaque verdict, toujours depuis l'ouverture.
        if is_terminal(status):
            record.expires_at = retention_expires_at(record)
            # Le verdict remplace le payload d'execution : `tasks/result` livre
            # un verdict propre (deliverables / cause / reason), jamais la
            # question restee en suspens d'un etat actif precedent.
            record.payload = dict(payload) if payload is not None else {}
        else:
            record.expires_at = None
            if payload is not None:
                record.payload = payload
        record.append_entry("state", message or f"Transition vers {status}", status)
        store.save(record)
    if notify:
        emit_notification(record)
    return record


def record_output(store: TaskStore, task_id: str, message: str) -> bool:
    """Ajoute une trace d'execution au journal, sans transition ni notification.

    Retourne False si la tache n'existe pas encore (lancement engage avant la
    publication de l'enregistrement) : l'appelant en charge le report.
    """
    with _STORE_LOCK:
        record = store.load(task_id)
        if record is None:
            return False
        record.append_entry("output", message)
        record.updated_at = utc_now()
        store.save(record)
    return True


def settle_on_lifecycle(
    store: TaskStore,
    story_id: str,
    status: str,
    payload: dict[str, Any] | None = None,
    message: str | None = None,
) -> TaskRecord | None:
    """Raccord `worker-harvest` / `worker-close` : statue la tache du recit.

    Aucun effet (None) quand aucun handle n'est ouvert pour ce recit : le cycle
    de lancement, de collecte et de nettoyage existants ne sont pas modifies.
    """
    if not (store.base_dir / store.project / "memory" / "tasks").is_dir():
        # Registre de taches jamais cree : rien a statuer et aucun dossier cree.
        return None
    record = store.find_active_for_story(story_id)
    if record is None:
        return None
    try:
        settled = transition_record(store, record.task_id, status, payload=payload, message=message)
    except TaskError as exc:
        logger.debug(
            "Statut de tache ignore en fin de cycle",
            exc_info=True,
            extra={"story_id": story_id, "status": status, "code": exc.code},
        )
        return None
    if is_terminal(settled.status):
        pop_handle(settled.task_id)
    return settled


def locate_active_store(identifier: str, base_dir: str = "Projects") -> TaskStore | None:
    """Resout le magasin portant la tache active d'un recit ou d'un compagnon.

    Le nettoyage (`worker-close`) ne connait que l'identifiant passe au fermeur
    de volet — recit ou nom de compagnon — et n'a aucun projet en main : le
    magasin est donc resolu ici, sans route nouvelle ni creation de dossier.
    """
    try:
        tasks_dirs = sorted(Path(base_dir).glob("*/memory/tasks"))
    except OSError as exc:
        logger.debug("Index des taches inaccesible", exc_info=True, extra={"base_dir": base_dir})
        return None
    for tasks_dir in tasks_dirs:
        project = tasks_dir.parent.parent.name
        store = TaskStore(project, base_dir=base_dir)
        for path in sorted(tasks_dir.glob("*.json")):
            record = store.load(path.stem)
            if record is None or record.is_terminal:
                continue
            if identifier in (record.story_id, record.subprocess_id):
                return store
    return None


def clear_registry() -> None:
    """Remise a zero du cycle de suivi (tests / nouvelle session)."""
    with _LIVE_LOCK:
        LIVE_HANDLES.clear()
