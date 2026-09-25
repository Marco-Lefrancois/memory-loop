# -*- coding: utf-8 -*-
"""
Commande CLI `story-backfill` — rétro-équipement du journal des transitions
(MLOOP-270-BE / ADR-011, opération 3).

`story-backfill --project <p> --approver "<Nom>"` :
  - **CA-5** : approbateur vide ou identifiant machine ⇒ **ZÉRO écriture** — la
    validation humaine précède toute ouverture de fichier ;
  - **semence du journal** `origin: backfill` pour tout récit actif non
    journalisé (`from_status` inconnu, jamais de reconstitution d'auteur) ;
  - **stamps d'approbation** `validated_by` / `validated_at` sur les récits
    actifs non terminés uniquement — les récits terminaux restent intacts
    (exemption `scratch_prune.py` L155) et une approbation préexistante n'est
    jamais écrasée ;
  - la première entrée `origin: backfill` bascule `is_backfilled()` à True et
    fait monter la sévérité des contrôles WARNING → BLOCKING.

Idempotent : une seconde exécution ne réécrit rien (stamps déjà présents,
entrées déjà journalisées). Verrou inter-processus unique sur toute la durée
(ADR-0369 : timeout explicite).

Conforme ADR-0202 (≤300 lignes / ≤15 Ko) et ADR-0369.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

from src.cli import ZeroFluffConsole
from src.core.gate4_validator import validate_human_authority
from src.core.transition_journal import (
    append_entry,
    build_entry,
    index_last_entries,
    utc_now_iso,
)
from src.pipelines import _story_lock_io as lock_io
from src.utils.file_lock import InterProcessFileLock
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.story_backfill")

LOCK_TIMEOUT_S = 10.0

_BACKFILL_REQUIREMENT = (
    "un approbateur humain formel est requis pour tout backfill "
    '(ex: --approver "Marco") — aucune écriture sans approbation (CA-5).'
)


def handle_story_backfill(args: Any, state: Any, project_path: Path) -> int:
    """Rétro-équipement : journal `origin: backfill` + stamps sur récits actifs.

    Returns:
        0 si le backfill est complété, 1 sur refus CA-5 ou interruption I/O.
    """
    # CA-5 : validation de l'autorité humaine AVANT toute écriture.
    try:
        approver = validate_human_authority(
            str(getattr(args, "approver", None) or ""),
            context="Backfill du journal des transitions",
            requirement=_BACKFILL_REQUIREMENT,
        )
    except ValueError as exc:
        ZeroFluffConsole.error(str(exc))
        logger.error(
            "story-backfill refusé (CA-5) : approbateur invalide — zéro écriture",
            exc_info=True,
            extra={"command": "story-backfill"},
        )
        return 1

    try:
        seeded, stamped = _backfill_project(Path(project_path), approver)
    except OSError:
        ZeroFluffConsole.error(
            "Backfill interrompu (erreur I/O) — re-exécution idempotente possible."
        )
        logger.error(
            "story-backfill interrompu",
            exc_info=True,
            extra={"command": "story-backfill"},
        )
        return 1

    ZeroFluffConsole.success(
        f"Backfill terminé par '{approver}' : {seeded} entrée(s) origin=backfill "
        f"semée(s), {stamped} récit(s) actif(s) estampillé(s)."
    )
    logger.info(
        "story-backfill exécuté avec succès",
        extra={"command": "story-backfill", "seeded": seeded, "stamped": stamped},
    )
    return 0


def _backfill_project(project: Path, approver: str) -> Tuple[int, int]:
    """Équipe un projet sous verrou unique. Retourne (entrées semées, récits estampillés)."""
    root = lock_io.stories_root(project)
    stories = sorted(root.glob("**/*.md")) if root.exists() else []
    last_index = index_last_entries(project)
    stamp = utc_now_iso()
    seeded = 0
    stamped = 0

    with InterProcessFileLock(lock_io.lock_path(project), timeout=LOCK_TIMEOUT_S):
        for story in stories:
            frontmatter = lock_io.safe_frontmatter(story)
            status = str(frontmatter.get("status") or "")
            if status in lock_io.TERMINAL_STATUSES:
                # Exemption terminale (scratch_prune.py L155) : récit livré intact.
                continue

            story_id = str(frontmatter.get("id") or story.stem)
            original = story.read_text(encoding="utf-8")
            updated = original

            # Stamps d'approbation — uniquement les champs absents (jamais d'écrasement).
            for key in lock_io.APPROVAL_KEYS:
                if not str(frontmatter.get(key) or "").strip():
                    value = approver if key == "validated_by" else stamp
                    updated = lock_io.write_field(updated, key, value)
            if updated != original:
                story.write_text(updated, encoding="utf-8")
                stamped += 1

            # Semence du journal pour tout récit encore non journalisé.
            if story_id not in last_index and story.stem not in last_index:
                entry = build_entry(
                    story_id,
                    "",
                    status,
                    approver,
                    "story-backfill",
                    "backfill",
                )
                append_entry(project, entry)
                last_index[story_id] = entry
                seeded += 1

    return seeded, stamped
