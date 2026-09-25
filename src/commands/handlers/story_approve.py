# -*- coding: utf-8 -*-
"""
Commande CLI `story-approve` — approbation humaine d'un récit (MLOOP-270-BE / ADR-011).

Opération 2 du verrou anti-promotion :
  1. `validate_human_authority()` — rejette tout approbateur vide ou identifiant
     machine (AI, bot, sentinel, agent...) **avant** toute écriture ;
  2. `apply_human_approval()` — seul écrivain de `validated_by` / `validated_at`,
     sous verrou inter-processus, avec entrée `kind: approval` atomique au
     journal `story_transitions.jsonl`.

Rejets garantis (exit code 1, **zéro écriture**) :
  - approbateur vide ou machine (CA-5) ;
  - récit introuvable sous `backlog/stories/` ;
  - récit au statut terminal (aucune validation rétroactive) ;
  - verrou déjà détenu par une autre session (`FileLockTimeoutError`).

Conforme ADR-0202 (≤300 lignes / ≤15 Ko) et ADR-0369 (observabilité ERROR).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.cli import ZeroFluffConsole
from src.core.gate4_validator import validate_human_authority
from src.pipelines.state_machine import StateTransitionError
from src.pipelines.story_status_lock import apply_human_approval
from src.utils.file_lock import FileLockTimeoutError
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.story_approve")

_APPROVAL_REQUIREMENT = (
    'une approbation humaine formelle est requise (ex: --approver "Marco" ou "Lead Architect").'
)


def handle_story_approve(args: Any, state: Any, project_path: Path) -> int:
    """`story-approve --project <p> --story <ID> --approver "<Nom>"` (opération 2).

    Returns:
        0 si l'approbation est enregistrée, 1 sur tout refus documenté.
    """
    story_id = str(getattr(args, "story", None) or "")
    try:
        approver = validate_human_authority(
            str(getattr(args, "approver", None) or ""),
            context="Approbation de récit",
            requirement=_APPROVAL_REQUIREMENT,
        )
        result = apply_human_approval(Path(project_path), story_id, approver)
    except (ValueError, FileNotFoundError, StateTransitionError, FileLockTimeoutError) as exc:
        ZeroFluffConsole.error(str(exc))
        logger.error(
            "story-approve refusé (aucune écriture)",
            exc_info=True,
            extra={"command": "story-approve", "story_id": story_id},
        )
        return 1

    ZeroFluffConsole.success(
        f"Approbation humaine enregistrée pour '{result['story_id']}' : "
        f"validated_by={result['validated_by']} @ {result['validated_at']}."
    )
    logger.info(
        "story-approve exécuté avec succès",
        extra={"command": "story-approve", "story_id": result["story_id"]},
    )
    return 0
