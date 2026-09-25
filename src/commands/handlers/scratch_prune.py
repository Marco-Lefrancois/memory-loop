"""
Nettoyage automatique et rétention des artefacts de session (MLOOP-233-BE / ADR-015).

Assure la purge des résidus temporaires (memory/scratch/, memory/tmp/),
le bornage FIFO strict à 10 checkpoints dans memory/compaction/history/,
la sanctuarisation de memory/evidence/ et memory/plan/, et le hook au statut DONE_TESTED / SHIPPED.
Conforme ADR-0003, ADR-015, ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.scratch_prune")

DEFAULT_OLDER_THAN_HOURS: int = 48
MAX_COMPACTION_CHECKPOINTS: int = 10
_SCRATCH_LOCK = threading.Lock()


def _resolve_scratch_dirs(base_dir: Optional[Path] = None) -> List[Path]:
    """Résout l'ensemble des répertoires temporaires scratch et tmp existants."""
    root = base_dir if base_dir else Path(".")
    dirs: List[Path] = [
        root / "memory" / "scratch",
        root / "memory" / "tmp",
    ]

    projects_dir = root / "Projects"
    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if p.is_dir():
                dirs.append(p / "memory" / "scratch")
                dirs.append(p / "memory" / "tmp")

    return [d for d in dirs if d.exists() and d.is_dir()]


def prune_compaction_checkpoints(
    history_dir: Optional[Path] = None,
    max_keep: int = MAX_COMPACTION_CHECKPOINTS,
) -> List[Path]:
    """Borne l'historique des checkpoints à max_keep (FIFO, suppression des plus anciens)."""
    target_dir = history_dir if history_dir else Path("memory/compaction/history")
    if not target_dir.exists():
        return []

    checkpoints = [p for p in target_dir.glob("*.json") if p.is_file()]
    if len(checkpoints) <= max_keep:
        return []

    # Tri par date de modification croissante (les plus anciens d'abord)
    checkpoints.sort(key=lambda p: p.stat().st_mtime)
    excess_count = len(checkpoints) - max_keep
    to_prune = checkpoints[:excess_count]

    pruned: List[Path] = []
    for item in to_prune:
        try:
            item.unlink(missing_ok=True)
            pruned.append(item)
            logger.info("Checkpoint ancien élagué : %s", item.name)
        except OSError as exc:
            logger.debug("Impossible d'élaguer le checkpoint %s : %s", item, exc, exc_info=True)

    return pruned


def prune_scratch_artifacts(
    base_dir: Optional[Path] = None,
    older_than_hours: int = DEFAULT_OLDER_THAN_HOURS,
    purge_all: bool = False,
    story_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Nettoie les artefacts jetables des répertoires scratch et tmp.
    Sanctuarise de manière absolue les dossiers evidence/ et plan/.
    """
    if older_than_hours < 0:
        raise ValueError(f"La durée en heures ne peut être négative (reçu: {older_than_hours})")

    root = base_dir if base_dir else Path(".")
    scratch_dirs = _resolve_scratch_dirs(root)
    cutoff_seconds = time.time() - (older_than_hours * 3600)

    pruned_files: List[Path] = []
    reclaimed_bytes = 0

    with _SCRATCH_LOCK:
        for sdir in scratch_dirs:
            for item in sdir.glob("*"):
                if not item.is_file():
                    continue

                # Règle de sanctuarisation absolue
                parts = item.parts
                if "evidence" in parts or "plan" in parts:
                    continue

                should_delete = False
                if story_id:
                    # Nettoyage ciblé sur le récit clôturé
                    if story_id.lower() in item.name.lower():
                        should_delete = True
                elif purge_all:
                    should_delete = True
                else:
                    try:
                        if item.stat().st_mtime < cutoff_seconds:
                            should_delete = True
                    except OSError as exc:
                        logger.debug("Erreur lecture mtime %s : %s", item, exc, exc_info=True)

                if should_delete:
                    try:
                        sz = item.stat().st_size
                        item.unlink(missing_ok=True)
                        pruned_files.append(item)
                        reclaimed_bytes += sz
                    except OSError as exc:
                        logger.debug("Échec suppression artefact scratch %s : %s", item, exc, exc_info=True)

        history_dir = root / "memory" / "compaction" / "history"
        pruned_checkpoints = prune_compaction_checkpoints(history_dir=history_dir, max_keep=MAX_COMPACTION_CHECKPOINTS)

    reclaimed_mb = round(reclaimed_bytes / (1024 * 1024), 2)
    return {
        "pruned_files_count": len(pruned_files),
        "checkpoints_pruned_count": len(pruned_checkpoints),
        "reclaimed_bytes": reclaimed_bytes,
        "reclaimed_mb": reclaimed_mb,
        "pruned_files": [str(p) for p in pruned_files],
        "pruned_checkpoints": [str(p) for p in pruned_checkpoints],
    }


def on_story_status_transition(
    story_id: str,
    new_status: str,
    base_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Hook événementiel déclenché à la transition d'un récit de travail.
    Purge automatiquement les artefacts scratch associés lors du passage à DONE_TESTED / SHIPPED.
    """
    status_upper = str(new_status).strip().upper()
    terminal_statuses = {"DONE_TESTED", "SHIPPED", "DONE", "ACCEPTED", "QA_CERTIFIED", "READY_TO_SHIP"}

    if status_upper not in terminal_statuses:
        return {"hook_executed": False, "pruned_count": 0, "reason": "status_not_terminal"}

    try:
        summary = prune_scratch_artifacts(base_dir=base_dir, story_id=story_id)
        logger.info(
            "Hook transition récit %s vers %s : %d artefact(s) scratch purgé(s)",
            story_id,
            status_upper,
            summary["pruned_files_count"],
        )
        return {
            "hook_executed": True,
            "story_id": story_id,
            "status": status_upper,
            "pruned_count": summary["pruned_files_count"],
        }
    except Exception as exc:
        logger.debug("Échec non-bloquant du hook scratch pour %s : %s", story_id, exc, exc_info=True)
        return {"hook_executed": False, "error": str(exc), "pruned_count": 0}


def handle_scratch(args: argparse.Namespace, state: Any, project_path: Optional[Path]) -> int:
    """Point d'entrée CLI pour la commande `mloop scratch prune`."""
    action = getattr(args, "action", "prune") or "prune"
    purge_all = bool(getattr(args, "all", False))
    older_than_hours = getattr(args, "older_than_hours", DEFAULT_OLDER_THAN_HOURS)

    if action != "prune":
        ZeroFluffConsole.error(f"Action scratch inconnue : '{action}'. Action valide : prune.")
        return 1

    try:
        hours_val = int(older_than_hours)
        if hours_val < 0:
            raise ValueError()
    except (ValueError, TypeError):
        ZeroFluffConsole.error(
            f"Paramètre --older-than-hours invalide : '{older_than_hours}'. Doit être un entier >= 0."
        )
        return 1

    mode_label = "TOUS LES FICHIERS" if purge_all else f"> {hours_val}h"
    ZeroFluffConsole.info(f"=== NETTOYAGE DES ARTEFACTS DE SESSION SCRATCH ({mode_label}) ===")
    base_dir = project_path if project_path else Path(".")

    try:
        res = prune_scratch_artifacts(base_dir=base_dir, older_than_hours=hours_val, purge_all=purge_all)
        ZeroFluffConsole.success(
            f"Nettoyage achevé : {res['pruned_files_count']} fichier(s) scratch éliminé(s) "
            f"et {res['checkpoints_pruned_count']} checkpoint(s) excédentaire(s) archivé(s)."
        )
        ZeroFluffConsole.info(f"Gain d'espace : {res['reclaimed_mb']} Mo libérés.")
        return 0
    except Exception as err:
        ZeroFluffConsole.error(f"Échec du nettoyage scratch : {err}")
        logger.error("Erreur lors de handle_scratch: %s", err, exc_info=True)
        return 1
