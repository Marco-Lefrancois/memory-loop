"""
Test de validation du 10e contrôle Vibe-Check : Contrat Visuel Lisible (Phase 2.3 —
Plan d'Implémentation Framework Enforcement Déterministe du Grounding Visuel & Épistémique).

Un projet frontend/fullstack dont une maquette ingérée est vectorisée (is_vectorized: true)
sans que l'OCR n'ait pu la lire (ocr_status != "DONE") doit déclencher un WARNING (non
bloquant à ce stade — cf. Phase 1/2.3 du plan), signalant l'angle mort du Contrat Visuel.
"""

from pathlib import Path
import shutil

from src.pipelines.vibe_check import run_vibe_check


def _mockup_frontmatter(is_vectorized: bool, ocr_status: str) -> str:
    return f"""---
title: "Spécification UI : Écran Test"
document_type: "ui_specification"
source_svg: "ecran_test.svg"
is_vectorized: {str(is_vectorized).lower()}
ocr_status: "{ocr_status}"
---
# Spécification UI Extraite
"""


def test_vibe_check_flags_unread_vectorized_mockup():
    project_dir = Path("Projects") / "TestVisualContractProj"
    maquettes_dir = project_dir / "docs" / "00-ingested" / "maquettes"
    maquettes_dir.mkdir(parents=True, exist_ok=True)

    try:
        (maquettes_dir / "ecran_test.md").write_text(
            _mockup_frontmatter(is_vectorized=True, ocr_status="UNAVAILABLE"),
            encoding="utf-8",
        )

        result = run_vibe_check("TestVisualContractProj")
        visual_checks = [c for c in result["checks"] if "Contrat Visuel Lisible" in c["check"]]
        assert len(visual_checks) == 1
        assert visual_checks[0]["status"] == "FAIL"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_vectorized_mockup_was_ocr_read():
    project_dir = Path("Projects") / "TestVisualContractProj2"
    maquettes_dir = project_dir / "docs" / "00-ingested" / "maquettes"
    maquettes_dir.mkdir(parents=True, exist_ok=True)

    try:
        (maquettes_dir / "ecran_test.md").write_text(
            _mockup_frontmatter(is_vectorized=True, ocr_status="DONE"), encoding="utf-8"
        )

        result = run_vibe_check("TestVisualContractProj2")
        visual_checks = [c for c in result["checks"] if "Contrat Visuel Lisible" in c["check"]]
        assert len(visual_checks) == 1
        assert visual_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_no_mockups_ingested():
    project_dir = Path("Projects") / "TestVisualContractProj3"
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_vibe_check("TestVisualContractProj3")
        visual_checks = [c for c in result["checks"] if "Contrat Visuel Lisible" in c["check"]]
        assert len(visual_checks) == 1
        assert visual_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
