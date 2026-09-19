"""
Banc de tests déterministes pour les verrous bloquants de Gate 4 (MLOOP-092-BE / ADR-0383).
Vérifie les 5 contrôles stricts de ProjectLifecycleManager.approve_gate(gate_number=4) :
1. Présence et validité du rapport de certification QA (qa_certification_report.json).
2. 100% de tests pytest au vert.
3. Zéro violation de standards AST sur le code du sprint.
4. Triangulation CEL complète sur les 4 Piliers Gherkin.
5. Signature humaine obligatoire (rejet des bots/agents).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from src.core.lifecycle import (
    ProjectLifecycleManager,
    ProjectLifecycleStage,
    ProjectLifecycleState,
    GateApprovalRecord,
)


def _setup_stage4_project(base: Path) -> None:
    """Initialise un projet factice en STAGE_4_VALIDATE avec les gates 1, 2 et 3 approuvées."""
    mem_dir = base / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    state = ProjectLifecycleState(
        project_name=base.name,
        current_stage=ProjectLifecycleStage.STAGE_4_VALIDATE,
        gates={
            "1": GateApprovalRecord(gate_number=1, gate_name="Gate 1", approver="Architecte"),
            "2": GateApprovalRecord(gate_number=2, gate_name="Gate 2", approver="Architecte"),
            "3": GateApprovalRecord(gate_number=3, gate_name="Gate 3", approver="Marco"),
        },
    )
    ProjectLifecycleManager.save_state(base, state)


def _write_qa_report(base: Path, data: dict) -> None:
    mem_dir = base / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    (mem_dir / "qa_certification_report.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def test_gate4_rejects_missing_qa_report():
    """Contrôle 1 : Rejet si le rapport qa_certification_report.json est introuvable."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        _setup_stage4_project(base)

        with pytest.raises(ValueError, match="aucun rapport de certification QA"):
            ProjectLifecycleManager.approve_gate(
                project_path=base,
                gate_number=4,
                approver="Marco",
                notes="Recette QA",
            )


def test_gate4_rejects_failed_pytest():
    """Contrôle 2 : Rejet si le banc de tests comporte des échecs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        _setup_stage4_project(base)
        _write_qa_report(base, {
            "is_certified": False,
            "pytest_result": {"all_passed": False, "failed_tests": 2, "total_tests": 50},
            "ast_summary": {"passed": True, "total_violations": 0},
            "cel_result": {"is_complete": True, "missing_pillars": []},
        })

        with pytest.raises(ValueError, match="suite de tests comporte"):
            ProjectLifecycleManager.approve_gate(
                project_path=base,
                gate_number=4,
                approver="Marco",
            )


def test_gate4_rejects_ast_violations():
    """Contrôle 3 : Rejet si des violations de standards AST sont présentes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        _setup_stage4_project(base)
        _write_qa_report(base, {
            "is_certified": False,
            "pytest_result": {"all_passed": True, "failed_tests": 0, "total_tests": 50},
            "ast_summary": {"passed": False, "total_violations": 3, "violations": [{"rule_id": "RULE-AST-01"}]},
            "cel_result": {"is_complete": True, "missing_pillars": []},
        })

        with pytest.raises(ValueError, match="violations de standards AST"):
            ProjectLifecycleManager.approve_gate(
                project_path=base,
                gate_number=4,
                approver="Marco",
            )


def test_gate4_rejects_incomplete_cel():
    """Contrôle 4 : Rejet si le Code Evidence Ledger présente des piliers manquants."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        _setup_stage4_project(base)
        _write_qa_report(base, {
            "is_certified": False,
            "pytest_result": {"all_passed": True, "failed_tests": 0, "total_tests": 50},
            "ast_summary": {"passed": True, "total_violations": 0},
            "cel_result": {"is_complete": False, "missing_pillars": ["PILIER_3_RESILIENCE_MODE_DEGRADE"]},
        })

        with pytest.raises(ValueError, match="Code Evidence Ledger présente des angles morts"):
            ProjectLifecycleManager.approve_gate(
                project_path=base,
                gate_number=4,
                approver="Marco",
            )


def test_gate4_rejects_bot_approver():
    """Contrôle 5 : Rejet si la signature provient d'un bot ou sous-agent IA."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        _setup_stage4_project(base)
        _write_qa_report(base, {
            "is_certified": True,
            "pytest_result": {"all_passed": True, "failed_tests": 0, "total_tests": 50},
            "ast_summary": {"passed": True, "total_violations": 0},
            "cel_result": {"is_complete": True, "missing_pillars": []},
        })

        for bot_name in ("sentinel", "ai", "bot", "subagent", "swarm"):
            with pytest.raises(ValueError, match="signature humaine formelle"):
                ProjectLifecycleManager.approve_gate(
                    project_path=base,
                    gate_number=4,
                    approver=bot_name,
                )


def test_gate4_nominal_human_approval_succeeds():
    """Chemin nominal : Tous les contrôles sont au vert et un humain valide signe."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        _setup_stage4_project(base)
        _write_qa_report(base, {
            "is_certified": True,
            "pytest_result": {"all_passed": True, "failed_tests": 0, "total_tests": 50},
            "ast_summary": {"passed": True, "total_violations": 0},
            "cel_result": {"is_complete": True, "missing_pillars": []},
        })

        new_state = ProjectLifecycleManager.approve_gate(
            project_path=base,
            gate_number=4,
            approver="Marco & Lead Architect",
            notes="Audit QA validé avec succès",
        )

        assert new_state.current_stage == ProjectLifecycleStage.STAGE_5_SHIP
        assert "4" in new_state.gates
        assert new_state.gates["4"].approver == "Marco & Lead Architect"
