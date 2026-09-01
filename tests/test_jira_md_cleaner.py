import pytest
from src.pipelines.jira.md_cleaner import clean_markdown_description

def test_clean_markdown_description_removes_traceability_notes():
    sample_md = """---
id: US-01-FOOD
jira_key: MMA-4651
---
# US-01 : Initialisation SDK OneTrust & Configuration du Consent Mode (FOOD)

## Description
En tant qu'application FOOD...

## Critères d'acceptation
| Catégorie | Signal |
| --- | --- |
| C0001 | N/A |

---

## 📑 Notes de Traçabilité & Références (IA Only)
> [!IMPORTANT]
> **Source de Vérité (Scan Unique)** : La catégorisation s'appuie sur 8002-metro-Appscan_for_metro-android.md.
"""

    cleaned = clean_markdown_description(sample_md)
    assert "Notes de Traçabilité" not in cleaned
    assert "Source de Vérité" not in cleaned
    assert "Critères d'acceptation" in cleaned
    assert "En tant qu'application FOOD" in cleaned

def test_clean_story_markdown_purges_all_traceability_variants():
    from src.pipelines.story_cleaner import clean_story_markdown

    sample_with_notes = """---
id: US-01-COMMERCE
---
# US-01 : Titre

## Scénarios de test
```gherkin
Scénario: Test
```

---

## 📑 Notes de Traçabilité & Références Fact-Search (IA Only)
- **Sources Fact-Search Vérifiées** : doc.md
- 🔗 **Artefact d'Audit Machine (EvidencePack)** : [US-01_evidence.json](file:///...)

---

> 🛡️ **Suite Mémoire & Audit (IA)** :
> - Preuves : memory/evidence/US-01_evidence.json
"""
    cleaned, changed = clean_story_markdown(sample_with_notes)
    assert changed is True
    assert "Notes de Traçabilité" not in cleaned
    assert "Suite Mémoire" not in cleaned
    assert "US-01_evidence.json" not in cleaned
    assert cleaned.endswith("```\n")
    assert "Scénario: Test" in cleaned
