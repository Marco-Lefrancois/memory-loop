---
id: ADR-0328
title: "Standard de Validation des Règles d'Adhérence et Moteur de Conformité (Rule Engine)"
status: Accepted
validation_rules:
  - check_id: adr_frontmatter_schema
    severity: BLOCKING
    target: adr_system
    params:
      required_fields:
        - "id"
        - "title"
        - "status"
---

# ADR-0328 : Standard de Validation des Règles d'Adhérence et Moteur de Conformité (Rule Engine)
## Statut : Accepté (Série 03xx - Gouvernance & Conformité Normative)
## Autorité : [ADR-0000](0000-agentic-coworker-framework.md), [ADR-0300](0300-story-constraint-contract.md), [ADR-0303](0303-harnachement-blueprints-markdown.md)

---

## 1. Contexte & Problématique

Dans les systèmes multi-agents complexes, les décisions d'architecture (ADRs) risquent de devenir des documents passifs si aucune mécanique d'évaluation continue ne vérifie leur respect dans le code et les artefacts.

Pour garantir que chaque décision architecturale devienne une règle exécutable de manière déterministe, mLoop intègre un moteur d'adhérence (`RuleEngine`) qui charge les contraintes déclaratives directement depuis le frontmatter YAML des ADRs.

---

## 2. Décision

Nous officialisons le **Moteur de Règles d'Adhérence (`RuleEngine`)** et le schéma déclaratif des règles dans les ADRs :

### 1. Schéma Déclaratif dans les Frontmatters d'ADR
Chaque ADR prescriptive peut définir un bloc `validation_rules` dans son frontmatter YAML :
```yaml
---
id: ADR-XXXX
title: "Titre de la décision"
status: Accepted
validation_rules:
  - check_id: nom_unique_de_la_regle
    severity: BLOCKING | WARNING | INFO
    target: backlog_stories | architecture_docs | codebase
    params:
      forbidden_patterns: [...]
      required_elements: [...]
---
```

### 2. Chargement Dynamique & Exécution Déterministe
- Le composant `src/core/rule_engine.py` scanne à chaud les répertoires d'ADRs (`standards/adr-system/` et `Projects/<nom>/docs/01-architecture/`).
- Les règles sont injectées dynamiquement dans les pipelines de validation (`struct-check`, `vibe-check`, `validate`).
- En cas de non-respect d'une règle de sévérité `BLOCKING`, la transition d'état ou le commit est automatiquement rejeté.

### 3. Traçabilité des Violations
Chaque violation relevée par le moteur indique explicitement l'ADR source (`adr_id`), le `check_id` et la prescription corrective.

---

## 3. Conséquences

- **Lois Exécutables (Executable Architecture)** : Les ADRs ne sont plus du texte statique mais des garde-fous logiciels actifs.
- **Auditabilité Totale** : Traçabilité directe entre une anomalie détectée et la décision architecturale correspondante.
- **Zéro Régression Invisible** : Toute tentative de réintroduire un antipattern documenté dans une ADR est immédiatement interceptée.
