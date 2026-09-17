"""
src/pipelines/dream_rsi/explorer.py — Explorateur Méta-Politique Dream RSI (ADR-0372).

Génère des variations de méta-politiques arborescentes et garantit une amélioration
strictement monotone en maintenant la politique courante pi_0 dans le vivier d'évaluation.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import logging
from typing import List, Optional, Tuple

from src.pipelines.dream_rsi.simulator import (
    PolicyParams,
    ReplayNode,
    ReplaySimulator,
    SimulationResult,
)

logger = logging.getLogger(__name__)


class DreamExplorer:
    """
    Explorateur d'auto-amélioration récursive (RSI) dans le simulateur de replay.
    """

    DEFAULT_BASELINE = PolicyParams(
        name="pi_0 (baseline)",
        branching_factor=1,
        patience=3,
        early_stopping_threshold=0.5,
        strategy="greedy",
    )

    @classmethod
    def generate_candidate_policies(
        cls, base_policy: Optional[PolicyParams] = None
    ) -> List[PolicyParams]:
        """
        Génère un vivier de méta-politiques candidates.
        Garantit l'inclusion systématique de pi_0 (théorème de monotonicité).
        """
        pi_0 = base_policy or cls.DEFAULT_BASELINE
        candidates: List[PolicyParams] = [pi_0]

        # Variations structurées de l'espace de recherche méta-politique
        branching_options = [1, 2, 3]
        patience_options = [2, 4, 5]
        threshold_options = [0.3, 0.6]

        idx = 1
        for b in branching_options:
            for p in patience_options:
                for th in threshold_options:
                    # Éviter de dupliquer exactement pi_0
                    if (
                        b == pi_0.branching_factor
                        and p == pi_0.patience
                        and th == pi_0.early_stopping_threshold
                    ):
                        continue

                    strat = "beam" if b > 1 else "greedy"
                    cand = PolicyParams(
                        name=f"pi_{idx} (b={b}, p={p}, th={th})",
                        branching_factor=b,
                        patience=p,
                        early_stopping_threshold=th,
                        strategy=strat,
                    )
                    candidates.append(cand)
                    idx += 1

                    # Vivier limité à 10 candidats pour sobriété de calcul
                    if len(candidates) >= 10:
                        return candidates

        return candidates

    @classmethod
    def evaluate_candidates(
        cls, episodes: List[List[ReplayNode]], candidates: List[PolicyParams]
    ) -> List[SimulationResult]:
        """Évalue chaque politique candidate sur les épisodes de replay."""
        results: List[SimulationResult] = []
        for policy in candidates:
            res = ReplaySimulator.simulate_policy(episodes, policy)
            results.append(res)
        return results

    @classmethod
    def calculate_score(cls, res: SimulationResult) -> float:
        """Score composite pondérant taux de succès et efficacité des coûts."""
        return (res.simulated_success_rate * 0.7) + (res.cost_efficiency_score * 0.3)

    @classmethod
    def explore(
        cls,
        episodes: List[List[ReplayNode]],
        base_policy: Optional[PolicyParams] = None,
    ) -> Tuple[SimulationResult, List[SimulationResult]]:
        """
        Exécute le cycle d'exploration Dream RSI.
        Retourne (best_result, all_results) avec garantie formelle de non-régression.
        """
        pi_0 = base_policy or cls.DEFAULT_BASELINE
        candidates = cls.generate_candidate_policies(pi_0)
        results = cls.evaluate_candidates(episodes, candidates)

        # Baseline pi_0 score
        pi_0_res = next((r for r in results if r.policy.name == pi_0.name), results[0])
        pi_0_score = cls.calculate_score(pi_0_res)

        # Recherche de la politique optimale
        best_res = pi_0_res
        best_score = pi_0_score

        for r in results:
            score = cls.calculate_score(r)
            if score > best_score:
                best_score = score
                best_res = r

        # Calcul du gain vs pi_0 garanti >= 0.0 (théorème de monotonicité)
        if pi_0_score >= 0.05:
            gain = max(0.0, ((best_score - pi_0_score) / pi_0_score) * 100.0)
        else:
            gain = max(0.0, (best_score - pi_0_score) * 100.0)

        best_res.gain_vs_pi0 = round(gain, 2)

        # Mettre à jour les gains pour tous les résultats pour reporting
        for r in results:
            r_score = cls.calculate_score(r)
            if pi_0_score >= 0.05:
                r_gain = ((r_score - pi_0_score) / pi_0_score) * 100.0
            else:
                r_gain = (r_score - pi_0_score) * 100.0
            r.gain_vs_pi0 = round(r_gain, 2)

        return best_res, results
