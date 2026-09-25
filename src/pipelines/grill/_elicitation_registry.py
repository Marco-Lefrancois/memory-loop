"""
src/pipelines/grill/_elicitation_registry.py — Registre de décisions immuable
(MLOOP-213-BE).

Seul et unique point d'écriture des lignes de décision d'arbitrage
(``Projects/<projet>/memory/evidence/decision_records.jsonl``) : le
complétion de formulaire **et** le repli textuel empruntent exactement ce
chemin (traçabilité unifiée, récit §4).

Fichiers de type JSONL déclaratifs — aucun moteur de base de données
(ADR-0387, Exigence 7) ; lecture ligne à ligne, écriture en fin de fichier,
lignes immuables. La présence au registre est la **seule** preuve qu'une
question est tranchée : la détection « déjà répondu » ne consulte jamais
l'état d'attente (récit §4, scénario 6).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.pipelines.grill._elicitation import (
    DECISION_RECORDS_FILE,
    ElicitationError,
    REQUIRED_DECISION_FIELDS,
    resolve_project_dir,
)

logger = logging.getLogger(__name__)


def decision_records_path(
    project_path: Optional[Path] = None, project: Optional[str] = None
) -> Path:
    return (
        resolve_project_dir(project_path, project) / "memory" / "evidence" / DECISION_RECORDS_FILE
    )


def read_decision_records(
    project_path: Optional[Path] = None, project: Optional[str] = None
) -> list[dict[str, Any]]:
    """Lit le registre **ligne à ligne** (JSONL déclaratif, aucun moteur BDD)."""
    path = decision_records_path(project_path, project)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                logger.debug(
                    "decision_record_ligne_ignorable",
                    extra={
                        "component": "pipelines.grill.elicitation.registry",
                        "operation": "read_decision_records",
                        "path": str(path),
                        "line": line_no,
                    },
                )
                continue
            if isinstance(parsed, dict):
                records.append(parsed)
    return records


def find_decision(
    elicitation_id: str,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Première ligne portant cet identifiant, ou ``None``."""
    for record in read_decision_records(project_path, project):
        if record.get("elicitation_id") == elicitation_id:
            return record
    return None


def is_answered(
    elicitation_id: str,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> bool:
    """Présence au registre = question tranchée. **Seule** source de vérité."""
    return find_decision(elicitation_id, project_path, project) is not None


def record_decision(
    *,
    elicitation_id: str,
    story_id: str,
    question: str,
    answer: Any,
    answered_by: str,
    fallback_used: bool,
    adr_ref: Optional[str] = None,
    answered_at: Optional[datetime] = None,
    project_path: Optional[Path] = None,
    project: Optional[str] = None,
) -> dict[str, Any]:
    """**Chemin unique d'écriture** : une ligne complète ajoutée en fin de
    registre, jamais modifiée ensuite. Lève :class:`ElicitationError` si la
    ligne est incomplète — rien n'est alors écrit (zéro entrée partielle)."""
    record: dict[str, Any] = {
        "elicitation_id": str(elicitation_id),
        "story_id": str(story_id),
        "question": str(question),
        "answer": answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False),
        "answered_by": str(answered_by),
        "answered_at": (answered_at or datetime.now(timezone.utc)).isoformat(),
        "fallback_used": bool(fallback_used),
    }
    if adr_ref:
        record["adr_ref"] = str(adr_ref)
    missing = [field for field in REQUIRED_DECISION_FIELDS if record.get(field) in (None, "")]
    if missing:
        raise ElicitationError([f"ligne_incomplete:{field}" for field in missing])
    path = decision_records_path(project_path, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.debug(
        "decision_record_written",
        extra={
            "component": "pipelines.grill.elicitation.registry",
            "operation": "record_decision",
            "elicitation_id": record["elicitation_id"],
            "story_id": record["story_id"],
            "fallback_used": record["fallback_used"],
            "path": str(path),
        },
    )
    return record
