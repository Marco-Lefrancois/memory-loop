import pytest
from pathlib import Path
from src.core.layout import ProjectLayout, load_adr_contracts
from src.engine.invest_evaluator import InvestEvaluator, InvestEvaluationResult


def test_project_layout_constants():
    """Vérifie que ProjectLayout charge correctement les constantes depuis adr-contracts.json."""
    assert "reference" in ProjectLayout.CLIENT_LAYOUT
    assert "docs" in ProjectLayout.CLIENT_LAYOUT
    assert "backlog" in ProjectLayout.CLIENT_LAYOUT
    assert "memory" in ProjectLayout.CLIENT_LAYOUT
    assert "src" in ProjectLayout.FORBIDDEN_CLIENT
    assert ProjectLayout.ACTIVE_PROJECT_FILE == "memory/active_project.json"
    
    contracts = load_adr_contracts()
    assert "ADR-0100" in contracts
    assert "ADR-0102" in contracts


def test_invest_evaluator_compliant_story():
    """Vérifie l'évaluation positive d'un récit conforme au gabarit 4 piliers."""
    story_markdown = """---
id: REC-001
jira_key: COUVBOIRE-101
title: Exportation du rapport de couverture
type: Feature
status: READY_FOR_DEV
---

# Exportation du rapport de couverture

## Contexte Métier
En tant que gestionnaire d'approvisionnement,
Afin d'obtenir une vision consolidée des stocks,
Je veux exporter le rapport de couverture au format CSV.

## Critères d'acceptation
- Le bouton Export CSV est visible sur la vue de synthèse.
- Un clic génère le fichier avec encodage UTF-8.

## Scénarios de test

### Pilier 1 : Scénario Nominal
Étant donné un gestionnaire authentifié sur l'écran des rapports
Quand il clique sur le bouton d'export CSV
Alors le navigateur télécharge le fichier de rapport complet.

### Pilier 2 : Scénario d'Exception
Étant donné un rapport sans données associées
Quand le gestionnaire déclenche l'export
Alors un message d'avertissement 'Aucune donnée disponible' est affiché.

### Pilier 3 : Résilience
Étant donné une perte de réseau pendant la génération
Alors le système affiche une notification de reprise sans crash.

### Pilier 4 : UX & Accessibilité
Étant donné l'ouverture du modal d'export
Alors le focus clavier est positionné sur le bouton de confirmation.
"""
    result = InvestEvaluator.evaluate_story_content(story_markdown)
    assert isinstance(result, InvestEvaluationResult)
    assert result.has_nominal is True
    assert result.has_exceptions is True
    assert result.has_resilience is True
    assert result.has_ux is True
    assert result.code_leak_detected is False
    assert result.total_score >= 80.0
    assert result.is_compliant is True


def test_invest_evaluator_code_leak_detection():
    """Vérifie la détection d'une fuite de code physique dans le récit Markdown."""
    bad_story = """# Mon Récit avec du code
```python
def handle_click(event):
    import requests
    requests.get('http://api')
```
"""
    result = InvestEvaluator.evaluate_story_content(bad_story)
    assert result.code_leak_detected is True
    assert result.is_compliant is False
    assert any("code source physique" in r for r in result.recommendations)
