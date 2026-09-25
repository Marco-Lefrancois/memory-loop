# -*- coding: utf-8 -*-
"""
src/commands/handlers/skill_eval.py — Handler CLI pour la commande skill-eval (MLOOP-244-FULL).
Exécute l'audit des compétences agentiques, le mode rapide --fast, le Flywheel et l'application HITL.
Conforme ADR-0202 (<= 300 lignes), ADR-0369 (Python Senior) et ADR-0389.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.cli import ZeroFluffConsole
from src.pipelines.skill_eval import SkillEvalEngine
from src.pipelines.skill_flywheel import SkillFlywheel
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.state import LoopState

logger = get_logger("commands.handlers.skill_eval")


def handle_skill_eval(
    args: argparse.Namespace,
    state: Optional[LoopState] = None,
    project_path: Optional[Path] = None,
) -> int:
    """Point d'entrée de la commande CLI 'mloop skill-eval'."""
    workspace_root = Path.cwd()
    target_skill = getattr(args, "skill", None)
    apply_patch_target = getattr(args, "apply_patch", None)
    run_flywheel_flag = getattr(args, "flywheel", False)
    as_json = getattr(args, "json", False)

    # 1. Action : Application formelle d'un patch HITL
    if apply_patch_target:
        flywheel = SkillFlywheel(workspace_root=workspace_root)
        patches_dir = flywheel.get_pending_patches_dir()
        patch_file = patches_dir / f"{apply_patch_target}_patch.md"

        if not patch_file.exists():
            ZeroFluffConsole.error(f"Aucun patch HITL en attente pour '{apply_patch_target}' ({patch_file}).")
            return 1

        # Confirmation interactive souveraine (HITL inviolable)
        is_batch = getattr(args, "batch", False)
        if not is_batch:
            resp = input(f"Confirmer l'application du patch pour '{apply_patch_target}' ? [y/N] : ").strip().lower()
            if resp not in ("y", "yes", "o", "oui"):
                ZeroFluffConsole.warning("Application du patch annulée par l'opérateur.")
                return 0

        res = flywheel.apply_pending_patch(apply_patch_target)
        if res.get("success"):
            ZeroFluffConsole.success(f"Patch HITL appliqué avec succès sur '{apply_patch_target}'.")
            return 0
        else:
            ZeroFluffConsole.error(f"Échec d'application du patch : {res.get('error')}")
            return 1

    # 2. Action : Évaluation unique ou globale
    engine = SkillEvalEngine(workspace_root=workspace_root)

    if target_skill:
        try:
            skill_res = engine.evaluate_with_golden_dataset(target_skill)
            summary = {
                "total_skills": 1,
                "average_score": skill_res.total_score,
                "pass_threshold": engine.pass_threshold,
                "passed": 1 if skill_res.verdict == "PASS" else 0,
                "warning": 1 if skill_res.verdict == "WARNING" else 0,
                "failed": 1 if skill_res.verdict == "FAIL" else 0,
                "results": [skill_res.to_dict()],
            }
        except FileNotFoundError as err:
            ZeroFluffConsole.error(str(err))
            return 1
    else:
        summary = engine.evaluate_all_skills()

    # Sauvegarde des rapports (uniquement lors d'un audit global)
    if not target_skill:
        try:
            engine.save_reports(summary)
        except Exception as exc:
            logger.warning(f"Avertissement lors de la sauvegarde des rapports : {exc}")

    # 3. Action optionnelle : Déclenchement du Flywheel
    flywheel_report = None
    if run_flywheel_flag:
        ZeroFluffConsole.section("Boucle d'Amélioration Fermée (Eval Flywheel)")
        flywheel = SkillFlywheel(workspace_root=workspace_root)
        flywheel_report = flywheel.run_flywheel(eval_summary=summary, target_skill=target_skill)
        ZeroFluffConsole.info(f"Flywheel achevé : {len(flywheel_report['proposals_generated'])} proposition(s) générée(s).")
        for prop in flywheel_report["proposals_generated"]:
            ZeroFluffConsole.success(f"  + Patch proposé pour {prop['skill']} (Δscore : +{prop['delta_score']} pts) -> {prop['patch_file']}")
        for n_rev in flywheel_report["needs_human_review"]:
            ZeroFluffConsole.warning(f"  ! Révision humaine requise pour {n_rev['skill']} (plafond d'itérations atteint)")

    # 4. Restitution
    if as_json:
        out = {"evaluation": summary}
        if flywheel_report:
            out["flywheel"] = flywheel_report
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        _display_cli_summary(summary)

    # Exit code strict (ADR-0389) : 0 si moyenne >= 80 et 0 FAIL, sinon 1
    is_healthy = summary.get("average_score", 0.0) >= 80.0 and summary.get("failed", 0) == 0
    return 0 if is_healthy else 1


def _display_cli_summary(summary: dict) -> None:
    """Affiche le tableau récapitulatif formaté sur la console ZeroFluff."""
    ZeroFluffConsole.section(f"Matrice d'Évaluation des Compétences Agentiques ({summary.get('total_skills', 0)} audités)")

    results = summary.get("results", [])
    for r in results:
        v = r.get("verdict", "FAIL")
        icon = "[PASS]" if v == "PASS" else ("[WARN]" if v == "WARNING" else "[FAIL]")
        score = r.get("total_score", 0.0)
        b = r.get("scores_breakdown", {})
        golden = b.get("golden_dataset")
        g_str = f"G:{golden:.1f}" if isinstance(golden, (int, float)) else "G:N/A"
        msg = f"{icon:<7} {r.get('skill_name'):<32} Score: {score:>5.1f}/100  (T:{b.get('trigger_clarity',0)} R:{b.get('rule_determinism',0)} A:{b.get('ground_truth_anchoring',0)} C:{b.get('resilience_and_confinement',0)} {g_str})"
        if v == "PASS":
            ZeroFluffConsole.success(msg)
        elif v == "WARNING":
            ZeroFluffConsole.warning(msg)
        else:
            ZeroFluffConsole.error(msg)

    ZeroFluffConsole.section(
        f"Bilan : Score Moyen {summary.get('average_score', 0.0)}/100 | "
        f"{summary.get('passed', 0)} PASS | {summary.get('warning', 0)} WARN | {summary.get('failed', 0)} FAIL"
    )
