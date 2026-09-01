# -*- coding: utf-8 -*-
"""
Tests unitaires pour Rubber Duck 2.0 (L'Avocat du Diable avec Discernement, Cohérence & Rigueur).
"""

import pytest
import json
from pathlib import Path

from src.engine.rubber_duck.coherence import CrossStoryCoherenceChecker, CoherenceIssue
from src.engine.rubber_duck.remediator import RubberDuckRemediator, RemediationPatch
from src.engine.rubber_duck.critic import DevilAdvocateCritic, DevilAdvocateCritique
from src.engine.rubber_duck import RubberDuckEngine, evaluate_story_critique
from src.pipelines.rubber_duck import RubberDuckEngine as LegacyRubberDuckPipeline


def test_cross_story_coherence_detection(tmp_path):
    """Vérifie que CrossStoryCoherenceChecker détecte les chevauchements de périmètre entre récits."""
    project_dir = tmp_path / "Projects" / "TestCoherence"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    story_a = stories_dir / "US-001.md"
    story_a.write_text(
        "---\nid: US-001\ntitle: Exportation et synchronisation des factures clients\n---\n"
        "# Exportation et synchronisation des factures clients\n\n"
        "## Critères d'acceptation\n"
        "- L'utilisateur peut exporter et lancer la synchronisation des factures au format PDF.\n",
        encoding="utf-8"
    )

    story_b = stories_dir / "US-002.md"
    story_b.write_text(
        "---\nid: US-002\ntitle: Synchronisation et exportation des factures clients PDF\n---\n"
        "# Synchronisation et exportation des factures clients PDF\n\n"
        "## Critères d'acceptation\n"
        "- L'utilisateur peut synchroniser et exporter les factures clients au format PDF.\n",
        encoding="utf-8"
    )

    issues = CrossStoryCoherenceChecker.check_story_coherence(
        story_file=story_a,
        project_dir=project_dir,
    )

    assert len(issues) >= 1
    assert any(i.issue_type == "SCOPE_OVERLAP" for i in issues)
    assert any("US-002" in i.description for i in issues)


def test_critic_business_discernment_and_silent_failures(tmp_path):
    """Vérifie la détection des faiblesses de discernement métier et des défaillances silencieuses."""
    project_dir = tmp_path / "Projects" / "TestCritic"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    flawed_story = stories_dir / "US-FLAWED.md"
    flawed_story.write_text(
        "---\nid: US-FLAWED\ntitle: Paiement express\n---\n"
        "# Paiement express\n\n"
        "## Critères d'acceptation\n"
        "- Le système doit être rapide et facile à utiliser pour l'utilisateur.\n\n"
        "## Scénarios de test\n\n"
        "### Pilier 1 : Scénario Nominal\n"
        "- Étant donné un panier valide\n"
        "- Quand l'utilisateur clique sur Payer\n"
        "- Alors le paiement est accepté.\n",
        encoding="utf-8"
    )

    critique = DevilAdvocateCritic.evaluate_story(
        story_file=flawed_story,
        project_name="TestCritic",
        project_dir=project_dir,
        persist_evidence=True,
    )

    assert critique.status in ("ACTION_REQUIRED", "REJECTED")
    assert critique.business_discernment_score < 90.0
    # Vérifier que les termes vagues "rapide", "facile" ont été pénalisés
    assert any("subjectifs" in f or "rapide" in f for f in critique.critical_flaws)
    # Vérifier que les défaillances silencieuses (timeout, double-clic, session expirée) sont relevées
    assert len(critique.silent_failures) >= 2
    # Vérifier la présence de patchs de remédiation
    assert len(critique.remediation_patches) >= 1

    # Vérifier l'intégration dans l'EvidencePack
    evidence_file = project_dir / "memory" / "evidence" / "US-FLAWED_evidence.json"
    assert evidence_file.exists()
    evidence_data = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert "devil_advocate_review" in evidence_data
    assert evidence_data["devil_advocate_review"]["status"] == critique.status


def test_remediator_gherkin_patch_generation():
    """Vérifie la génération de patchs Gherkin chirurgicaux par RubberDuckRemediator."""
    flaws = [
        "Absence de scénario en cas de timeout API ou de coupure réseau inopinée.",
        "Absence de protection contre la soumission multiple rapide (anti-rebond).",
        "Spécification insuffisante des états de chargement et de la navigation clavier.",
    ]
    patches = RubberDuckRemediator.generate_remediation_patches(
        story_content="",
        detected_flaws=flaws,
        story_id="US-TEST",
    )

    assert len(patches) == 3
    pillars = [p.pillar_target for p in patches]
    assert any("Résilience" in p for p in pillars)
    assert any("Concurrence" in p for p in pillars)
    assert any("UX" in p for p in pillars)

    for p in patches:
        assert "Étant donné" in p.suggested_gherkin
        assert "Quand" in p.suggested_gherkin
        assert "Alors" in p.suggested_gherkin


def test_rubber_duck_pipeline_delegation_compatibility(tmp_path):
    """Vérifie que l'ancien point d'entrée de pipeline délègue sans régression."""
    project_dir = tmp_path / "Projects" / "TestLegacy"
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    story = stories_dir / "US-099.md"
    story.write_text(
        "---\nid: US-099\ntitle: Story Robuste\n---\n"
        "# Story Robuste\n\n"
        "## Critères d'acceptation\n"
        "- Temps de réponse inférieur à 200ms.\n\n"
        "## Scénarios de test\n\n"
        "### Pilier 1 : Scénario Nominal\n"
        "- Étant donné un utilisateur connecté\n"
        "- Quand il consulte son profil\n"
        "- Alors ses données s'affichent.\n\n"
        "### Pilier 2 : Exceptions\n"
        "- Étant donné un profil inexistant\n"
        "- Quand l'API renvoie une erreur 404\n"
        "- Alors une notification d'erreur s'affiche.\n\n"
        "### Pilier 3 : Résilience\n"
        "- Étant donné un timeout réseau (503)\n"
        "- Quand l'utilisateur réessaie avec un double-clic anti-rebond\n"
        "- Alors un message de service dégradé s'affiche sans crash.\n\n"
        "### Pilier 4 : UX & Accessibilité\n"
        "- Étant donné l'ouverture de la page\n"
        "- Quand le lecteur d'écran parcourt les champs\n"
        "- Alors chaque balise ARIA est correctement vocalisée.\n",
        encoding="utf-8"
    )

    pipeline = LegacyRubberDuckPipeline(project_dir)
    res = pipeline.evaluate_file(story, force=True)

    assert "scores" in res
    assert "remediation_patches" in res
    assert "blocking_issues" in res
