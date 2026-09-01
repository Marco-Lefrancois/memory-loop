---
id: ADR-0329
title: "Standard Canonique de Référencement Inter-Récits (Jira-Only)"
status: Accepted
validation_rules:
  - check_id: no_local_file_paths
    severity: BLOCKING
    target: backlog_stories
    params:
      forbidden_patterns: 
        - "REC-\\d+-FE"
        - "REC-\\d+-BE"
        - "backlog/stories"
---

# ADR-0329 : Standard Canonique de Référencement Inter-Récits

## 1. Contexte
Les références entre récits doivent être basées sur des clés Jira uniques et pérennes (ex: `COUVBOIRE-990`), et non sur des identifiants internes mLoop (ex: `REC-015-FE`) ou des chemins de fichiers locaux.

## 2. Décision
- **Interdiction formelle des références locales** : Dans le corps fonctionnel des stories, aucun lien ne doit pointer vers un fichier local ou utiliser un identifiant interne mLoop.
- **Référencement Jira Exclusif** : Toute dépendance ou lien entre récits doit utiliser exclusivement la clé Jira officielle.
- **Validation** : Le moteur `struct-check` rejettera toute occurrence de pattern interne (`REC-XXX`) dans les sections fonctionnelles.
