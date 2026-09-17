"""
tests/test_dream_rsi.py — Tests Unitaires & d'Intégration Dream RSI (ADR-0372).

Valide le simulateur de replay hors-ligne, l'isolation modulaire du harnais,
l'explorateur méta-politique et le théorème de monotonicité (non-régression).
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import argparse
import json
from pathlib import Path
import pytest

from src.commands.handlers.dream_rsi import handle_dream_rsi
from src.pipelines.base import PipelineStage
from src.pipelines.dream_rsi import (
    DreamExplorer,
    DreamRSIStage,
    HarnessFailureCategory,
    ModularHarnessIsolator,
    PolicyParams,
    ReplayNode,
    ReplaySimulator,
)
from src.state import LoopState


def test_replay_simulator_empty():
    """Vérifie le comportement avec une liste vide d'épisodes."""
    res = ReplaySimulator.simulate_policy([], PolicyParams())
    assert res.total_episodes == 0
    assert res.simulated_success_rate == 0.0
    assert res.cost_efficiency_score == 0.0


def test_replay_simulator_synthetic_fallback(tmp_path: Path):
    """Vérifie le fallback synthétique si aucun fichier de traces n'existe."""
    empty_proj = tmp_path / "empty_proj"
    empty_proj.mkdir()
    episodes = ReplaySimulator.load_from_project(empty_proj)
    assert len(episodes) > 0
    res = ReplaySimulator.simulate_policy(episodes, PolicyParams())
    assert res.total_episodes == len(episodes)
    assert res.simulated_success_rate >= 0.0


def test_replay_simulator_branching_and_patience():
    """Vérifie que branching_factor > 1 améliore la résilience face aux pannes."""
    # Épisode avec 2 échecs puis un succès
    episodes = [
        [
            ReplayNode(node_id="n1", status="failure", reward=-0.5),
            ReplayNode(node_id="n2", status="failure", reward=-0.5),
            ReplayNode(node_id="n3", status="success", reward=1.0),
        ]
    ]

    # Politique stricte (patience=1) : abandonne dès le premier échec
    p_strict = PolicyParams(name="strict", branching_factor=1, patience=1)
    res_strict = ReplaySimulator.simulate_policy(episodes, p_strict)
    assert res_strict.simulated_success_rate == 0.0

    # Politique patiente (patience=3) : atteint le nœud de succès
    p_patient = PolicyParams(name="patient", branching_factor=1, patience=3)
    res_patient = ReplaySimulator.simulate_policy(episodes, p_patient)
    assert res_patient.simulated_success_rate == 1.0


@pytest.mark.parametrize(
    "issue_text,expected_category",
    [
        ("Context length exceeded in token buffer", HarnessFailureCategory.MEMORY),
        ("Hygiene breach in memory health log", HarnessFailureCategory.MEMORY),
        ("Tool execution timeout on git status", HarnessFailureCategory.TOOLING),
        ("AttributeError: NoneType object has no attribute run", HarnessFailureCategory.TOOLING),
        ("INVEST Gherkin 4-Piliers rejected by Sentinel", HarnessFailureCategory.GATE),
        ("Validation gate error code ERR_WIKIFIX", HarnessFailureCategory.GATE),
        ("Instruction drift and unexpected format output", HarnessFailureCategory.PROMPT),
        ("Unknown strange anomaly", HarnessFailureCategory.GATE),  # Fallback
    ],
)
def test_modular_harness_categorization(issue_text: str, expected_category: HarnessFailureCategory):
    """Vérifie la classification déterministe des défaillances du harnais."""
    cat = ModularHarnessIsolator.categorize_issue(issue_text)
    assert cat == expected_category


def test_modular_harness_nominal():
    """Vérifie le diagnostic quand aucun échec n'est enregistré."""
    diagnosis = ModularHarnessIsolator.analyze([])
    assert diagnosis.total_failures == 0
    assert diagnosis.primary_bottleneck == "None"
    assert diagnosis.isolated_harness_score == 95


def test_dream_explorer_monotonicity():
    """Théorème de monotonicité : la politique optimale bat ou égale systématiquement pi_0."""
    episodes = ReplaySimulator._generate_synthetic_episodes()
    pi_0 = PolicyParams(name="pi_0 (baseline)", branching_factor=1, patience=2)

    best_res, all_res = DreamExplorer.explore(episodes, base_policy=pi_0)

    # pi_0 doit être dans le vivier
    pi_0_res = next(r for r in all_res if r.policy.name == pi_0.name)
    pi_0_score = DreamExplorer.calculate_score(pi_0_res)
    best_score = DreamExplorer.calculate_score(best_res)

    assert best_score >= pi_0_score
    assert best_res.gain_vs_pi0 >= 0.0


def test_dream_rsi_stage_composition(tmp_path: Path):
    """Vérifie l'exécution d'un pipeline composable avec l'étape DreamRSIStage."""
    state = LoopState(project_name="TestProj")
    proj_dir = tmp_path / "TestProj"
    proj_dir.mkdir(parents=True, exist_ok=True)

    class MockPreStage(PipelineStage):
        def execute(self, st: LoopState) -> LoopState:
            return st

    stage = DreamRSIStage(project_path=proj_dir)
    pipeline = MockPreStage() | stage
    final_state = pipeline(state)

    assert stage.last_result is not None
    info = stage.last_result
    assert "best_policy" in info
    assert "gain_vs_pi0" in info
    assert info["gain_vs_pi0"] >= 0.0
    assert len(final_state.journal) > 0


def test_handle_dream_rsi_cli(tmp_path: Path, capsys):
    """Vérifie les options CLI (--simulate, --json, --apply)."""
    proj_dir = tmp_path / "cli_test_proj"
    proj_dir.mkdir(parents=True)
    state = LoopState(project_name="cli_test_proj")

    # 1. Test simulation JSON
    args_json = argparse.Namespace(project="cli_test_proj", simulate=True, apply=False, json=True)
    ret_json = handle_dream_rsi(args_json, state, proj_dir)
    assert ret_json == 0
    captured = capsys.readouterr()
    # Le flux de sortie JSON est pur
    payload = json.loads(captured.out.strip())
    assert payload["project_name"] == "cli_test_proj"
    assert "selected_policy" in payload

    # 2. Test apply
    args_apply = argparse.Namespace(project="cli_test_proj", simulate=False, apply=True, json=False)
    ret_apply = handle_dream_rsi(args_apply, state, proj_dir)
    assert ret_apply == 0
    policy_file = proj_dir / ".mloop" / "dream_policy.json"
    assert policy_file.exists()
    saved = json.loads(policy_file.read_text(encoding="utf-8"))
    assert "policy_name" in saved
