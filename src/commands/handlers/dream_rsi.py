"""
src/commands/handlers/dream_rsi.py — Handler CLI Dream RSI (ADR-0372).

Commande CLI : dream-rsi
Exécute le cycle d'auto-amélioration récursive hors-ligne (Replay Simulator)
à coût d'inférence nul avec garantie formelle de non-régression.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from src.cli import ZeroFluffConsole
from src.pipelines.dream_rsi import (
    DreamExplorer,
    ModularHarnessIsolator,
    ReplaySimulator,
)

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

logger = logging.getLogger(__name__)


def handle_dream_rsi(args: argparse.Namespace, state: LoopState, project_path: Path) -> int:
    """Handler CLI pour la commande 'swarm.py dream-rsi'."""
    project_name = getattr(args, "project", None) or (state.project_name if state else "mLoop")
    target_path = project_path or (Path("Projects") / project_name if project_name else Path("."))

    # 1. Chargement des traces dans le Replay Simulator
    episodes = ReplaySimulator.load_from_project(target_path)
    ep_count = len(episodes)

    # 2. Diagnostic d'isolation du harnais
    diagnosis = ModularHarnessIsolator.analyze(episodes)

    # 3. Exploration méta-politique (garantie de non-régression vs pi_0)
    best_res, all_res = DreamExplorer.explore(episodes)
    gain = best_res.gain_vs_pi0

    # 4. Sauvegarde éventuelle de la politique (--apply)
    applied_path = None
    if getattr(args, "apply", False):
        mloop_dir = target_path / ".mloop"
        mloop_dir.mkdir(parents=True, exist_ok=True)
        policy_file = mloop_dir / "dream_policy.json"
        policy_data = {
            "policy_name": best_res.policy.name,
            "branching_factor": best_res.policy.branching_factor,
            "patience": best_res.policy.patience,
            "early_stopping_threshold": best_res.policy.early_stopping_threshold,
            "strategy": best_res.policy.strategy,
            "simulated_success_rate": best_res.simulated_success_rate,
            "gain_vs_pi0": gain,
            "harness_score": diagnosis.isolated_harness_score,
        }
        with open(policy_file, "w", encoding="utf-8") as f:
            json.dump(policy_data, f, indent=2, ensure_ascii=False)
        applied_path = policy_file.as_posix()

    # 5. Formatage JSON si demandé (sans pollution de bannières)
    if getattr(args, "json", False):
        summary: Dict[str, Any] = {
            "project_name": project_name,
            "episodes_simulated": ep_count,
            "harness_diagnosis": {
                "primary_bottleneck": diagnosis.primary_bottleneck,
                "distribution": diagnosis.distribution,
                "score": diagnosis.isolated_harness_score,
                "recommendations": diagnosis.recommendations,
            },
            "selected_policy": {
                "name": best_res.policy.name,
                "branching_factor": best_res.policy.branching_factor,
                "patience": best_res.policy.patience,
                "early_stopping_threshold": best_res.policy.early_stopping_threshold,
                "strategy": best_res.policy.strategy,
                "success_rate": best_res.simulated_success_rate,
                "gain_vs_pi0": gain,
            },
            "applied_file": applied_path,
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    ZeroFluffConsole.section(f"Dream RSI — Replay Simulator & Auto-Amélioration (ADR-0372) - {project_name}")

    # 6. Affichage console zéro-fluff
    ZeroFluffConsole.info(
        f"Simulateur de Replay : {ep_count} épisodes historiques évalués (coût d'inférence LLM nul)"
    )
    ZeroFluffConsole.info(
        f"Isolation Harnais : Goulot majeur [{diagnosis.primary_bottleneck}] (Score harnais: {diagnosis.isolated_harness_score}/100)"
    )
    dist_str = " | ".join(f"{k}: {v}%" for k, v in diagnosis.distribution.items())
    ZeroFluffConsole.info(f"Distribution des échecs : {dist_str}")

    if diagnosis.recommendations:
        ZeroFluffConsole.info("Recommandations d'optimisation du harnais :")
        for rec in diagnosis.recommendations:
            ZeroFluffConsole.info(f"  • {rec}")

    gain_str = f"+{gain:.1f}%" if gain > 0 else "0.0% (maintien pi_0 garanti)"
    ZeroFluffConsole.info(f"Méta-Politique Optimale Sélectionnée : [bold]{best_res.policy.name}[/bold]")
    ZeroFluffConsole.info(
        f"  • Paramètres : Branching={best_res.policy.branching_factor} | Patience={best_res.policy.patience} | Seuil Arrêt={best_res.policy.early_stopping_threshold} | Stratégie={best_res.policy.strategy}"
    )
    ZeroFluffConsole.info(
        f"  • Performance : Taux de succès={best_res.simulated_success_rate * 100:.1f}% | Gain vs pi_0 : [green]{gain_str}[/green]"
    )

    if applied_path:
        ZeroFluffConsole.success(f"Politique appliquée avec succès dans : {applied_path}")
    else:
        ZeroFluffConsole.info("Utilisez '--apply' pour persister la méta-politique dans la configuration du harnais.")

    ZeroFluffConsole.success("Cycle Dream RSI terminé avec succès.")
    return 0
