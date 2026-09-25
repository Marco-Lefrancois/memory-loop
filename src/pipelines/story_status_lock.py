# -*- coding: utf-8 -*-
"""
Verrou anti-promotion — écrivain unique des transitions de statut (MLOOP-270-BE / ADR-011).

Répond à l'incident du 24/09/2026 (promotion sauvage de récits en `READY_FOR_DEV`
sans feu vert humain) en centralisant toute écriture de statut derrière un verrou
inter-processus couvrant **récit + journal**, avec journalisation atomique.

Opérations du plan :
  1. `set_story_status`     — seule porte d'entrée d'un changement de statut.
  2. `apply_human_approval` — seul écrivain de `validated_by` / `validated_at`.
  4. `scan_transitions`     — contrôle rétrogradant (jamais de suppression).

OQ-270-1 : `READY_FOR_DEV → READY_FOR_GROOMING` est illégal dans
`ALLOWED_TRANSITIONS`. La rétrogradation sanctionnée passe donc par
`lock_io.apply_sanction_downgrade()` (écriture directe, `origin: sanction`) qui
ne bypass que la FSM — jamais le verrou, jamais le journal.

Les helpers d'E/S, de parsing et l'exécution de la sanction sont isolés dans
`_story_lock_io.py` (plafond ADR-0202 : ≤300 lignes / ≤15 Ko par fichier).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.core.gate4_validator import validate_human_authority
from src.core.transition_journal import build_entry, index_last_entries
from src.core.transition_journal import is_backfilled, journal_path, utc_now_iso
from src.pipelines import _story_lock_io as lock_io
from src.pipelines.state_machine import StateMachineEngine, StateTransitionError
from src.state import StoryStatus
from src.utils.file_lock import InterProcessFileLock
from src.utils.logger import get_logger

logger = get_logger("pipelines.story_status_lock")

# Motif consigné dans toute entrée de sanction — SSOT : `_story_lock_io.py`.
SANCTION_REASON = lock_io.SANCTION_REASON

_APPROVAL_REQUIREMENT = (
    "une approbation humaine formelle est requise avant toute promotion en "
    "READY_FOR_DEV (champs validated_by / validated_at absents)."
)


def set_story_status(
    project: Path,
    story_id: str,
    target: str,
    actor: str,
    source_cmd: str,
    timeout_s: float = 10.0,
) -> Dict[str, Any]:
    """Change le statut d'un récit sous verrou, avec journalisation atomique.

    Séquence tout-ou-rien :
      1. acquisition du verrou inter-processus récit + journal (`timeout_s`
         explicite, `FileLockTimeoutError` en cas de contention) ;
      2. exigence d'approbation humaine si la cible est `READY_FOR_DEV` ;
      3. validation FSM (`validate_transition`) — refus ⇒ zéro écriture ;
      4. écriture du récit puis append au journal (`commit_with_rollback`) ;
      5. échec du journal ⇒ restauration du récit (rollback) puis relance.

    Returns:
        Dictionnaire `{"changed", "story_id", "from", "to"}`.

    Raises:
        StateTransitionError : statut cible inconnu, transition illicite, ou
            promotion en `READY_FOR_DEV` sans `validated_by` / `validated_at`.
        FileLockTimeoutError : verrou déjà détenu par une autre session.
    """
    project = Path(project)
    story = lock_io.resolve_story_file(project, story_id)
    normalized = str(target or "").strip().upper().replace(" ", "_").replace("-", "_")
    if normalized not in StoryStatus.__members__:
        raise StateTransitionError(f"[VERROU STATUT] Statut cible inconnu : {target!r}")
    target_status = StoryStatus[normalized]
    engine = StateMachineEngine(str(project))

    with InterProcessFileLock(lock_io.lock_path(project), timeout=timeout_s):
        original = story.read_text(encoding="utf-8")
        frontmatter = lock_io.parse_frontmatter(original)
        current = str(frontmatter.get("status") or "")
        resolved_id = str(frontmatter.get("id") or story.stem)

        if target_status is StoryStatus.READY_FOR_DEV:
            lock_io.require_approval(frontmatter, resolved_id)

        if current == target_status.value:
            logger.debug(
                "Transition idempotente ignorée (statut déjà cible)",
                extra={"story_id": resolved_id, "status": current},
            )
            return {
                "changed": False,
                "story_id": resolved_id,
                "from": current,
                "to": current,
            }

        engine.validate_transition(current, target_status.value)
        updated = lock_io.write_field(original, "status", target_status.value)
        entry = build_entry(resolved_id, current, target_status.value, actor, source_cmd, "api")
        lock_io.commit_with_rollback(story, project, original, updated, entry)

    return {
        "changed": True,
        "story_id": resolved_id,
        "from": current,
        "to": target_status.value,
    }


def apply_human_approval(
    project: Path,
    story_id: str,
    approver: str,
    timeout_s: float = 10.0,
    source_cmd: str = "story-approve",
) -> Dict[str, Any]:
    """Appose l'approbation humaine sur un récit, sous verrou (opération 2).

    Seul écrivain des champs `validated_by` / `validated_at`. Écrit les deux
    stamps **puis** journalise une entrée `kind=approval` via `commit_with_rollback` :
    un échec du journal restaure le récit d'origine (même contrat tout-ou-rien que
    la transition).

    Raises:
        ValueError : approbateur vide ou identifiant machine (`validate_human_authority`).
        StateTransitionError : récit au statut terminal (aucune approbation a posteriori).
    """
    project = Path(project)
    approver_name = validate_human_authority(
        approver, context="Approbation de récit", requirement=_APPROVAL_REQUIREMENT
    )
    story = lock_io.resolve_story_file(project, story_id)
    stamp = utc_now_iso()

    with InterProcessFileLock(lock_io.lock_path(project), timeout=timeout_s):
        original = story.read_text(encoding="utf-8")
        frontmatter = lock_io.parse_frontmatter(original)
        status = str(frontmatter.get("status") or "")
        resolved_id = str(frontmatter.get("id") or story.stem)

        if status in lock_io.TERMINAL_STATUSES:
            raise StateTransitionError(
                f"[VERROU ANTI-PROMOTION] Le récit '{resolved_id}' est au statut "
                f"terminal {status} : approbation refusée (aucune validation rétroactive)."
            )

        updated = lock_io.write_field(original, "validated_by", approver_name)
        updated = lock_io.write_field(updated, "validated_at", stamp)
        approval = {"approver": approver_name, "validated_at": stamp}
        entry = build_entry(
            resolved_id,
            status,
            status,
            approver_name,
            source_cmd,
            "api",
            "approval",
            **approval,
        )
        lock_io.commit_with_rollback(story, project, original, updated, entry)

    logger.info(
        "Approbation humaine enregistrée",
        extra={"story_id": resolved_id, "approver": approver_name, "validated_at": stamp},
    )
    return {
        "story_id": resolved_id,
        "status": status,
        "validated_by": approver_name,
        "validated_at": stamp,
    }


def scan_transitions(
    project: Path,
    apply_sanctions: bool = True,
    timeout_s: float = 10.0,
) -> Dict[str, Any]:
    """Contrôle rétrogradant : compare chaque ligne d'état à la dernière entrée du journal.

    Écarts détectés :
      - `approval_missing` : `READY_FOR_DEV` sans approbation ⇒ rétrogradation
        sanctionnée si `apply_sanctions=True`, sinon simple signalement ;
      - `unjournaled` : récit engagé (`GATED_STATUSES`) sans aucune entrée au
        journal — sévérité WARNING (récit legacy non rétro-équipé) ;
      - `state_mismatch` : le journal porte un statut différent du récit (édit
        brut de la ligne `status:`) — sévérité BLOCKING.

    Les statuts terminaux sont exemptés. Un récit illisible est ignoré avec log
    DEBUG (jamais d'interruption).

    `apply_sanctions=False` (usage `struct-check` / `vibe-check`) : lecture
    seule — `backlog/` n'est jamais modifié par un contrôle.
    """
    project = Path(project)
    root = lock_io.stories_root(project)
    exists = root.exists()
    stories = sorted(root.glob("**/*.md")) if exists else []
    if not exists:
        logger.debug(
            "Répertoire backlog/stories absent — scan neutralisé",
            extra={"project": str(project)},
        )

    last_index = index_last_entries(project)
    issues: List[Dict[str, Any]] = []
    downgraded: List[str] = []
    with InterProcessFileLock(lock_io.lock_path(project), timeout=timeout_s):
        for story in stories:
            frontmatter = lock_io.safe_frontmatter(story)
            raw_status = str(frontmatter.get("status") or "")
            sid = str(frontmatter.get("id") or story.stem)
            if raw_status in lock_io.TERMINAL_STATUSES:
                continue

            approved = all(str(frontmatter.get(k) or "").strip() for k in lock_io.APPROVAL_KEYS)
            last = last_index.get(sid, last_index.get(story.stem))

            if raw_status == StoryStatus.READY_FOR_DEV.value and not approved:
                detail = f"{raw_status} sans validated_by/validated_at"
                if apply_sanctions:
                    try:
                        lock_io.apply_sanction_downgrade(
                            project,
                            story,
                            sid,
                            raw_status,
                            actor="scan_transitions",
                            source_cmd="story-scan",
                        )
                        downgraded.append(sid)
                        detail += " [sanction_applied]"
                    except Exception as exc:
                        detail += " [sanction_failed]"
                        logger.debug(
                            "Sanction impossible — écart signalé sans interruption",
                            exc_info=True,
                            extra={"story_id": sid, "error": str(exc)},
                        )
                else:
                    detail += " [sanction_pending]"
                issues.append(lock_io.make_issue(sid, "approval_missing", detail))
            elif last is None and raw_status in lock_io.GATED_STATUSES:
                detail = f"{raw_status} sans entrée au journal"
                issues.append(lock_io.make_issue(sid, "unjournaled", detail))
            elif last is not None and str(last.get("to_status") or "") != raw_status:
                detail = f"journal={last.get('to_status')} != récit={raw_status}"
                issues.append(lock_io.make_issue(sid, "state_mismatch", detail))

    return {
        "project": project.name,
        "scanned": len(stories),
        "backfilled": is_backfilled(project),
        "journal": str(journal_path(project)),
        "issues": issues,
        "downgraded": downgraded,
    }
