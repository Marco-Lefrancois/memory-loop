# -*- coding: utf-8 -*-
"""
CLI Handler for 'hook' command (mLoop Core - ADR-0364).

Permet d'exécuter, déclencher et tester les hooks de cycle de vie et de pré-compaction
depuis la CLI, les scripts shell ou les harnais d'agents (OpenCode, Claude Code, Antigravity).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Any

from src.cli import ZeroFluffConsole
from src.engine.hooks.compaction import PreCompactionHandler, CompactionRecoveryManager
from src.engine.hooks.registry import global_hook_registry
from src.utils.lexicon_resolver import SemanticLexiconResolver


def handle_hook(
    args: argparse.Namespace,
    state: Optional[Any] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Handler CLI officiel pour la commande 'hook'."""
    event = getattr(args, "event", "pre_compact") or "pre_compact"
    raw_project = getattr(args, "project", None) or (state.project_name if state else None)
    output_format = getattr(args, "format", "text") or "text"
    story_override = getattr(args, "story", None)

    # Résolution canonique du projet
    project_name = "Memory Loop"
    if raw_project:
        project_name = SemanticLexiconResolver.resolve_project_alias(raw_project) or raw_project

    base_dir = project_path if project_path else Path(".")

    # 1. Événement pre_compact
    if event == "pre_compact":
        try:
            checkpoint = PreCompactionHandler.create_checkpoint(
                project_name=project_name,
                focused_story_id=story_override,
                base_dir=base_dir,
            )
            # Déclenchement des handlers enregistrés dans le registre
            global_hook_registry.trigger("pre_compact", checkpoint.model_dump())

            if output_format == "json":
                print(checkpoint.model_dump_json(indent=2))
            else:
                ZeroFluffConsole.section("PRE-COMPACTION CHECKPOINT CRÉÉ (ADR-0364)")
                ZeroFluffConsole.value("Projet", checkpoint.project_name)
                ZeroFluffConsole.value("Story", checkpoint.focused_story_id or "N/A")
                ZeroFluffConsole.value("Stage", checkpoint.stage)
                ZeroFluffConsole.value("Fichiers réservés", len(checkpoint.file_reservations))
                ZeroFluffConsole.value("Hash SHA-256", (checkpoint.checkpoint_hash or "")[:12])
                print("\n" + checkpoint.resume_instructions + "\n")
            return 0
        except Exception as e:
            ZeroFluffConsole.error(f"Échec de l'exécution du hook pre_compact: {e}")
            return 1

    # 2. Événement resume / post_compact
    elif event in ("resume", "post_compact", "checkpoint_resume"):
        try:
            checkpoint = CompactionRecoveryManager.recover_checkpoint(
                project_name=project_name, base_dir=base_dir
            )
            if not checkpoint:
                ZeroFluffConsole.warning("Aucun checkpoint trouvé pour reprise.")
                return 1

            global_hook_registry.trigger("checkpoint_resume", checkpoint.model_dump())

            if output_format == "json":
                print(checkpoint.model_dump_json(indent=2))
            else:
                ZeroFluffConsole.section("REPRISE DE CHECKPOINT EFFECTUÉE (ADR-0364)")
                ZeroFluffConsole.value("Projet", checkpoint.project_name)
                ZeroFluffConsole.value("Story Cible", checkpoint.focused_story_id or "N/A")
                print("\n" + checkpoint.resume_instructions + "\n")
            return 0
        except Exception as e:
            ZeroFluffConsole.error(f"Échec de la récupération du checkpoint: {e}")
            return 1

    # 3. Autres événements généraux
    else:
        results = global_hook_registry.trigger(event, {"project": project_name})
        ZeroFluffConsole.info(f"Événement '{event}' exécuté ({len(results)} handler(s) invoqué(s)).")
        return 0
