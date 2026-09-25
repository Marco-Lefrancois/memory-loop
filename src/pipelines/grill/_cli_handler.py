"""
CLI Handler for Grill Commands (ADR-0320 / ADR-0389 / MLOOP-290-BE).
Orchestration CLI du Grilling mLoop v2 (Rounds, Modes Asymétriques & Context Health).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.pipelines._fsm_authority import LifecycleAuthorityError
from src.pipelines.grill._frontier import check_context_health
from src.pipelines.grill._grill_guards import (
    assert_no_story_mutation,
    log_lifecycle_violation,
)
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
    ZeroFluffConsole.info(
        f"   • Tokens estimés : ~{health_info['tokens']} / Seuil : {health_info['threshold']}"
    )
    ZeroFluffConsole.info(f"   • Statut         : {health_info['status']}")
    ZeroFluffConsole.info(f"   • Directive      : {health_info['message']}")

    if health_info["status"] == "CRITICAL":
        ZeroFluffConsole.warning(
            "⚠️ Attention : Dumb Zone atteinte. Ne pas purger la mémoire ; basculer en rédaction."
        )
    elif health_info["status"] == "WARNING":
        ZeroFluffConsole.warning(
            "⚠️ Avertissement : fatigue cognitive imminente. Envisager un checkpoint."
        )
    else:
        ZeroFluffConsole.success("✅ Fenêtre de contexte optimale (Smart Zone).")

    return 0


_VALID_FORMATS = frozenset({"round", "atomic"})
_VALID_SCOPES = frozenset({"STORY", "EPIC", "PROJECT"})


def _resolve_format(raw_format: str | None, raw_mode: str | None, is_macro: bool) -> str:
    """
    Résout le format d'interrogation (round | atomic) selon ADR-0393.

    Primauté déterministe : `--format` prime sur `--mode` en cas de coexistence.
    Défaut asymétrique : `round` en macro (transverse), `atomic` en micro (1:1).
    Une valeur inconnue déclenche un message explicite et un repli sur le défaut.
    """
    default = "round" if is_macro else "atomic"

    fmt = (raw_format or "").strip().lower()
    mode = (raw_mode or "").strip().lower()

    # Notification d'alignement si les deux axes sont fournis (RM primauté).
    if fmt and mode and fmt != mode:
        ZeroFluffConsole.info(
            f"[MATRICE] --format ({fmt}) prime sur --mode ({mode}) : "
            "alignement déterministe sur --format (ADR-0393)."
        )

    chosen = fmt or mode
    if not chosen:
        return default
    if chosen not in _VALID_FORMATS:
        ZeroFluffConsole.warning(
            f"⚠️ Valeur de format inconnue « {chosen} » : utilisez 'round' ou "
            f"'atomic'. Repli sur le format par défaut « {default} »."
        )
        return default
    return chosen


def _resolve_scope(raw_scope: str | None, is_macro: bool) -> str:
    """
    Résout le périmètre d'analyse (STORY | EPIC | PROJECT) selon ADR-0393.

    Le flag `--scope` explicite prime ; sinon défaut = PROJECT en macro, STORY
    en micro. Une valeur inconnue déclenche un message explicite et un repli.
    """
    default = "PROJECT" if is_macro else "STORY"
    scope = (raw_scope or "").strip().upper()
    if not scope:
        return default
    if scope not in _VALID_SCOPES:
        ZeroFluffConsole.warning(
            f"⚠️ Valeur de scope inconnue « {scope} » : utilisez 'story', 'epic' "
            f"ou 'project'. Repli sur le scope par défaut « {default} »."
        )
        return default
    return scope


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

    # Résolution du scope (ADR-0393 / MLOOP-322-BE) : un grill sans --story
    # (grill-project ou grill macro) est transverse et interdit toute mutation
    # de récit. Le flag --scope explicite prime s'il est fourni. La sélection du
    # scope n'altère JAMAIS le format d'interrogation (orthogonalité ADR-0393).
    scope = _resolve_scope(getattr(args, "scope", None), is_macro)

    # 2. Détermination du format asymétrique (ADR-013 / ADR-0389 / ADR-0393).
    # Axe Format orthogonal à l'axe Scope. Primauté déterministe de --format sur
    # --mode : si les deux sont fournis, --format prévaut et l'alignement est notifié.
    mode = _resolve_format(getattr(args, "format", None), getattr(args, "mode", None), is_macro)

    # Transparence d'affichage (ADR-0393) : couple matrice actif Format × Scope.
    ZeroFluffConsole.info(f"[GRILL MATRICE] Format: {mode.upper()} | Scope: {scope}")

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
    search_term = getattr(args, "query", None) or getattr(args, "title", None) or story_id
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
            negatives=getattr(args, "negatives", None) or "Obligation d'alignement strict.",
        )
        ZeroFluffConsole.success(f"ADR généré avec succès : {adr_path}")
    else:
        ZeroFluffConsole.info(
            "Aucun contenu de décision (--context/--decision) fourni : cadrage sans génération d'ADR."
        )

    # 7. Marquage story — sous barrière d'étanchéité de scope transverse.
    #    En scope EPIC/PROJECT, toute mutation de backlog/stories/ est interdite
    #    et lève LifecycleAuthorityError (Fail-Closed, code de sortie 1).
    try:
        with assert_no_story_mutation(scope, ge.stories_dir):
            if story_id:
                if ge.mark_story_grilled(story_id):
                    ZeroFluffConsole.success(
                        f"Récit {story_id} qualifié avec succès via Grill-Me Micro 1:1."
                    )
                else:
                    ZeroFluffConsole.warning(
                        f"Récit {story_id} introuvable dans backlog/stories ou sprint_backlog.md."
                    )
    except LifecycleAuthorityError as exc:
        log_lifecycle_violation(project_path, story_id, str(exc), scope)
        logger.error(
            "Infraction d'autorité de cycle de vie interceptée (grill)",
            extra={
                "component": "grill.cli_handler",
                "operation": "execute_grill_cli",
                "story_id": story_id or "",
                "violation": str(exc),
                "scope": scope,
            },
        )
        ZeroFluffConsole.error(str(exc))
        return 1

    # 8. Synchronisation canonique
    run_sync(args.project, state, project_path)
    return 0
