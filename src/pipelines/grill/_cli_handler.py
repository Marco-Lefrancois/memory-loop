"""
CLI Handler for Grill Commands (ADR-0320 / ADR-0389 / MLOOP-290-BE).
Orchestration CLI du Grilling mLoop v2 (Rounds, Modes Asymétriques & Context Health).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole
from src.pipelines.grill._frontier import check_context_health
from src.pipelines.grill._handoff import stage_prototype
from src.utils.logger import get_logger

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

logger = get_logger("grill.cli_handler")


def inspect_session_health(project_path: Path) -> int:
    """Affiche l'état de santé du contexte de session CLI sans appel externe."""
    health_file = project_path / "memory" / "SESSION_MEMORY_HEALTH.md"
    health_info = check_context_health(transcript_path=health_file)

    ZeroFluffConsole.info(f"📊 Santé du Contexte de Session — {health_info['zone']}")
    ZeroFluffConsole.info(f"   • Tokens estimés : ~{health_info['tokens']} / Seuil : {health_info['threshold']}")
    ZeroFluffConsole.info(f"   • Statut         : {health_info['status']}")
    ZeroFluffConsole.info(f"   • Directive      : {health_info['message']}")

    if health_info["status"] == "CRITICAL":
        ZeroFluffConsole.warning("⚠️ Attention : Dumb Zone atteinte. Ne pas purger la mémoire ; basculer en rédaction.")
    elif health_info["status"] == "WARNING":
        ZeroFluffConsole.warning("⚠️ Avertissement : fatigue cognitive imminente. Envisager un checkpoint.")
    else:
        ZeroFluffConsole.success("✅ Fenêtre de contexte optimale (Smart Zone).")

    return 0


def execute_grill_cli(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Point d'entrée principal pour les commandes 'grill' et 'grill-project'."""
    from src.pipelines.grill._engine import GrillEngine
    from src.pipelines.sync import run_sync

    # 1. Inspection rapide de santé si demandé
    if getattr(args, "health", False):
        return inspect_session_health(project_path)

    ge = GrillEngine(project_path)
    story_id = getattr(args, "story", None)
    is_macro = story_id is None

    # 2. Détermination du mode asymétrique (ADR-013 / ADR-0389)
    # grill-project -> round par défaut ; grill-me --story -> atomic par défaut
    raw_mode = getattr(args, "mode", None)
    if raw_mode:
        mode = raw_mode.lower().strip()
    else:
        mode = "round" if is_macro else "atomic"

    # 3. Contrôle préventif de santé de contexte
    health_file = project_path / "memory" / "SESSION_MEMORY_HEALTH.md"
    health = check_context_health(transcript_path=health_file)
    if health["alert"]:
        ZeroFluffConsole.warning(f"⚠️ [CONTEXT HEALTH {health['zone']}] {health['message']}")

    # 4. Annonce de session
    if is_macro:
        mode_label = "Frontier Rounds" if mode == "round" else "1:1 Atomic"
        ZeroFluffConsole.info(
            f"[GRILL-ME MACRO ({mode_label})] Cadrage transverse du projet '{args.project}'."
        )
    else:
        ZeroFluffConsole.info(
            f"[GRILL-ME MICRO 1:1 ({mode.upper()})] Entretien contradictoire chirurgical sur le récit '{story_id}'."
        )

    # 5. Recherche documentaire FTS5 si terme fourni
    search_term = (
        getattr(args, "query", None)
        or getattr(args, "title", None)
        or story_id
    )
    if search_term and search_term != "Décision d'Architecture":
        ge.perform_fact_search(str(search_term))

    # 6. Génération conditionnelle d'ADR
    ctx = getattr(args, "context", None)
    dec = getattr(args, "decision", None)
    if ctx or dec:
        adr_path = ge.record_adr(
            title=getattr(args, "title", None) or "Décision d'Architecture",
            context=ctx or "Contexte issu d'une session de grilling interactive.",
            decision=dec or "Décision arbitrée conjointement.",
            positives=getattr(args, "positives", None)
            or "Clarification du domaine et réduction de l'ambiguïté.",
            negatives=getattr(args, "negatives", None)
            or "Obligation d'alignement strict.",
        )
        ZeroFluffConsole.success(f"ADR généré avec succès : {adr_path}")
    else:
        ZeroFluffConsole.info(
            "Aucun contenu de décision (--context/--decision) fourni : cadrage sans génération d'ADR."
        )

    # 7. Marquage story
    if story_id:
        if ge.mark_story_grilled(story_id):
            ZeroFluffConsole.success(
                f"Récit {story_id} qualifié avec succès via Grill-Me Micro 1:1."
            )
        else:
            ZeroFluffConsole.warning(
                f"Récit {story_id} introuvable dans backlog/stories ou sprint_backlog.md."
            )

    # 8. Synchronisation canonique
    run_sync(args.project, state, project_path)
    return 0
