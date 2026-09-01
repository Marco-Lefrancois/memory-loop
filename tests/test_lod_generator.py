"""
Tests unitaires pour le générateur de sidecars LOD et le contrôle de fraîcheur OKF (ADR-0335).
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from src.core.lod_generator import LODGenerator


@pytest.fixture
def temp_docs_dir():
    temp_dir = Path(tempfile.mkdtemp(prefix="mloop_lod_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_lod_generator_creates_sidecars(temp_docs_dir):
    # Créer 2 fichiers markdown de test
    file1 = temp_docs_dir / "01_auth.md"
    file1.write_text("# Guide d'Authentification\n\nCe document détaille les flux OAuth2 et JWT.", encoding="utf-8")

    file2 = temp_docs_dir / "02_api.md"
    file2.write_text("# Spécifications API\n\nEndpoints REST pour la gestion des utilisateurs.", encoding="utf-8")

    abstract_file, overview_file = LODGenerator.generate_lod_sidecars(
        directory_path=temp_docs_dir,
        source_info={"kind": "unit_test"},
        project_name="TestProject"
    )

    assert abstract_file.exists()
    assert overview_file.exists()

    abstract_content = abstract_file.read_text(encoding="utf-8")
    assert "directory:" in abstract_content
    assert "freshness:" in abstract_content
    assert "total_entries: 2" in abstract_content

    overview_content = overview_file.read_text(encoding="utf-8")
    assert "# Vue d'Ensemble" in overview_content
    assert "Navigation Rapide" in overview_content
    assert "01_auth.md" in overview_content
    assert "02_api.md" in overview_content


def test_lod_generator_freshness_check(temp_docs_dir):
    # 1. Dossier initial
    f1 = temp_docs_dir / "rule_01.md"
    f1.write_text("# Règle 1\n\nContenu initial de la règle.", encoding="utf-8")

    LODGenerator.generate_lod_sidecars(temp_docs_dir)

    freshness_initial = LODGenerator.check_directory_freshness(temp_docs_dir)
    assert freshness_initial["status"] == "PASS"
    assert freshness_initial["pending_child_changes"] == 0

    # 2. Modification physique d'un fichier enfant
    f1.write_text("# Règle 1 Modifiée\n\nContenu modifié qui change le hash.", encoding="utf-8")

    freshness_after_mod = LODGenerator.check_directory_freshness(temp_docs_dir)
    assert freshness_after_mod["status"] == "OUTDATED"
    assert freshness_after_mod["pending_child_changes"] > 0

    # 3. Auto-healing / Régénération
    LODGenerator.generate_lod_sidecars(temp_docs_dir)
    freshness_healed = LODGenerator.check_directory_freshness(temp_docs_dir)
    assert freshness_healed["status"] == "PASS"


def test_split_markdown_chapters(temp_docs_dir):
    source_file = temp_docs_dir / "large_spec.md"
    content = (
        "# Chapitre 1 : Introduction\n\n" + "Texte de l'intro... " * 100 + "\n\n"
        "# Chapitre 2 : Architecture\n\n" + "Texte d'archi... " * 100 + "\n\n"
        "# Chapitre 3 : Sécurité\n\n" + "Texte de sécu... " * 100 + "\n"
    )
    source_file.write_text(content, encoding="utf-8")

    out_dir = temp_docs_dir / "split_output"
    created = LODGenerator.split_markdown_chapters(source_file, out_dir, min_chars_per_chapter=500)

    assert len(created) == 3
    assert (out_dir / ".abstract.md").exists()
    assert (out_dir / ".overview.md").exists()
