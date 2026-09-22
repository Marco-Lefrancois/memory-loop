"""
src/pipelines/dream_rsi/simulator.py — Replay Simulator Hors-Ligne (ADR-0372).

Simule l'évaluation de méta-politiques d'exploration arborescente sur des traces
d'exécution et événements historiques sans aucun appel LLM en ligne (coût d'inférence nul).
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PolicyParams:
    """Paramètres d'une méta-politique d'exploration arborescente."""
    name: str = "baseline_pi0"
    branching_factor: int = 1
    patience: int = 3
    early_stopping_threshold: float = 0.5
    strategy: str = "greedy"  # "greedy", "beam", "uct"


@dataclass
class ReplayNode:
    """Nœud d'exécution dans l'arbre ou la séquence de replay."""
    node_id: str
    parent_id: Optional[str] = None
    step_index: int = 0
    action_type: str = "unknown"
    command_or_tool: str = ""
    status: str = "success"  # "success", "failure", "timeout"
    cost_tokens: int = 0
    reward: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """Résultats d'évaluation d'une politique par le Replay Simulator."""
    policy: PolicyParams
    simulated_success_rate: float
    total_episodes: int
    avg_steps: float
    total_reward: float
    cost_efficiency_score: float
    gain_vs_pi0: float = 0.0


class ReplaySimulator:
    """
    Simulateur de replay hors-ligne (ADR-0372).
    Évalue des méta-politiques d'exploration sur des arbres de traces historiques.
    """

    @classmethod
    def load_from_traces(cls, traces: List[Dict[str, Any]]) -> List[List[ReplayNode]]:
        """Convertit une liste de traces brutes en épisodes de nœuds de replay."""
        episodes: List[List[ReplayNode]] = []
        current_episode: List[ReplayNode] = []

        for idx, tr in enumerate(traces):
            node_id = str(tr.get("trace_id") or f"node_{idx}")
            event_type = str(tr.get("event_type") or tr.get("type") or "step")
            val_res = tr.get("validation_result") or {}
            critique = tr.get("rubber_duck_critique") or {}

            # Calcul du statut et de la récompense
            is_rejected = critique.get("status") == "REJECTED" or val_res.get("wikifix_passed") is False
            has_error = bool(val_res.get("error_code"))
            status = "failure" if (is_rejected or has_error) else "success"
            reward = 1.0 if status == "success" else -0.5

            node = ReplayNode(
                node_id=node_id,
                step_index=len(current_episode),
                action_type=event_type,
                command_or_tool=str(tr.get("agent_role") or tr.get("agent") or "worker"),
                status=status,
                cost_tokens=int(tr.get("cost_tokens") or 150),
                reward=reward,
                metadata={"blocking_issues": critique.get("blocking_issues") or []},
            )
            current_episode.append(node)

            # Délimitation d'épisode: fin naturelle ou lot de 8 étapes
            if status == "success" or len(current_episode) >= 8:
                episodes.append(current_episode)
                current_episode = []

        if current_episode:
            episodes.append(current_episode)

        return episodes

    @classmethod
    def load_from_project(cls, project_path: Path) -> List[List[ReplayNode]]:
        """Charge les traces historiques depuis le stockage mémoire du projet."""
        traces_file = project_path / "memory" / "execution_traces.json"
        events_file = project_path / "memory" / "events.jsonl"
        traces: List[Dict[str, Any]] = []

        if traces_file.exists():
            try:
                with open(traces_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        traces.extend(data)
            except Exception as e:
                logger.debug(
                    "Échec de lecture de execution_traces.json",
                    exc_info=True,
                    extra={"path": traces_file.as_posix(), "error": str(e)},
                )

        if not traces and events_file.exists():
            try:
                with open(events_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                traces.append(json.loads(line))
                            except json.JSONDecodeError as e:
                                logger.debug(
                                    "Événement JSON illisible dans events.jsonl ignoré",
                                    exc_info=True,
                                    extra={
                                        "component": "pipelines.dream_rsi.simulator",
                                        "operation": "load_events",
                                        "error": str(e),
                                    },
                                )
            except Exception as e:
                logger.debug(
                    "Échec de lecture de events.jsonl",
                    exc_info=True,
                    extra={"path": events_file.as_posix(), "error": str(e)},
                )

        if not traces:
            return cls._generate_synthetic_episodes()

        return cls.load_from_traces(traces)

    @classmethod
    def _generate_synthetic_episodes(cls) -> List[List[ReplayNode]]:
        """Génère des épisodes synthétiques déterministes si aucune trace n'existe."""
        episodes: List[List[ReplayNode]] = []
        for ep_idx in range(5):
            episode: List[ReplayNode] = []
            for step in range(4):
                status = "success" if step >= 2 else ("failure" if step == 1 else "success")
                episode.append(
                    ReplayNode(
                        node_id=f"syn_ep{ep_idx}_step{step}",
                        step_index=step,
                        action_type="synthetic_step",
                        status=status,
                        reward=1.0 if status == "success" else -0.5,
                        cost_tokens=100,
                    )
                )
            episodes.append(episode)
        return episodes

    @classmethod
    def simulate_policy(
        cls, episodes: List[List[ReplayNode]], policy: PolicyParams
    ) -> SimulationResult:
        """
        Simule l'exécution de la méta-politique sur la forêt d'épisodes de replay.
        Applique patience, seuil d'arrêt précoce et facteur d'arborescence.
        """
        if not episodes:
            return SimulationResult(
                policy=policy,
                simulated_success_rate=0.0,
                total_episodes=0,
                avg_steps=0.0,
                total_reward=0.0,
                cost_efficiency_score=0.0,
            )

        successful_episodes = 0
        total_steps_taken = 0
        total_cumulative_reward = 0.0

        for episode in episodes:
            consecutive_failures = 0
            ep_reward = 0.0
            ep_success = False
            steps_in_ep = 0

            for idx, node in enumerate(episode):
                steps_in_ep += policy.branching_factor
                total_steps_taken += policy.branching_factor

                effective_status = node.status
                if effective_status == "failure" and policy.branching_factor > 1:
                    recovery_prob = 0.4 * (policy.branching_factor - 1)
                    if (idx * 7 + policy.branching_factor) % 10 < int(recovery_prob * 10):
                        effective_status = "success"

                if effective_status == "success":
                    consecutive_failures = 0
                    ep_reward += 1.0
                    ep_success = True
                else:
                    consecutive_failures += 1
                    ep_reward -= 0.5

                if consecutive_failures >= policy.patience:
                    break

                if idx >= 2:
                    current_ratio = ep_reward / max(1, steps_in_ep)
                    if current_ratio < -policy.early_stopping_threshold:
                        break

            total_cumulative_reward += ep_reward
            if ep_success:
                successful_episodes += 1

        total_ep_count = len(episodes)
        success_rate = successful_episodes / total_ep_count
        avg_steps = total_steps_taken / total_ep_count
        # Normalisation du rendement moyen par étape dans [0.0, 1.0]
        step_efficiency = (total_cumulative_reward / max(1, total_steps_taken) + 0.5) / 1.5
        efficiency = max(0.0, min(1.0, (step_efficiency * 0.5) + (success_rate * 0.5)))

        return SimulationResult(
            policy=policy,
            simulated_success_rate=round(success_rate, 4),
            total_episodes=total_ep_count,
            avg_steps=round(avg_steps, 2),
            total_reward=round(total_cumulative_reward, 2),
            cost_efficiency_score=round(efficiency, 4),
        )
