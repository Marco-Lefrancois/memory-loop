---
id: MLOOP-240-BE
jira_key: ''
epic_key: EPIC-24-SKILLS-EVAL-HARNESS
type: Feature
title: "Moteur d'Évaluation Déterministe & Rubrique Sémantique 100 pts pour Compétences"
tags:
- skills
- eval
- rubric
- deterministic
- backend
origin: SPEC_SLICING
source_ref: EPIC-24-§4.1
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: backend
blocked_by: []
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-240-BE : Moteur d'Évaluation Déterministe & Rubrique Sémantique 100 pts pour Compétences

## Description
**En tant qu'** Architecte Agentique / Développeur mLoop,
**je veux** étendre le `SkillEvalEngine` existant (`src/pipelines/skill_eval.py`) pour intégrer les Golden Datasets et produire un score déterministe statique (Système 1) sur 100 points par compétence,
**afin de** disposer d'un audit automatisé et reproductible de la qualité de chaque manifeste `.agents/skills/*/SKILL.md` sans recourir à des appels LLM coûteux.

---

## Contexte & Périmètre

### Contexte Métier
L'écosystème mLoop compte 39 compétences déclarées. L'audit reposait sur `SkillDoctor` (hygiène statique budgétaire) et `SkillEvalEngine` (rubrique 4 axes × 25 pts). Ce récit étend l'existant pour y intégrer la consommation de Golden Datasets (`memory/evals/skills/<skill_name>/cases.json`) et produit un rapport consolidé JSON + Markdown persisté sous `memory/evals/skills_eval_summary.json`.

**Décisions Grill (2026-09-24) :**
- Scope : **Système 1 statique uniquement** (lint de manifeste + assertions déterministes), pas d'invocation LLM comportementale (Système 2 différé à EPIC-24-v2).
- Seuil de passage : **80 pts** (aligné sur `PASS_THRESHOLD` existant dans `skill_eval.py`).
- Extension de l'existant, **pas de remplacement**.
- Les 8 `HEAVY_META_SKILLS` (`zero-blindspot-spec`, `handoff`, `router`, `sentinel`, `rubber-duck`, `calibrate`, `obsidian-canvas`, `visual-excalidraw`, `visual-mermaid`) bénéficient de **couverture statique seule** — identiques aux exclusions déjà dans le code.

### In-Scope
- Extension de `SkillEvalEngine` dans `src/pipelines/skill_eval.py` : ajout de la méthode `evaluate_with_golden_dataset(skill_name, cases_path)`.
- Chargement et validation des cas de test depuis `memory/evals/skills/<skill_name>/cases.json` (créés par MLOOP-241-BE).
- Calcul d'un score `golden_dataset_score` (assertions déterministes Système 1) injecté dans le rapport final.
- Production d'un rapport consolidé `memory/evals/skills_eval_summary.json` et `skills_eval_summary.md`.
- Respect strict de la contrainte `ADR-0202` : modules ≤ 300 lignes. Si extension dépasse le plafond, scission en `skill_eval_core.py` + `skill_eval_report.py`.

### Out-of-Scope
- Évaluation comportementale LLM-as-a-judge (Système 2) — différé à EPIC-24-v2.
- Modification du seuil de passage (reste à 80 pts pour cette épopée).
- Génération des Golden Datasets (responsabilité de MLOOP-241-BE).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extension SkillEvalEngine — evaluate_with_golden_dataset
* **Entrée Métier** : Nom de la skill + chemin vers `cases.json` (liste de `{"input": ..., "expect_triggered": bool, "expect_static": {...}}`)
* **Règles d'admissibilité & Validation** : Si `cases.json` absent ou invalide → score `golden_dataset_score = 0`, warning loggé, pas de crash.
* **Traitement & Algorithme Métier** : Pour chaque cas, vérification déterministe Système 1 (présence de mots-clés dans le manifeste vs. attendu). Score = (cas passés / total cas) × 100.
* **Résultat Métier & Mutations** : Score injecté dans `SkillEvalResult.scores_breakdown["golden_dataset"]`. Score total recalibré : moyenne pondérée 80% rubrique statique + 20% golden dataset.
* **Cas de Rejet Métier** : `cases.json` corrompu → warning non bloquant, score golden = 0. Skill introuvable → `FAIL` avec message explicite.

#### 2. Rapport Consolidé JSON + Markdown
* **Entrée Métier** : Liste complète des `SkillEvalResult` pour les 39 skills.
* **Traitement** : Agrégation en `skills_eval_summary.json` + formatage Markdown `skills_eval_summary.md`.
* **Résultat** : Fichiers persistés sous `memory/evals/` avec timestamp ISO 8601.

### Contrats d'Échange API
- Aucun endpoint réseau. Module Python pur, appelé par CLI `mloop skill-eval`.

---

## Parcours Interactif & API
N/A — module backend pur.

---

## Règles d'affaires

- **Seuil Souverain 80 pts** : Toute skill sous 80 pts → verdict `FAIL`. Entre 65 et 80 → `WARNING`. Au-dessus → `PASS`.
- **HEAVY_META_SKILLS exclues du golden_dataset** : Score `golden_dataset_score = N/A` pour ces 8 skills ; leur score total reste basé à 100% sur la rubrique statique 4 axes.
- **Plafond AST strict** : Aucun module ne dépasse 300 lignes. Si `skill_eval.py` dépasse après extension → scission obligatoire avant merge.
- **Persistance non-destructive** : Le rapport est toujours écrit en remplacement du précédent (pas d'accumulation), sauf `skill_impact.jsonl` (append).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Sources normatives** : [`src/pipelines/skill_eval.py`](../../../src/pipelines/skill_eval.py), [`src/pipelines/skill_doctor.py`](../../../src/pipelines/skill_doctor.py)
- 🏛️ **ADR** : [ADR-0308](../../../standards/adr-system/0308-mcp-prompts-and-evals-engine.md) · [ADR-0348](../../../standards/adr-system/0348-wikiskill-tri-layer-evolution.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_skills_eval_harness.md`](../epics/epic_skills_eval_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Extension SkillEvalEngine avec Golden Datasets Système 1

  Scénario: Évaluation nominale d'une skill avec golden dataset valide
    Étant donné une skill "grill" avec un manifeste SKILL.md valide
    Et un fichier "memory/evals/skills/grill/cases.json" contenant 3 cas (nominal, limite, adversarial)
    Quand j'appelle evaluate_with_golden_dataset("grill", cases_path)
    Alors le résultat contient un champ "golden_dataset" dans scores_breakdown
    Et le score total est une moyenne pondérée 80/20 entre rubrique statique et golden dataset
    Et le rapport est persisté sous "memory/evals/skills_eval_summary.json"

  Scénario: Évaluation d'une HEAVY_META_SKILL sans golden dataset comportemental
    Étant donné une skill "sentinel" appartenant aux HEAVY_META_SKILLS
    Quand j'appelle evaluate_all()
    Alors le champ "golden_dataset" est absent ou marqué "N/A"
    Et le score total est basé à 100% sur la rubrique statique 4 axes

  Scénario: Fichier cases.json absent ou corrompu
    Étant donné une skill "archify" sans fichier cases.json dans memory/evals/skills/archify/
    Quand j'appelle evaluate_with_golden_dataset("archify", cases_path)
    Alors golden_dataset_score = 0 avec un warning loggé
    Et l'évaluation continue sans crash (dégradation gracieuse)

  Scénario: Violation AST — module dépasse 300 lignes
    Étant donné l'extension de skill_eval.py
    Quand le module atteint 301 lignes ou plus
    Alors la CI bloque le merge avec une violation ADR-0202
    Et une scission en skill_eval_core.py + skill_eval_report.py est requise
```
