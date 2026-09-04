"""
Test de validation du 12e contrôle Vibe-Check : Granularité SOW (ADR-0331 §2.2
Règle #3 — Interdiction Formelle des Libellés Génériques). Un SOW généré sous
docs/01-architecture/SOW_*.md contenant des libellés vagues (« [Détail des
récits] », « Composant générique », « Développement divers ») doit déclencher
un WARNING (non-bloquant, cohérent avec la sévérité des autres checks récents).
"""

from pathlib import Path
import shutil

from src.pipelines.vibe_check import run_vibe_check


def test_vibe_check_flags_generic_sow_labels():
    project_dir = Path("Projects") / "TestSowGranularityProj"
    arch_dir = project_dir / "docs" / "01-architecture"
    arch_dir.mkdir(parents=True, exist_ok=True)

    try:
        (arch_dir / "SOW_TestSowGranularityProj.md").write_text(
            """# SOW Test

| # | Discipline & Tâche | SP | Heures | Commentaires |
| :---: | :--- | :---: | :---: | :--- |
| 3.1 | Développement divers | 12 SP | 96 h | [Détail des récits] |
""",
            encoding="utf-8",
        )

        result = run_vibe_check("TestSowGranularityProj")
        sow_checks = [c for c in result["checks"] if "Granularité SOW" in c["check"]]
        assert len(sow_checks) == 1
        assert sow_checks[0]["status"] == "FAIL"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_sow_has_concrete_labels():
    project_dir = Path("Projects") / "TestSowGranularityProj2"
    arch_dir = project_dir / "docs" / "01-architecture"
    arch_dir.mkdir(parents=True, exist_ok=True)

    try:
        (arch_dir / "SOW_TestSowGranularityProj2.md").write_text(
            """# SOW Test

| # | Discipline & Tâche | SP | Heures | Commentaires |
| :---: | :--- | :---: | :---: | :--- |
| 3.1 | Application Mobile : Profil & Authentification | 12 SP | 96 h | Inscription sécurisée. |
""",
            encoding="utf-8",
        )

        result = run_vibe_check("TestSowGranularityProj2")
        sow_checks = [c for c in result["checks"] if "Granularité SOW" in c["check"]]
        assert len(sow_checks) == 1
        assert sow_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_no_sow_exists():
    project_dir = Path("Projects") / "TestSowGranularityProj3"
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_vibe_check("TestSowGranularityProj3")
        sow_checks = [c for c in result["checks"] if "Granularité SOW" in c["check"]]
        assert len(sow_checks) == 1
        assert sow_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
