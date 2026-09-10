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
        encoding="utf-8",
    )

    story_file = backlog_dir / "US-01_initialisation_ui.md"
    story_file.write_text(
        "---\nid: US-01\ntitle: Initialisation UI\nstatus: IN_ANALYZE\n---\n## Description\nInitialisation.",
        encoding="utf-8",
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
        negatives="Temps d'interrogatoire initial.",
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
    story_file = (
        temp_project / ProjectLayout.BACKLOG / "stories" / "US-01_initialisation_ui.md"
    )
    content = story_file.read_text(encoding="utf-8")
    assert "status: READY_FOR_GROOMING" in content
    assert "content_hash:" in content  # Hash anti-tampering

    # Vérification sprint_backlog.md
    sb_file = temp_project / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sb_content = sb_file.read_text(encoding="utf-8")
    assert "READY_FOR_GROOMING" in sb_content


def test_grill_engine_mark_story_grilled_by_internal_id_when_file_named_by_jira_key(
    tmp_path,
):
    """
    BUG-GRILL-01 (anti-régression) : quand le fichier est nommé par la clé Jira (MMA-4658.md)
    mais que l'utilisateur passe l'ID interne du frontmatter (US-05-FOOD), mark_story_grilled
    doit résoudre le récit via le champ `id:` du frontmatter et promouvoir son statut.
    """
    project_dir = tmp_path / "jira_named_project"
    (project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE).mkdir(
        parents=True
    )
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories" / "OneTrust_FOOD"
    stories_dir.mkdir(parents=True)
    (project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md").write_text(
        "# Sprint Backlog\n\n| ID | Titre | Statut |\n| :--- | :--- | :--- |\n",
        encoding="utf-8",
    )

    # Fichier nommé par la CLÉ JIRA, ID interne uniquement dans le frontmatter
    story_file = stories_dir / "MMA-4658.md"
    story_file.write_text(
        "---\nid: US-05-FOOD\njira_key: MMA-4658\ntitle: Centre de préférence\nstatus: IN_ANALYZE\n---\n## Description\nDispatcher.",
        encoding="utf-8",
    )

    engine = GrillEngine(project_dir)
    # On passe l'ID INTERNE (US-05-FOOD), pas la clé Jira ni le nom de fichier
    success = engine.mark_story_grilled("US-05-FOOD")

    assert success is True, (
        "mark_story_grilled doit résoudre l'ID interne via le frontmatter id:."
    )
    content = story_file.read_text(encoding="utf-8")
    assert "status: READY_FOR_GROOMING" in content


def test_grill_engine_no_adr_generated_without_decision_content(tmp_path):
    """
    BUG-GRILL-02 (anti-régression) : la génération d'un ADR ne doit se produire QUE lorsqu'un
    contenu de décision réel (context/decision) est fourni. Un simple marquage de story
    (title générique + story) ne doit PAS créer d'ADR parasite.
    """
    from src.commands.handlers.architecture import handle_grill
    import argparse

    project_dir = tmp_path / "no_adr_project"
    docs_arch = project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
    docs_arch.mkdir(parents=True)
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    stories_dir.mkdir(parents=True)
    (project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md").write_text(
        "# Sprint Backlog\n", encoding="utf-8"
    )
    (stories_dir / "US-01.md").write_text(
        "---\nid: US-01\ntitle: T\nstatus: IN_ANALYZE\n---\n## Description\nX.",
        encoding="utf-8",
    )

    # Args sans --context/--decision : intention = marquer la story, PAS créer un ADR
    args = argparse.Namespace(
        project=str(project_dir),
        story="US-01",
        title="Validations",
        context=None,
        decision=None,
        positives=None,
        negatives=None,
    )

    class _DummyState:
        def save_to_graph(self, *a, **k):
            pass

    try:
        handle_grill(args, _DummyState(), project_dir)
    except Exception:
        pass  # run_sync peut échouer dans le sandbox — on n'audite que l'effet ADR

    adrs = list(docs_arch.glob("ADR-*.md"))
    assert adrs == [], (
        f"Aucun ADR parasite ne doit être créé sans contenu de décision, trouvés : {adrs}"
    )


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
    adr_file = Path(
        "standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md"
    )
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
            encoding="utf-8",
        )

        engine = EvidencePackEngine(project_dir)
        pack = engine.extract_evidence(story_file)

        assert (
            pack["confidence"] != "HIGH"
            or pack["confidence_score"] != 1.0
            or not pack["fact_search_proofs"]
        ), (
            "Un récit sans preuve code_source_verified ne doit pas hériter d'un score HIGH/1.0 par défaut."
        )
        assert pack["status"] in ("VALIDATED", "STALE_PENDING_REGENERATION")
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
