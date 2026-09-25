"""
task_spawner.py - Lancement asynchrone des compagnons de travail (MLOOP-211-BE).

`tasks/create` encapsule le cycle de lancement **existant**
(`HerdrWorkerMixin.spawn_story_worker`) sans le dupliquer ni le regresser :
le sous-processus est lance dans un thread de demonsation, la session
appelante n'attend jamais sa fin et ne pose aucun verrou.

La poignee retournee porte l'identifiant du sous-processus (nom d'agent
Herdr, deterministe avant lancement) et un arret **borne** conforme au
desistement (`tasks/cancel`) : seul un sous-processus enregistre dans le
cycle de suivi est susceptible d'arret.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from src.core.task_handles import TaskRecord

logger = logging.getLogger("mloop.task_spawner")

FailureCallback = Callable[[str, str], None]
EventCallback = Callable[[str, str], None]


class TaskSpawner(Protocol):
    """Lanceur de sous-processus rattache au cycle de suivi."""

    def launch(self, record: TaskRecord, execution: Mapping[str, Any]) -> "HerdrLaunchHandle": ...


def worker_name_for(story_id: str) -> str:
    """Nom d'agent Herdr deterministe (meme formule que spawn_story_worker)."""
    clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", story_id).lower()
    return f"worker_{clean_id}"[:32]


@dataclass
class HerdrLaunchHandle:
    """Poignee de sous-processus : arret borne, jamais de processus etranger."""

    task_id: str
    subprocess_id: str
    on_failure: FailureCallback
    on_event: EventCallback
    worker_name: str = ""
    pane_id: str | None = None
    armed: bool = False
    started: bool = False
    cancel_event: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None

    def arm(self) -> None:
        """Engage reellement le sous-processus (uniquement apres publication)."""
        if self.cancel_event.is_set() or self.thread is None:
            return
        self.armed = True
        self.thread.start()

    def terminate(self, timeout_s: float = 10.0) -> bool:
        """Arret borne du sous-processus ; False si l'extinction n'est pas prouvee."""
        self.cancel_event.set()
        if not self.armed or not self.started:
            # Jamais engage ou deja termine : aucun sous-processus ne subsiste.
            return True
        outcome: dict[str, bool] = {"closed": False}

        def _close() -> None:
            from src.core.herdr_adapter import herdr

            try:
                result = herdr.cleanup_worker(self.worker_name or self.subprocess_id)
                outcome["closed"] = bool(result.get("success"))
            except Exception as exc:
                logger.debug(
                    "Extinction du sous-processus echouee",
                    exc_info=True,
                    extra={"task_id": self.task_id, "error": str(exc)},
                )

        closer = threading.Thread(target=_close, name=f"task-cancel-{self.task_id}", daemon=True)
        closer.start()
        closer.join(timeout_s)
        if closer.is_alive():
            logger.warning(
                "Extinction bornee du sous-processus non confirmee",
                extra={"task_id": self.task_id, "timeout_s": timeout_s},
            )
            return False
        return bool(outcome["closed"])

    def _run(self, project: str, story_id: str, execution: Mapping[str, Any]) -> None:
        if self.cancel_event.is_set():
            return
        from src.core.herdr_adapter import herdr

        try:
            result = herdr.spawn_story_worker(
                project_name=project,
                story_id=story_id,
                kind=str(execution.get("kind") or "opencode"),
                model=execution.get("model"),
                task_type=execution.get("task_type"),
                extra_args=list(execution.get("extra_args") or []) or None,
            )
        except Exception as exc:
            logger.debug(
                "Lancement du compagnon de travail interrompu",
                exc_info=True,
                extra={"task_id": self.task_id, "story_id": story_id},
            )
            self.on_failure(self.task_id, f"Lancement impossible: {exc}")
            return
        if not isinstance(result, dict) or not result.get("success"):
            cause = "Lancement refuse par le runtime Herdr"
            if isinstance(result, dict):
                cause = str(result.get("error") or cause)
            self.on_failure(self.task_id, cause)
            return
        self.worker_name = str(result.get("worker_name") or self.worker_name)
        self.pane_id = result.get("pane_id")
        self.started = True
        self.on_event(
            self.task_id,
            f"Compagnon de travail lance (agent={self.worker_name}, pane={self.pane_id})",
        )
        if self.cancel_event.is_set():
            self.terminate()


class HerdrTaskSpawner:
    """Lance le cycle de lancement existant hors de la session appelante."""

    def __init__(
        self,
        on_failure: FailureCallback | None = None,
        on_event: EventCallback | None = None,
    ) -> None:
        self._on_failure = on_failure or (lambda task_id, cause: None)
        self._on_event = on_event or (lambda task_id, message: None)

    def launch(self, record: TaskRecord, execution: Mapping[str, Any]) -> HerdrLaunchHandle:
        handle = HerdrLaunchHandle(
            task_id=record.task_id,
            subprocess_id=record.subprocess_id or record.task_id,
            on_failure=self._on_failure,
            on_event=self._on_event,
        )
        handle.worker_name = handle.subprocess_id
        handle.thread = threading.Thread(
            target=handle._run,
            args=(record.project, record.story_id, dict(execution)),
            name=f"task-launch-{record.task_id}",
            daemon=True,
        )
        # Le thread n'est engage qu'apres publication de l'enregistrement
        # (voir TaskService.create) : aucun echec de lancement ne peut naitre
        # avant que la tache n'existe physiquement.
        return handle
