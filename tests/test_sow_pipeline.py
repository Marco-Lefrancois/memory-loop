"""
Tests unitaires pour le SOWEngine et la commande to-sow (mLoop).
"""

import pytest
from pathlib import Path
from src.pipelines.sow_engine import SOWEngine


def test_sow_engine_loads_blueprint(tmp_path: Path):
    """Vérifie que le SOWEngine accède au gabarit officiel."""
    project_dir = tmp_path / "Projects" / "Test_Project"
    project_dir.mkdir(parents=True)

    engine = SOWEngine(project_dir)
    blueprint = engine.get_blueprint_content()

    assert "# [TITRE DU PROJET] — Énoncé des Travaux" in blueprint
    assert "Grille de Référence Kevin Chamberland" in blueprint
    assert "Conception UX/UI" in blueprint
    assert "Assurance Qualité (QA)" in blueprint


def test_sow_engine_generates_sow(tmp_path: Path):
    """Vérifie la génération d'un SOW complet avec chiffrage T-Shirt Size."""
    project_dir = tmp_path / "Projects" / "Metro_Test"
    (project_dir / "docs" / "00-ingested").mkdir(parents=True)
    (project_dir / "backlog" / "stories").mkdir(parents=True)

    # Fake ingested file
    (project_dir / "docs" / "00-ingested" / "brief.md").write_text(
        "# Brief Santé\nIntégration du dossier santé pour Metro.", encoding="utf-8"
    )

    engine = SOWEngine(project_dir)
    sow_file = engine.generate_sow(title="Metro Test Dossier", target_size="M")

    assert sow_file.exists()
    content = sow_file.read_text(encoding="utf-8")

    assert "Metro Test Dossier" in content
    assert "`M`" in content
    assert "95 000 $" in content
    assert "760" in content  # 95 * 8 = 760 h
