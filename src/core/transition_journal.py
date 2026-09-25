# -*- coding: utf-8 -*-
"""
Journal des transitions de statut des récits — append-only « Zéro Rollback »
(MLOOP-270-BE / ADR-011 EPIC-27).

Source unique de vérité de l'historique des changements d'état :
`Projects/<p>/memory/story_transitions.jsonl` (versionné, cf. OQ-270-2).

Contrats :
  - **Append-only** : aucune entrée n'est jamais réécrite ni supprimée ;
    l'ordre chronologique constitue la preuve (ADR-011 Q3).
  - **Écriture durable** : `flush()` + `fsync()` sous `with` (ADR-0369 §2/§3).
  - **Failure Contract** : un échec d'écriture lève une exception propagée — le
    caller annule alors sa transition (atomicité récit + journal, ADR-0369 §5).
  - **Zéro silent-pass** : toute ligne corrompue est tracée en DEBUG avec
    `exc_info=True` puis écartée (résilience de lecture, jamais de purge).

Schéma d'entrée :
  `ts` (ISO-8601 UTC), `story_id`, `from_status`, `to_status`, `actor`,
  `source_cmd`, `origin` ∈ {api, raw_edit_detected, backfill, sanction},
  `kind` ∈ {transition, approval, control_claim}
  + `approval` (kind=approval) ou `claim` (kind=control_claim).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("core.transition_journal")

JOURNAL_FILENAME = "story_transitions.jsonl"
ORIGINS = ("api", "raw_edit_detected", "backfill", "sanction")
KINDS = ("transition", "approval", "control_claim")


def journal_path(project: Path) -> Path:
    """Chemin canonique du journal append-only d'un projet."""
    return Path(project) / "memory" / JOURNAL_FILENAME


def utc_now_iso() -> str:
    """Horodatage UTC ISO-8601 normalisé pour toutes les entrées."""
    return datetime.now(timezone.utc).isoformat()


def build_entry(
    story_id: str,
    from_status: str,
    to_status: str,
    actor: str,
    source_cmd: str,
    origin: str,
    kind: str = "transition",
    **extra: Any,
) -> Dict[str, Any]:
    """Construit une entrée conforme au schéma. Lève ValueError sur domaine invalide."""
    if origin not in ORIGINS:
        raise ValueError(
            f"origine d'écriture inconnue : {origin!r} (attendu : {', '.join(ORIGINS)})"
        )
    if kind not in KINDS:
        raise ValueError(f"type d'entrée inconnu : {kind!r} (attendu : {', '.join(KINDS)})")
    entry: Dict[str, Any] = {
        "ts": utc_now_iso(),
        "story_id": str(story_id),
        "from_status": str(from_status),
        "to_status": str(to_status),
        "actor": str(actor),
        "source_cmd": str(source_cmd),
        "origin": origin,
        "kind": kind,
    }
    entry.update(extra)
    return entry


def append_entry(project: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appose une ligne JSON au journal. Échec ⇒ exception propagée (aucun repli
    silencieux) : c'est le contrat qui rend la transition « tout-ou-rien ».
    """
    path = journal_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    logger.debug(
        "Entrée journal appendée",
        extra={
            "story_id": entry.get("story_id"),
            "origin": entry.get("origin"),
            "kind": entry.get("kind"),
        },
    )
    return entry


def read_entries(project: Path) -> List[Dict[str, Any]]:
    """Lit toutes les entrées valides du journal dans leur ordre chronologique."""
    path = journal_path(project)
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(
                    "Ligne de journal illisible écartée (lecture résiliente, jamais de purge)",
                    exc_info=True,
                    extra={"journal": str(path)},
                )
                continue
            if isinstance(data, dict):
                entries.append(data)
            else:
                logger.debug(
                    "Entrée de journal hors schéma écartée",
                    extra={"journal": str(path), "payload_type": type(data).__name__},
                )
    return entries


def last_entry_for(project: Path, story_id: str) -> Optional[Dict[str, Any]]:
    """Dernière entrée d'un récit donné, ou None si le récit n'est pas journalisé."""
    for entry in reversed(read_entries(project)):
        if entry.get("story_id") == story_id:
            return entry
    return None


def index_last_entries(project: Path) -> Dict[str, Dict[str, Any]]:
    """Index `story_id -> dernière entrée` lu une seule fois (scan project-wide)."""
    index: Dict[str, Dict[str, Any]] = {}
    for entry in read_entries(project):
        sid = entry.get("story_id")
        if isinstance(sid, str) and sid:
            index[sid] = entry
    return index


def is_backfilled(project: Path) -> bool:
    """
    True dès qu'au moins une entrée `origin: backfill` existe : le projet a été
    rétro-équipé, la sévérité des contrôles bascule WARNING → BLOCKING/FAIL.
    """
    return any(entry.get("origin") == "backfill" for entry in read_entries(project))


def append_control_claim(
    project: Path, control: str, artifact: str, actor: str, source_cmd: str
) -> Dict[str, Any]:
    """
    Enregistre la revendication d'exécution d'un contrôle (CA-4). Le contrôle de
    gouvernance confronte ensuite `claim.artifact` au disque : sans artefact
    réel, la revendication est signalée « non corroborée ».
    """
    entry = build_entry(
        story_id="",
        from_status="",
        to_status="",
        actor=actor,
        source_cmd=source_cmd,
        origin="api",
        kind="control_claim",
        claim={"control": control, "artifact": artifact},
    )
    return append_entry(project, entry)
