"""
task_handles.py - Registre durable des handles de tache (MLOOP-211-BE).

Extension Tasks (`io.modelcontextprotocol/tasks`, ADR-0387 Pilier 1) : chaque
travail long est declare sous `Projects/<projet>/memory/tasks/<task_id>.json`
en ecriture atomique tout-ou-rien, portant identifiant, etat courant,
horodatage d'ouverture, echeance de retention, identifiant du sous-processus
et rattachement au recit traite.

Contrats tranches par le recit : vocabulaire ferme a 5 etats en mapping direct
avec le cycle de vie des compagnons (aucun second moteur d'etat) ; echeance
nulle tant que la tache vit et calculee uniquement a l'atteinte d'un etat
terminal (cf. `task_lifecycle.transition_record`) ; aucune purge : la
suppression physique appartient au chantier de retention (EPIC-23) et seul le
rejet de purge est expose ici (`purge_guard`).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger("mloop.task_handles")

TASK_STATES: tuple[str, ...] = ("working", "input_required", "completed", "failed", "cancelled")
ACTIVE_STATES: tuple[str, ...] = ("working", "input_required")
TERMINAL_STATES: tuple[str, ...] = ("completed", "failed", "cancelled")

# Mapping 1:1 avec le cycle de vie des compagnons de travail (SSOT unique).
AGENT_STATE_MAP: dict[str, str] = {
    "working": "working",
    "busy": "working",
    "blocked": "input_required",
    "idle": "completed",
    "done": "completed",
    "failed": "failed",
    "error": "failed",
    "stopped": "cancelled",
    "closed": "cancelled",
}

_TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_JOURNAL_KINDS: tuple[str, ...] = ("state", "output", "event")


class TaskError(Exception):
    """Rejet metier a motif explicite - jamais d'ecriture partielle."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def is_valid_state(state: Any) -> bool:
    return isinstance(state, str) and state in TASK_STATES


def is_terminal(state: Any) -> bool:
    return isinstance(state, str) and state in TERMINAL_STATES


def map_agent_state(agent_state: Any, default: str = "working") -> str:
    """Convertit un etat Herdr vers le vocabulaire ferme Tasks (mapping 1:1)."""
    key = agent_state.strip().lower() if isinstance(agent_state, str) else default
    return AGENT_STATE_MAP.get(key, default)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def from_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        logger.debug("Horodatage de tache illisible", extra={"value": value})
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def validate_task_id(task_id: Any) -> str:
    """Valide un identifiant de tache (anti traversal de chemin)."""
    if not isinstance(task_id, str) or not _TASK_ID_RE.match(task_id):
        raise TaskError("invalid_task_id", f"Identifiant de tache invalide: {task_id!r}")
    return task_id


@dataclass
class TaskRecord:
    """Enregistrement durable d'un handle de tache."""

    task_id: str
    story_id: str
    project: str
    status: str = "working"
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    subprocess_id: str | None = None
    payload: dict[str, Any] | None = None
    journal: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return is_terminal(self.status)

    @property
    def is_purgeable(self) -> bool:
        return self.expires_at is not None

    def append_entry(self, kind: str, message: str, status: str | None = None) -> dict[str, Any]:
        """Ajoute une entree de journal (sequence croissante, jamais de sondage)."""
        entry = {
            "seq": len(self.journal) + 1,
            "at": to_iso(utc_now()),
            "kind": kind if kind in _JOURNAL_KINDS else "event",
            "status": status or self.status,
            "message": message,
        }
        self.journal.append(entry)
        return entry

    def journal_since(self, since: Any) -> tuple[list[dict[str, Any]], int]:
        """Lecture incrémentale : ni consommation ni altération du journal."""
        try:
            cursor = int(since) if since is not None else 0
        except (TypeError, ValueError):
            cursor = 0
        if cursor < 0:
            cursor = 0
        fresh = [entry for entry in self.journal if int(entry.get("seq", 0)) > cursor]
        return fresh, len(self.journal)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "story_id": self.story_id,
            "project": self.project,
            "status": self.status,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
            "expires_at": to_iso(self.expires_at),
            "subprocess_id": self.subprocess_id,
            "payload": self.payload,
            "journal": list(self.journal),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TaskRecord:
        status = data.get("status", "working")
        if not is_valid_state(status):
            status = "failed"
        journal = data.get("journal")
        return cls(
            task_id=str(data.get("task_id", "")),
            story_id=str(data.get("story_id", "")),
            project=str(data.get("project", "")),
            status=status,
            created_at=from_iso(data.get("created_at")) or utc_now(),
            updated_at=from_iso(data.get("updated_at")) or utc_now(),
            expires_at=from_iso(data.get("expires_at")),
            subprocess_id=data.get("subprocess_id"),
            payload=data.get("payload") if isinstance(data.get("payload"), dict) else None,
            journal=list(journal) if isinstance(journal, list) else [],
        )


class TaskStore:
    """Lecture/ecriture atomique des enregistrements sous memory/tasks/."""

    def __init__(self, project: str, base_dir: str | Path = "Projects") -> None:
        self.project = project or "mLoop"
        self.base_dir = Path(base_dir)

    @property
    def tasks_dir(self) -> Path:
        directory = self.base_dir / self.project / "memory" / "tasks"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def path_for(self, task_id: str) -> Path:
        return self.tasks_dir / f"{validate_task_id(task_id)}.json"

    def exists(self, task_id: str) -> bool:
        return self.path_for(task_id).exists()

    def load(self, task_id: str) -> TaskRecord | None:
        path = self.path_for(task_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.debug(
                "Enregistrement de tache illisible",
                exc_info=True,
                extra={"task_id": task_id, "error": str(exc)},
            )
            return None
        if not isinstance(payload, dict):
            return None
        return TaskRecord.from_dict(payload)

    def _write(self, record: TaskRecord, publish: bool) -> Path:
        """Ecrit l'enregistrement : temporaire, puis publication optionnelle."""
        path = self.path_for(record.task_id)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(record.to_dict(), handle, ensure_ascii=False, indent=2)
            handle.flush()
        if publish:
            tmp_path.replace(path)
        return tmp_path

    def save(self, record: TaskRecord) -> Path:
        """Ecriture atomique (fichier temporaire puis remplacement)."""
        return self._write(record, publish=True)

    def stage(self, record: TaskRecord) -> Path:
        """Ecrit l'enregistrement engageable en attente de validation du budget."""
        return self._write(record, publish=False)

    def commit(self, task_id: str) -> Path:
        """Publie l'enregistrement staged : aucune tache n'existe avant cet instant."""
        path = self.path_for(task_id)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        if not tmp_path.exists():
            raise TaskError("task_not_staged", f"Aucune tache staged pour {task_id}")
        tmp_path.replace(path)
        return path

    def discard_staged(self, task_id: str) -> bool:
        """Retire l'enregistrement non engage (aucune tache n'a jamais existé)."""
        try:
            self.path_for(task_id).with_suffix(".json.tmp").unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            logger.debug(
                "Retrait d'enregistrement staged impossible",
                exc_info=True,
                extra={"task_id": task_id, "error": str(exc)},
            )
            return False

    def read_journal(self, task_id: str, since: Any = None) -> tuple[list[dict], int, TaskRecord]:
        record = self.load(task_id)
        if record is None:
            raise TaskError("task_not_found", f"Tache inconnue ou emportee: {task_id}")
        fresh, cursor = record.journal_since(since)
        return fresh, cursor, record

    def find_active_for_story(self, identifier: str) -> TaskRecord | None:
        """Localise la tache **active** rattachee a un recit ou a un compagnon."""
        try:
            candidates = sorted(
                p for p in self.tasks_dir.glob("*.json") if not p.name.endswith(".tmp")
            )
        except OSError as exc:
            logger.debug("Index de taches inaccessible", exc_info=True, extra={"error": str(exc)})
            return None
        for path in candidates:
            record = self.load(path.stem)
            if (
                record
                and not record.is_terminal
                and identifier in (record.story_id, record.subprocess_id)
            ):
                return record
        return None

    def purge_guard(self, task_id: str) -> dict[str, Any]:
        """Contrat d'echeance lisible - aucune purge n'est jamais executee."""
        record = self.load(task_id)
        if record is None:
            raise TaskError("task_not_found", f"Tache inconnue ou emportee: {task_id}")
        if not record.is_purgeable:
            raise TaskError("purge_refused", "Tache vivante (echeance nulle) : purge refusee.")
        if record.expires_at is not None and record.expires_at > utc_now():
            raise TaskError("purge_not_due", "Echeance de retention encore valide : purge refusee.")
        return {
            "task_id": record.task_id,
            "purgeable": True,
            "expires_at": to_iso(record.expires_at),
            "deletion_executed": False,
        }
