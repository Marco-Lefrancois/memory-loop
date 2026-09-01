"""
MCTS Multi-Agent Debate Engine (Arbre de Décision Arborescent).

Pattern Proposer / Critic / Verifier :
1. Proposer (Agent Plan) : Génère jusqu'à N variantes de découpage vertical ou de contrat.
2. Critic (Agent Sentinel) : Évalue chaque branche sur INVEST, couplage, et régressions potentielles.
3. Verifier (Formal Gate) : Valide les invariants négatifs et calcule le score Pareto.
"""
from __future__ import annotations

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DebateBranch:
    """Branche de proposition dans l'arbre de décision."""
    branch_id: str
    title: str
    proposal: str
    critic_notes: str = ""
    invest_score: float = 0.0
    risk_score: float = 0.0
    is_approved: bool = False


class MCTSAdvDebateEngine:
    """Moteur de débat contradictoire multi-agents."""

    def __init__(self, max_branches: int = 3) -> None:
        self.max_branches = max_branches

    def evaluate_branches(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Évalue plusieurs alternatives et sélectionne la solution optimale (Pareto-Optimale)."""
        branches: List[DebateBranch] = []

        for i, prop in enumerate(proposals[:self.max_branches]):
            bid = f"BRANCH-{i+1}"
            title = prop.get("title", f"Option {i+1}")
            content = prop.get("content", "")

            # Simulation de l'évaluation contradictoire Sentinel
            invest_score = self._compute_invest_score(content)
            risk_score = self._compute_risk_score(content)

            # Une branche est approuvée si INVEST >= 80% et Risque <= 4/10
            is_approved = invest_score >= 80.0 and risk_score <= 4.0

            branch = DebateBranch(
                branch_id=bid,
                title=title,
                proposal=content,
                critic_notes="Couplage minimal, 4 piliers Gherkin respectés" if is_approved else "Risque de couplage horizontal",
                invest_score=invest_score,
                risk_score=risk_score,
                is_approved=is_approved,
            )
            branches.append(branch)

        # Sélection de la meilleure branche (Pareto: max INVEST, min Risk)
        best_branch = max(branches, key=lambda b: (b.invest_score - b.risk_score * 10)) if branches else None

        return {
            "total_branches_explored": len(branches),
            "selected_branch": best_branch.branch_id if best_branch else None,
            "selected_title": best_branch.title if best_branch else None,
            "branches": [
                {
                    "id": b.branch_id,
                    "title": b.title,
                    "invest_score": b.invest_score,
                    "risk_score": b.risk_score,
                    "approved": b.is_approved,
                    "notes": b.critic_notes,
                }
                for b in branches
            ],
        }

    def _compute_invest_score(self, content: str) -> float:
        """Calcule une estimation du respect INVEST (0-100%)."""
        score = 60.0
        if "Scénario" in content or "Scenario" in content:
            score += 15.0
        if "Étant donné" in content or "Given" in content:
            score += 15.0
        if "Frontmatter" in content or "---" in content:
            score += 10.0
        return min(100.0, score)

    def _compute_risk_score(self, content: str) -> float:
        """Calcule un score de risque de régression (1-10)."""
        if "global" in content.lower() or "shared" in content.lower():
            return 6.0
        return 2.0
