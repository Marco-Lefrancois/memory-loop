"""
Handler CLI : multi-draft — Exécute le challenge d'évaluation locale multi-branches (ADR-0373).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.pipelines.multi_draft import MultiDraftChallengeEngine

if TYPE_CHECKING:
    from src.state import LoopState


def handle_multi_draft(
    args: argparse.Namespace, state: LoopState, project_path: Path
) -> int:
    """Point d'entrée CLI pour swarm.py multi-draft."""
    story_id = getattr(args, "story", None)
    if not story_id:
        ZeroFluffConsole.error("L'argument --story <STORY_ID> est obligatoire pour multi-draft.")
        return 2

    strict = getattr(args, "strict", True)
    eval_only = getattr(args, "eval_only", False)

    ZeroFluffConsole.step_s2(
        "Challenge Engine",
        f"Lancement du challenge multi-drafts pour {story_id} sur {args.project}..."
    )

    engine = MultiDraftChallengeEngine(project_path, story_id)
    drafts = engine.discover_drafts()

    if not drafts:
        ZeroFluffConsole.error(
            f"Aucun brouillon trouvé sous memory/drafts/{story_id}/.\n"
            f"Créez d'abord au moins 2 fichiers (ex: draft_A_*.md, draft_B_*.md) conformément à l'ADR-0373."
        )
        return 1

    if len(drafts) < 2:
        ZeroFluffConsole.error(
            f"Seulement {len(drafts)} draft trouvé sous memory/drafts/{story_id}/.\n"
            f"Règle ADR-0373 : Au moins 2 drafts physiques sont requis pour arbitrage."
        )
        return 1

    ZeroFluffConsole.info(f"Découverte de {len(drafts)} branches candidates :")
    for df in drafts:
        ZeroFluffConsole.info(f"  📄 {df.name}")

    report = engine.run_challenge(strict=strict)

    ZeroFluffConsole.section(f"RÉSULTATS DU MULTI-DRAFT CHALLENGE — {story_id}")
    for r in report.results:
        sc_status = "✅ CONFORME" if r.struct_check_passed else f"❌ {len(r.struct_violations)} VIOLATIONS"
        if r.rubber_duck_status == "APPROVED":
            rd_status = "✅ APPROUVÉ"
        elif r.rubber_duck_status == "ACTION_REQUIRED":
            rd_status = f"⚠️  ACTION ({len(r.silent_failures)} warns)"
        else:
            rd_status = f"❌ REJETÉ ({len(r.critical_flaws)} critiques)"
        ZeroFluffConsole.info(
            f"  • {r.file_name:<35} | Struct: {sc_status:<16} | Sentinel: {rd_status:<22} | Trust: {r.trust_score:>5.1f}/100"
        )

    if report.best_draft:
        ZeroFluffConsole.success(
            f"🏆 Meilleure branche Pareto : {report.best_draft} avec un score de {report.best_trust_score:.1f}/100"
        )
        ZeroFluffConsole.info(
            f"Matrice complète sauvegardée sous : memory/drafts/{story_id}/challenge_matrix.json\n"
            f"Rapport comparatif sauvegardé sous : memory/drafts/{story_id}/challenge_report.md"
        )

    return 0 if report.status == "SUCCESS" else 1

