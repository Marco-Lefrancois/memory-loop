"""
_mcp_tasks.py — Pont JSON-RPC de l'extension Tasks (MLOOP-211-BE).

Les 4 primitives `tasks/*` sont servies par le carrefour unique
`mcp_loop_mem.process_message` : l'exchange JSON-RPC local existant reste la
seule route, aucune route reseau n'est ajoutee et aucun sondage n'est installe.

Chaque changement d'etat reel pousse **une seule** notification
`notifications/tasks/updated` (evenement SSE `tasks/updated`) lorsque des
clients sont abonnes ; sinon l'etat est mis en attente et rattrape au prochain
echange porteur d'un `result`, via `_meta.routing.tasks` — rattrapage
strictement passif, consomme une seule fois.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.bridges._mcp_protocol_core import register_known_method
from src.bridges._mcp_tasks_service import TaskService
from src.bridges.mcp_event_bus import get_event_bus
from src.core import task_lifecycle as lifecycle
from src.core.task_handles import TaskError, TaskRecord, TaskStore, to_iso
from src.core.task_spawner import HerdrTaskSpawner

logger = logging.getLogger("mloop.mcp_tasks")

TASKS_METHODS: tuple[str, ...] = (
    "tasks/create",
    "tasks/status",
    "tasks/cancel",
    "tasks/result",
)
TASKS_NOTIFICATION: str = "notifications/tasks/updated"
ERROR_INVALID_PARAMS: int = -32602

# Magasins par projet : une vue de chemins, aucune ressource ouverte.
_STORES: dict[str, TaskStore] = {}
# Rattrapage : etats en attente d'un prochain echange porteur d'un `result`.
_PIGGYBACK: dict[str, dict[str, Any]] = {}


def _store_for(project: Any = None) -> TaskStore:
    name = str(project) if project else "mLoop"
    return _STORES.setdefault(name, TaskStore(name))


def get_service(project: Any = None) -> TaskService:
    """Fabrique le service des 4 primitives pour le projet de session."""
    store = _store_for(project)
    spawner = HerdrTaskSpawner(
        on_failure=lambda task_id, cause: _settle_failed(store, task_id, cause),
        on_event=lambda task_id, message: _record_output(store, task_id, message),
    )
    return TaskService(store=store, spawner=spawner)


def _record_output(store: TaskStore, task_id: str, message: str) -> None:
    """Trace d'execution portee au journal, sans transition ni notification."""
    lifecycle.record_output(store, task_id, message)


def _settle_failed(store: TaskStore, task_id: str, cause: str) -> None:
    """Le lancement a echoue : verdict `failed` rendu sans attendre quiconque."""
    try:
        lifecycle.transition_record(
            store,
            task_id,
            "failed",
            payload={"cause": cause},
            message=f"Lancement echoue : {cause}",
        )
    except TaskError as exc:
        logger.debug(
            "Verdict de lancement non applicable",
            exc_info=True,
            extra={"task_id": task_id, "code": exc.code},
        )
    finally:
        lifecycle.pop_handle(task_id)


def _emit(record: TaskRecord) -> None:
    """Notifie une transition reelle ; rattrapage passif sinon."""
    payload: dict[str, Any] = {
        "task_id": record.task_id,
        "status": record.status,
        "expires_at": to_iso(record.expires_at),
    }
    bus = get_event_bus()
    if bus.client_count > 0:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("Boucle asyncio absente : etat mis en piggyback", extra=payload)
        else:
            loop.create_task(bus.notify_task_updated(**payload, session_id=record.project))
            return
    _PIGGYBACK[record.task_id] = payload
    logger.debug("Aucun abonne SSE : etat mis en piggyback", extra=payload)


def attach_pending_task_updates(response: Any) -> Any:
    """Rattache les etats en attente au prochain echange porteur d'un `result`."""
    if not _PIGGYBACK or not isinstance(response, dict):
        return response
    result = response.get("result")
    if not isinstance(result, dict):
        return response
    meta = result.get("_meta")
    merged = dict(meta) if isinstance(meta, dict) else {}
    routing = dict(merged.get("routing") or {})
    routing["tasks"] = list(_PIGGYBACK.values())
    merged["routing"] = routing
    result["_meta"] = merged
    _PIGGYBACK.clear()
    return response


def pending_updates() -> dict[str, dict[str, Any]]:
    """Etats en attente (observabilite / tests) - lecture seule."""
    return dict(_PIGGYBACK)


def reset_state() -> None:
    """Remise a zero des etats en attente (tests / nouvelle session)."""
    _PIGGYBACK.clear()
    _STORES.clear()


def dispatch(
    method: str,
    req_id: Any,
    params: Any,
    session_project: str | None = None,
) -> dict[str, Any]:
    """Execute une primitive Tasks et la renvoie en enveloppe JSON-RPC."""
    body = params if isinstance(params, dict) else {}
    project = body.get("project") or session_project
    service = get_service(project)
    try:
        result = _invoke(service, method, body, project)
    except TaskError as exc:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": ERROR_INVALID_PARAMS,
                "message": exc.message,
                "data": {"code": exc.code},
            },
            "id": req_id,
        }
    except (TypeError, ValueError) as exc:
        logger.debug("Parametre Tasks mal forme", exc_info=True, extra={"method": method})
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": ERROR_INVALID_PARAMS,
                "message": str(exc),
                "data": {"code": "invalid_params"},
            },
            "id": req_id,
        }
    return {"jsonrpc": "2.0", "result": result, "id": req_id}


def _invoke(service: TaskService, method: str, body: dict, project: Any) -> dict[str, Any]:
    if method == "tasks/create":
        return service.create(
            story_id=body.get("story_id"),
            task_id=body.get("task_id"),
            status=body.get("status", "working"),
            command=body.get("command", "worker-spawn"),
            project=project,
            execution=body.get("execution"),
            request=body.get("request"),
        )
    if method == "tasks/status":
        return service.status_view(body.get("task_id"), body.get("since"))
    if method == "tasks/cancel":
        return service.cancel(
            body.get("task_id"),
            body.get("reason"),
            timeout_s=float(body.get("timeout_s", 10.0)),
        )
    if method == "tasks/result":
        return service.result_view(body.get("task_id"))
    raise TaskError("unsupported_command", f"Primitive Tasks inconnue: {method}")


for _method in TASKS_METHODS:  # couture avec le registre de routage (socle 210)
    register_known_method(_method)
register_known_method(TASKS_NOTIFICATION)
lifecycle.set_notifier(_emit)
