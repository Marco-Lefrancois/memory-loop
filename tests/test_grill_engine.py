"""
Tests unitaires pour le GrillEngine et la conformité ADR-0320 (Frontier Design Tree).
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.pipelines.grill_engine import GrillEngine
from src.state import ProjectLayout, StoryStatus


@pytest.fixture
def temp_project(tmp_path):
    """Crée une arborescence projet mLoop temporaire."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(parents=True)
    
    docs_dir = project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
    docs_dir.mkdir(parents=True)
    
    backlog_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    backlog_dir.mkdir(parents=True)
    
    sprint_backlog = project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sprint_backlog.write_text(
        "# Sprint Backlog\n\n| ID | Titre | Statut |\n| :--- | :--- | :--- |\n| US-01 | Initialisation UI | IN_ANALYZE |\n",
        encoding="utf-8"
    )
    
    story_file = backlog_dir / "US-01_initialisation_ui.md"
    story_file.write_text(
        "---\nid: US-01\ntitle: Initialisation UI\nstatus: IN_ANALYZE\n---\n## Description\nInitialisation.",
        encoding="utf-8"
    )
    
    return project_dir


def test_grill_engine_record_adr(temp_project):
    """Vérifie la génération d'un ADR structuré."""
    engine = GrillEngine(temp_project)
    adr_path = engine.record_adr(
        title="Adoption du Frontier Design Tree",
        context="Alignement sur l'arbre de décision préalable.",
        decision="Intégration du pattern Grill-Me.",
        positives="Clarté et réduction du flou.",
        negatives="Temps d'interrogatoire initial."
    )
    
    assert adr_path.exists()
    content = adr_path.read_text(encoding="utf-8")
    assert "ADR-001" in content
    assert "Adoption du Frontier Design Tree" in content
    assert "**Statut** : DECIDED" in content
    assert "Intégration du pattern Grill-Me." in content


def test_grill_engine_mark_story_grilled(temp_project):
    """Vérifie la transition FSM et le marquage du statut READY_FOR_GROOMING."""
    engine = GrillEngine(temp_project)
    success = engine.mark_story_grilled("US-01")
    assert success is True
    
    # Vérification fichier story
    story_file = temp_project / ProjectLayout.BACKLOG / "stories" / "US-01_initialisation_ui.md"
    content = story_file.read_text(encoding="utf-8")
    assert "status: READY_FOR_GROOMING" in content
    assert "content_hash:" in content  # Hash anti-tampering
    
    # Vérification sprint_backlog.md
    sb_file = temp_project / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sb_content = sb_file.read_text(encoding="utf-8")
    assert "READY_FOR_GROOMING" in sb_content


def test_grill_skill_conformance():
    """Vérifie la présence des composantes clés d'ADR-0320 dans le skill grill."""
    skill_file = Path(".agents/skills/grill/SKILL.md")
    assert skill_file.exists()
    content = skill_file.read_text(encoding="utf-8")
    
    # Vérification des concepts clés
    assert "Frontier Design Tree" in content or "Design Tree" in content
    assert "Faits vs Décisions" in content
    assert "CONTEXT.md" in content
    assert "to-questionnaire" in content
    assert "5 Vecteurs de Résilience" in content or "Résilience" in content
    assert "4 États" in content or "Matrice des 4 États" in content

    # ADR-0320 §F/§G (amendement 2026-08-26) : Règle d'Épuisement de Frontière
    # par récit et fiabilisation du signal de confiance / priorité au code source.
    assert "Frontier Exhaustion" in content or "Épuisement de Frontière" in content
    assert "avance automatiquement" in content


def test_adr_0320_frontier_exhaustion_sections_present():
    """Vérifie la présence des sections F & G dans l'ADR-0320 (amendement 2026-08-26)."""
    adr_file = Path("standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md")
    assert adr_file.exists()
    content = adr_file.read_text(encoding="utf-8")

    assert "Règle d'Épuisement de Frontière par Récit" in content
    assert "Critère d'Arrêt Unitaire" in content
    assert "Avancement Automatique vers le Récit Suivant" in content
    assert "code_source_verified" in content
    assert "file_existence_only" in content


def test_evidence_pack_no_hardcoded_high_confidence_without_code_proof():
    """
    Vérifie que EvidencePackEngine.extract_evidence() ne retourne plus HIGH/1.0
    par défaut pour un récit sans aucune preuve de type code_source_verified
    (ADR-0320 §G — anti-régression du score codé en dur).
    """
    from src.pipelines.evidence_pack import EvidencePackEngine

    project_dir = Path(tempfile.mkdtemp())
    try:
        backlog_dir = project_dir / "backlog" / "stories"
        backlog_dir.mkdir(parents=True)

        # Récit ne citant que de la documentation (aucun fichier de code source réel)
        story_file = backlog_dir / "US-99_sans_code.md"
        story_file.write_text(
            "---\nid: US-99\ntitle: Sans Code Source\nstatus: OPEN\n---\n"
            "## Description\nRécit basé uniquement sur specs.md.\n",
            encoding="utf-8"
        )

        engine = EvidencePackEngine(project_dir)
        pack = engine.extract_evidence(story_file)

        assert pack["confidence"] != "HIGH" or pack["confidence_score"] != 1.0 or not pack["fact_search_proofs"], (
            "Un récit sans preuve code_source_verified ne doit pas hériter d'un score HIGH/1.0 par défaut."
        )
        assert pack["status"] in ("VALIDATED", "STALE_PENDING_REGENERATION")
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
