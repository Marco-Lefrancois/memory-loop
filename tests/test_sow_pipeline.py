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


# ── ADR-0331 §2.2.3 : Interdiction Formelle des Libellés Génériques ──────────


def test_sow_validate_granularity_flags_generic_labels(tmp_path: Path):
    """
    Un libellé de tâche générique (« [Détail des récits] », « Composant
    générique », « Développement divers ») dans le tableau de chiffrage détaillé
    doit être rejeté par le linter de conformité (ADR-0331 §2.2 Règle #3).
    """
    project_dir = tmp_path / "Projects" / "Metro_Generic"
    project_dir.mkdir(parents=True)

    sow_content = """# SOW Test

| # | Discipline & Tâche | SP | Heures | Commentaires |
| :---: | :--- | :---: | :---: | :--- |
| 3.1 | Développement divers | 12 SP | 96 h | [Détail des récits] |
| 3.2 | Composant générique | 10 SP | 80 h | À définir. |
"""
    out_dir = project_dir / "docs" / "01-architecture"
    out_dir.mkdir(parents=True)
    sow_file = out_dir / "SOW_Metro_Generic.md"
    sow_file.write_text(sow_content, encoding="utf-8")

    engine = SOWEngine(project_dir)
    violations = engine.validate_task_granularity(sow_file)

    assert len(violations) >= 2
    joined = " ".join(violations)
    assert "Développement divers" in joined or "développement divers" in joined.lower()
    assert "Composant générique" in joined or "composant générique" in joined.lower()
    assert "[Détail des récits]" in joined


def test_sow_validate_granularity_passes_on_concrete_labels(tmp_path: Path):
    """Un tableau de chiffrage avec des libellés fonctionnels concrets ne doit lever aucune violation."""
    project_dir = tmp_path / "Projects" / "Metro_Concrete"
    project_dir.mkdir(parents=True)

    sow_content = """# SOW Test

| # | Discipline & Tâche | SP | Heures | Commentaires |
| :---: | :--- | :---: | :---: | :--- |
| 3.1 | Application Mobile : Profil, Authentification & Tâches | 12 SP | 96 h | Inscription sécurisée, onboarding déclaratif. |
"""
    out_dir = project_dir / "docs" / "01-architecture"
    out_dir.mkdir(parents=True)
    sow_file = out_dir / "SOW_Metro_Concrete.md"
    sow_file.write_text(sow_content, encoding="utf-8")

    engine = SOWEngine(project_dir)
    violations = engine.validate_task_granularity(sow_file)

    assert violations == []
