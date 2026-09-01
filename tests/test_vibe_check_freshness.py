"""
Test de validation du guardrail de fraîcheur LOD dans Vibe-Check.
"""
from pathlib import Path
import tempfile
import shutil
import pytest

from src.core.lod_generator import LODGenerator
from src.pipelines.vibe_check import run_vibe_check


def test_vibe_check_lod_freshness_integration():
    # Création d'un projet temporaire pour tester le guardrail
    temp_proj_dir = Path("Projects") / "TestLODProj"
    docs_dir = temp_proj_dir / "docs" / "00-ingested" / "02-guides-et-specs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Fichier initial
        f1 = docs_dir / "spec_test.md"
        f1.write_text("# Spécification Test\n\nContenu initial pour le test de vibe-check.", encoding="utf-8")

        # Générer le sidecar
        LODGenerator.generate_lod_sidecars(docs_dir, project_name="TestLODProj")

        res_pass = run_vibe_check("TestLODProj")
        lod_checks = [c for c in res_pass["checks"] if "Sidecars LOD" in c["check"]]
        assert len(lod_checks) == 1
        assert lod_checks[0]["status"] == "PASS"

        # Modifier le fichier enfant sans mettre à jour le sidecar
        f1.write_text("# Spécification Test Modifiée\n\nNouveau contenu qui désynchronise le hash.", encoding="utf-8")

        res_outdated = run_vibe_check("TestLODProj")
        lod_checks_outdated = [c for c in res_outdated["checks"] if "Sidecars LOD" in c["check"]]
        assert len(lod_checks_outdated) == 1
        assert lod_checks_outdated[0]["status"] == "FAIL"

    finally:
        shutil.rmtree(temp_proj_dir, ignore_errors=True)
