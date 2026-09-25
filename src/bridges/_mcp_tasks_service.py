"""
_mcp_tasks_service.py - Primitives `tasks/*` de l'extension Tasks (MLOOP-211-BE).

Call-Now-Fetch-Later : `create` remet un identifiant durable dans la foulée
(sous le seuil des 500 ms), `status` lit l'avancement sans bloquer, `cancel`
arrete le sous-processus du cycle de suivi, `result` livre le verdict d'une
tache eteinte tant que son echeance de retention est valide.

Aucune de ces operations n'ouvre de route reseau ni n'instaure de sondage
proactif : l'extension vit uniquement sur l'exchange JSON-RPC local et sur
le bus d'evenements en flux continu deja en service.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Mapping

from src.core.task_handles import (
    ACTIVE_STATES,
    TaskError,
    TaskRecord,
    TaskStore,
    is_terminal,
    is_valid_state,
    to_iso,
    utc_now,
    validate_task_id,
)
from src.core.task_lifecycle import (
    get_handle,
    pop_handle,
    register_handle,
    transition_record,
)
from src.core.task_spawner import TaskSpawner, worker_name_for

logger = logging.getLogger("mloop.mcp_tasks_service")

CREATE_RESPONSE_BUDGET_S: float = 0.5
SUPPORTED_COMMANDS: tuple[str, ...] = ("worker-spawn",)
VERDICT_KEYS: dict[str, str] = {
    "completed": "deliverables",
    "failed": "cause",
    "cancelled": "reason",
}


class TaskService:
    """Ensemble des 4 primitives d'echange de l'extension Tasks."""

    def __init__(
        self,
        store: TaskStore,
        spawner: TaskSpawner,
        budget_s: float = CREATE_RESPONSE_BUDGET_S,
    ) -> None:
        self.store = store
        self.spawner = spawner
        self.budget_s = budget_s

    # ── 1. Ouverture ──────────────────────────────────────────────────────
    def create(
        self,
        *,
        story_id: Any,
        task_id: Any = None,
        status: Any = "working",
        command: Any = "worker-spawn",
        project: Any = None,
        execution: Any = None,
        request: Any = None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        if not isinstance(story_id, str) or not story_id.strip():
            raise TaskError("missing_story_id", "Le rattachement au recit est obligatoire.")
        if command is not None and command not in SUPPORTED_COMMANDS:
            raise TaskError(
                "unsupported_command",
                f"Commande de lancement non supportee: {command!r} "
                f"(seules: {', '.join(SUPPORTED_COMMANDS)}).",
            )
        declared = "working" if status is None else status
        if not is_valid_state(declared):
            raise TaskError(
                "invalid_status",
                f"Etat declare hors du vocabulaire ferme des cinq etats: {declared!r}",
            )
        if is_terminal(declared):
            raise TaskError(
                "cannot_open_on_terminal_state",
                f"Une ouverture ne peut viser qu'une tache nouvelle, pas un etat terminal ({declared}).",
            )
        if declared not in ACTIVE_STATES:
            raise TaskError("invalid_status", f"Etat d'ouverture inactif: {declared!r}")
        params = dict(execution) if isinstance(execution, Mapping) else {}
        for key in ("kind", "model", "task_type"):
            if params.get(key) is not None and not isinstance(params[key], str):
                raise TaskError("invalid_execution", f"Parametre d'execution invalide: {key}")
        new_id = f"task_{uuid.uuid4().hex[:16]}" if task_id is None else validate_task_id(task_id)
        if self.store.exists(new_id):
            raise TaskError(
                "task_already_exists",
                f"Tache deja enregistree (etat terminal ou existant): {new_id}",
            )

        record = TaskRecord(
            task_id=new_id,
            story_id=story_id.strip(),
            project=str(project or self.store.project),
            status=declared,
            subprocess_id=worker_name_for(story_id.strip()),
            payload={"request": request} if isinstance(request, str) and request else None,
        )
        record.append_entry("event", f"Ouverture de tache via {command}", declared)

        handle = self.spawner.launch(record, params)
        self.store.stage(record)
        if time.monotonic() - started > self.budget_s:
            # Seuil franchi : aucune tache enregistree, aucun sous-processus lance.
            self.store.discard_staged(new_id)
            handle.terminate(timeout_s=1.0)
            raise TaskError(
                "response_budget_exceeded",
                f"Seuil de reponse immediate ({self.budget_s}s) franchi : tache non engagee.",
            )
        self.store.commit(new_id)
        register_handle(new_id, handle)
        handle.arm()
        logger.info(
            "Tache ouverte",
            extra={
                "task_id": new_id,
                "story_id": record.story_id,
                "status": record.status,
                "subprocess_id": record.subprocess_id,
            },
        )
        return self._open_view(record, str(command or "worker-spawn"))

    # ── 2. Avancement ─────────────────────────────────────────────────────
    def status_view(self, task_id: Any, since: Any = None) -> dict[str, Any]:
        validated = validate_task_id(task_id)
        fresh, cursor, record = self.store.read_journal(validated, since)
        return {
            "task_id": record.task_id,
            "status": record.status,
            "story_id": record.story_id,
            "created_at": to_iso(record.created_at),
            "expires_at": to_iso(record.expires_at),
            "subprocess_id": record.subprocess_id,
            "cursor": cursor,
            "journal": fresh,
        }

    # ── 3. Desistement ────────────────────────────────────────────────────
    def cancel(self, task_id: Any, reason: Any = None, timeout_s: float = 10.0) -> dict[str, Any]:
        validated = validate_task_id(task_id)
        record = self.store.load(validated)
        if record is None:
            raise TaskError("task_not_found", f"Tache inconnue ou emportee: {validated}")
        if record.is_terminal:
            raise TaskError(
                "task_already_terminal",
                f"Le verdict ({record.status}) fait foi et ne peut pas etre defait.",
            )
        handle = get_handle(validated)
        if handle is None:
            raise TaskError(
                "subprocess_not_tracked",
                "Seul un sous-processus rattache au cycle de suivi peut etre arrete.",
            )
        if not handle.terminate(timeout_s=timeout_s):
            raise TaskError(
                "termination_timeout",
                "Extinction du sous-processus non confirmee dans le delai imparti.",
            )
        pop_handle(validated)
        motif = reason if isinstance(reason, str) and reason.strip() else "Desistement demande"
        settled = transition_record(
            self.store,
            validated,
            "cancelled",
            payload={"reason": motif},
            message=f"Desistement : {motif}",
        )
        return self._verdict_view(settled, include_journal=False)

    # ── 4. Verdict ────────────────────────────────────────────────────────
    def result_view(self, task_id: Any) -> dict[str, Any]:
        validated = validate_task_id(task_id)
        record = self.store.load(validated)
        if record is None:
            raise TaskError("task_not_found", f"Tache inconnue ou emportee: {validated}")
        if not record.is_terminal:
            raise TaskError(
                "task_still_active",
                f"Tache encore active ({record.status}) : le verdict n'est pas delivre.",
            )
        if record.expires_at is None or record.expires_at <= utc_now():
            raise TaskError(
                "task_expired",
                "Echeance de retention depassee : la tache ne peut plus livrer son verdict.",
            )
        view = self._verdict_view(record, include_journal=True)
        view["verdict"] = self._verdict_payload(record)
        return view

    # ── Vues partagees ────────────────────────────────────────────────────
    def _open_view(self, record: TaskRecord, command: str) -> dict[str, Any]:
        return {
            "task_id": record.task_id,
            "status": record.status,
            "created_at": to_iso(record.created_at),
            "expires_at": None,
            "subprocess_id": record.subprocess_id,
            "story_id": record.story_id,
            "command": command,
        }

    def _verdict_view(self, record: TaskRecord, include_journal: bool) -> dict[str, Any]:
        view = {
            "task_id": record.task_id,
            "status": record.status,
            "story_id": record.story_id,
            "created_at": to_iso(record.created_at),
            "expires_at": to_iso(record.expires_at),
            "subprocess_id": record.subprocess_id,
        }
        if include_journal:
            view["journal"] = list(record.journal)
        return view

    @staticmethod
    def _verdict_payload(record: TaskRecord) -> dict[str, Any]:
        key = VERDICT_KEYS.get(record.status, "deliverables")
        payload = record.payload or {}
        if key in payload:
            return {key: payload[key]}
        return {key: payload or None}
