"""
Test de validation du 13e contrôle Vibe-Check : Interdiction de Saut de Phase
(ADR-0339 §3 — un agent opérant dans un projet sous statut T-SHIRT-SIZE a
l'interdiction formelle de rédiger des récits détaillés avant le passage
franchi de la Porte 1 / SOW). Ce check détecte les stories physiques rédigées
alors qu'aucun SOW (`docs/01-architecture/SOW_*.md`) n'a jamais été produit,
signe qu'une phase de cadrage macro a été sautée. Non-bloquant (WARNING) pour
ne pas casser les petits projets internes qui n'ont légitimement pas de SOW
(dérogation explicite via `phase_gate_exempt: true` dans sprint_backlog.md).
"""

from pathlib import Path
import shutil

from src.pipelines.vibe_check import run_vibe_check


def test_vibe_check_flags_phase_skip_when_stories_exist_without_sow():
    project_dir = Path("Projects") / "TestPhaseGateProj"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    try:
        (stories_dir / "US-01.md").write_text("# Récit détaillé\n", encoding="utf-8")

        result = run_vibe_check("TestPhaseGateProj")
        gate_checks = [c for c in result["checks"] if "Saut de Phase" in c["check"]]
        assert len(gate_checks) == 1
        assert gate_checks[0]["status"] == "FAIL"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_sow_exists_before_stories():
    project_dir = Path("Projects") / "TestPhaseGateProj2"
    arch_dir = project_dir / "docs" / "01-architecture"
    stories_dir = project_dir / "backlog" / "stories"
    arch_dir.mkdir(parents=True, exist_ok=True)
    stories_dir.mkdir(parents=True, exist_ok=True)

    try:
        (arch_dir / "SOW_TestPhaseGateProj2.md").write_text("# SOW\n", encoding="utf-8")
        (stories_dir / "US-01.md").write_text("# Récit détaillé\n", encoding="utf-8")

        result = run_vibe_check("TestPhaseGateProj2")
        gate_checks = [c for c in result["checks"] if "Saut de Phase" in c["check"]]
        assert len(gate_checks) == 1
        assert gate_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_explicit_exemption():
    project_dir = Path("Projects") / "TestPhaseGateProj3"
    stories_dir = project_dir / "backlog" / "stories"
    backlog_dir = project_dir / "backlog"
    stories_dir.mkdir(parents=True, exist_ok=True)

    try:
        (stories_dir / "US-01.md").write_text("# Récit détaillé\n", encoding="utf-8")
        (backlog_dir / "sprint_backlog.md").write_text(
            "---\nphase_gate_exempt: true\n---\n# Sprint Backlog\n", encoding="utf-8"
        )

        result = run_vibe_check("TestPhaseGateProj3")
        gate_checks = [c for c in result["checks"] if "Saut de Phase" in c["check"]]
        assert len(gate_checks) == 1
        assert gate_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_sprint_backlog_exists_without_explicit_flag():
    """
    ADR-0339 §3 : « L'en-tête de sprint_backlog.md doit obligatoirement déclarer
    la phase active du projet. » La simple EXISTENCE de sprint_backlog.md
    constitue déjà une preuve de gouvernance de phase tracée — suffisant pour
    exempter les projets établis (ex: BoireFrere_Segment2, 25+ stories déjà
    READY_FOR_DEV sans SOW jamais produit dans mLoop) sans exiger le flag
    explicite `phase_gate_exempt: true`.
    """
    project_dir = Path("Projects") / "TestPhaseGateProj5"
    stories_dir = project_dir / "backlog" / "stories"
    backlog_dir = project_dir / "backlog"
    stories_dir.mkdir(parents=True, exist_ok=True)

    try:
        (stories_dir / "US-01.md").write_text("# Récit détaillé\n", encoding="utf-8")
        (backlog_dir / "sprint_backlog.md").write_text(
            "# Sprint Backlog établi\n", encoding="utf-8"
        )

        result = run_vibe_check("TestPhaseGateProj5")
        gate_checks = [c for c in result["checks"] if "Saut de Phase" in c["check"]]
        assert len(gate_checks) == 1
        assert gate_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_no_stories_yet():
    project_dir = Path("Projects") / "TestPhaseGateProj4"
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_vibe_check("TestPhaseGateProj4")
        gate_checks = [c for c in result["checks"] if "Saut de Phase" in c["check"]]
        assert len(gate_checks) == 1
        assert gate_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
