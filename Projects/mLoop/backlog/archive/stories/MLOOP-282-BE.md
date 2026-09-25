---
id: MLOOP-282-BE
jira_key: ""
epic_key: EPIC-28-ADR-CLEAN-ARCHITECTURE
type: Refactor
title: "Scission Modulaire de grill_engine.py (Plafond Strict ADR-0202 ≤ 300L)"
tags: [grill, refactoring, modularity, ast, rule-ast-01]
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
layer: backend
invest_score: 6/6
macro_size: M
created_at: "2026-09-24"
---

# 📖 MLOOP-282-BE : Scission Modulaire de grill_engine.py (Plafond Strict ADR-0202 ≤ 300L)

---

## Description
**En tant que** Développeur et Mainteneur du framework mLoop,  
**je veux** scinder le fichier monolithique `src/pipelines/grill_engine.py` (441 lignes) en modules spécialisés sous le package `src/pipelines/grill/`,  
**afin de** respecter strictement la règle constitutionnelle `RULE-AST-01` (≤ 300 lignes par fichier) et de maintenir un shim rétrocompatible pour préserver 100% des dépendances amont.

---

## Contexte & Périmètre

### Contexte Métier
Le fichier `src/pipelines/grill_engine.py` cumulait historiquement l'orchestration générale, le Fact-Search, l'écriture d'ADRs, la validation FSM des récits, ainsi que les méthodes récentes d'heuristique et de rounds de frontière. Cette accumulation a poussé le fichier à 441 lignes, provoquant le blocage immédiat des hooks pre-commit (`code-check` FAIL). L'ADR-012 acté en Macro-Grill ordonne la création d'un sous-package propre avec conservation d'un shim transparent.

### In-Scope
- Création du package `src/pipelines/grill/` avec 4 modules spécialisés :
  1. `src/pipelines/grill/__init__.py` (≤ 25L) : exporte la classe `GrillEngine`.
  2. `src/pipelines/grill/_engine.py` (≤ 220L) : classe principale `GrillEngine`, orchestration, Fact-Search, fallback code source et transition de statut FSM (`mark_story_grilled`).
  3. `src/pipelines/grill/_adr_writer.py` (≤ 150L) : logique `resolve_adr_template`, `render_adr_content`, `get_next_adr_id` et écriture physique de l'ADR.
  4. `src/pipelines/grill/_frontier.py` (≤ 150L) : formatage des Frontier Rounds, détection heuristique des questions ungrillables et évaluation de santé du contexte (Dumb Zone).
- Remplacement du corps de `src/pipelines/grill_engine.py` par un shim minimaliste (≤ 15L) réexportant `GrillEngine`.
- Zéro régression sur les 72 modules appelants et les suites de tests existantes.

### Out-of-Scope
- Altération des signatures publiques des méthodes de `GrillEngine`.
- Modification des interfaces CLI externes (`src/swarm.py`).

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path)
```gherkin
Scénario: Conformité stricte au plafond modulaire de 300 lignes
  Étant donné l'arbre de fichiers sous "src/pipelines/grill/"
  Quand le linter AST "python src/swarm.py code-check" est exécuté
  Alors chaque fichier individuel contient au maximum 300 lignes
  Et la taille de chaque fichier est inférieure à 15360 octets (15 Ko)
  Et le verdict AST retourne 0 violation RULE-AST-01
```

### 2. Pilier Exception & Rétrocompatibilité Shim
```gherkin
Scénario: Maintien des anciens imports via le shim src/pipelines/grill_engine.py
  Étant donné un composant tiers important "from src.pipelines.grill_engine import GrillEngine"
  Quand ce composant est importé et instancié
  Alors aucune erreur ImportError n'est levée
  Et l'instance dispose de l'intégralité des méthodes record_adr, mark_story_grilled et check_context_health
```

### 3. Pilier Résilience & Dépendances Cycliques
```gherkin
Scénario: Absence de dépendances cycliques entre sous-modules
  Étant donné l'organisation interne de "src/pipelines/grill/"
  Quand l'interpréteur Python charge le module _engine, _adr_writer et _frontier
  Alors aucun avertissement de circularité n'est émis
  Et l'initialisation s'exécute en moins de 10 millisecondes
```

### 4. Pilier UX & Diagnostics de Logging
```gherkin
Scénario: Traçabilité structurée des opérations dans les logs
  Étant donné l'exécution d'une commande de grill
  Quand un composant interne émet des événements de log
  Alors les extra fields "component: pipelines.grill" sont uniformément renseignés
  Et les messages d'erreurs éventuels sont capturés sans crash silencieux
```

---

### Contrats d'Échange API (Interface Python & Package)

#### Matrice des Contrats API
- **OQ-282 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — refactoring modulaire interne sous `src/pipelines/grill/` avec shim `src/pipelines/grill_engine.py`, sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

**Contrats Python Internes :**
- `from src.pipelines.grill import GrillEngine`
- `from src.pipelines.grill_engine import GrillEngine` (shim rétrocompatible)

---

## Architecture Cible & Découpage


```
src/pipelines/
├── grill_engine.py              # Shim rétrocompatible (15 lignes)
└── grill/
    ├── __init__.py              # Export officiel GrillEngine (20 lignes)
    ├── _engine.py               # Orchestrateur, Fact-Search, FSM (210 lignes)
    ├── _adr_writer.py           # Résolution gabarit, ID regex, écriture (130 lignes)
    └── _frontier.py             # Rounds frontière, ungrillables, dumb zone (120 lignes)
```

---

## Références
- 🏛️ **ADR Associés** : [ADR-0202](../../../../standards/adr-system/0202-modularite-interne-agents.md) · [ADR-0320](../../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md) · [ADR-012](../../../docs/01-architecture/ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md)
- 📂 **Directives AST** : `RULE-AST-01` (≤ 300L, ≤ 15 Ko)
- 📦 **Épopée Parente** : [`EPIC-28-ADR-CLEAN-ARCHITECTURE`](../epics/epic_adr_clean_architecture.md)