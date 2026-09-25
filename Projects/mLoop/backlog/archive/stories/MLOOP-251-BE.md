---
id: MLOOP-251-BE
jira_key: ''
epic_key: EPIC-25-OPENCODE-ECOSYSTEM-HARNESS
type: Feature
title: "Bridge d'Outils Natifs TypeScript mLoop pour OpenCode (.opencode/tools/)"
tags:
- opencode
- tools
- typescript
- fts5
- vibe-check
- backend
origin: SPEC_SLICING
source_ref: EPIC-25-§3
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-25'
layer: backend
blocked_by:
- MLOOP-250-BE
created_at: '2026-09-24'
updated_at: '2026-09-25'
---

# 📖 MLOOP-251-BE : Bridge d'Outils Natifs TypeScript mLoop pour OpenCode (.opencode/tools/)

## Description
**En tant qu'** Agent d'implémentation OpenCode opérant sur un projet mLoop,  
**je veux** disposer d'outils TypeScript natifs sous `.opencode/tools/` pour interroger le lexique FTS5 (`fact_search`) et exécuter les vérifications pré-vol (`vibe_check`),  
**afin d'** accéder aux vérités terrain et guardrails mLoop directement depuis le raisonnement du modèle sans recourir à des commandes de terminal artisanales et fragiles.

---

## Contexte & Périmètre

### Contexte Métier
OpenCode (v1.18.30+) permet d'étendre les capacités du LLM en déposant des définitions d'outils typés dans `.opencode/tools/*.ts`. Ces outils sont exécutés par le runtime interne d'OpenCode et exposent des signatures JSON Schema aux modèles. mLoop capitalise sur cette interface pour fournir un accès direct et sécurisé à son moteur de recherche lexicale (FTS5) et à son vérificateur d'invariants (Vibe-Check).

**Décisions Grill-Me (2026-09-25) :**
- Format **TypeScript pur auto-exécutable** sans étape de compilation ni bundler externe requis (consommable directement par le moteur TS embarqué d'OpenCode).
- **Mode lecture seule strict** : aucune mutation de la base SQLite `loop_mem.db` ni des fichiers de gouvernance n'est permise depuis ces outils.
- Générateur Python dédié `src/bridges/opencode/tools_bridge.py` garantissant la cohérence et l'actualisation des outils lors de chaque synchronisation.

### In-Scope
- Développement du générateur `src/bridges/opencode/tools_bridge.py` (≤ 300 lignes, ADR-0202).
- Génération de `.opencode/tools/fact_search.ts` : interrogation FTS5 via pont CLI structuré JSON (`python src/swarm.py fact-search`).
- Génération de `.opencode/tools/vibe_check.ts` : vérification rapide pré-vol via pont CLI structuré JSON (`python src/swarm.py vibe-check --fast`).
- Définition des schémas d'entrée/sortie typés compatibles avec la spécification OpenCode Tool Definition.
- Traitement défensif des erreurs d'exécution et renvoi de diagnostics clairs au modèle.

### Out-of-Scope
- Réécriture de la logique FTS5 ou des 26 contrôles Vibe-Check en pur TypeScript.
- Exposition d'outils mutateurs de base de données en écriture.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Générateur d'Outils — OpenCodeToolsBridge
* **Entrée Métier** : Emplacement cible `.opencode/tools/` et configuration du projet.
* **Traitement & Algorithme Métier** :
  - Déploiement des fichiers sources `fact_search.ts` et `vibe_check.ts`.
  - Typage des arguments d'entrée (`query: string`, `limit?: number` pour search ; `mode?: string` pour vibe-check).
  - Encapsulation des appels de sous-processus Python avec timeout strict de 5 secondes.
  - Parsing de la réponse stdout au format JSON propre.
* **Résultat Métier & Mutations** : Fichiers TypeScript créés avec succès et immédiatement découvrables par OpenCode.

#### 2. Comportement des Outils à l'Exécution
* **Entrée Métier** : Appel tool émis par le modèle OpenCode.
* **Règles de Robustesse** : Si la base FTS5 est temporairement verrouillée ou indisponible, l'outil renvoie un message JSON d'erreur gracieuse plutôt que de planter le processus parent.

---

## Règles d'affaires

- **Lecture Seule Inviolable** : Tout appel provenant de `.opencode/tools/` est confiné en lecture seule (pas de mutation SQLite ni d'écriture disque).
- **Zéro Dépendance Externe Lourde** : Les outils n'exigent pas de `npm install` préalable dans le projet cible.
- **Plafond Modulaire AST** : `src/bridges/opencode/tools_bridge.py` $\le 300$ lignes et $\le 15$ Ko (ADR-0202).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Moteur FTS5** : `src/pipelines/fact_search.py`
- 📂 **Moteur Vibe-Check** : `src/pipelines/vibe_check/__init__.py`
- 🏛️ **ADR** : [ADR-0377](../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) · [ADR-0369](../../../standards/adr-system/0369-standard-robustesse-python-senior.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_opencode_ecosystem_harness.md`](../epics/epic_opencode_ecosystem_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Bridge d'Outils TypeScript pour OpenCode

  Scénario: Pilier 1 - Nominal (Happy path) : Génération et exécution de fact_search.ts
    Étant donné un projet mLoop avec base FTS5 indexée
    Quand le bridge déploie les outils sous .opencode/tools/
    Alors le fichier fact_search.ts est généré avec son schéma de validation
    Et l'invocation avec query="ADR-0377" renvoie les extraits textuels en moins de 150 ms

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Requête FTS5 sans résultat
    Étant donné une requête fact_search avec un mot-clé inexistant "terme_totalement_inconnu_xyz"
    Quand l'outil s'exécute
    Alors la sortie JSON indique "total_results: 0" et "matches: []" sans lever d'exception non gérée

  Scénario: Pilier 3 - Résilience (Timeout & Mode dégradé) : Timeout sous-processus CLI
    Étant donné un appel à vibe_check.ts dont le sous-processus tarde plus de 5 secondes
    Quand l'interpréteur tool atteint le timeout
    Alors l'exécution est interrompue proprement
    Et une réponse JSON d'erreur avec code "TIMEOUT_EXPIRED" est renvoyée au modèle

  Scénario: Pilier 4 - UX (Accessibilité & Schéma explicite) : Documentation intégrée des outils
    Étant donné l'inspection des métadonnées des outils générés
    Quand OpenCode interroge la description et les paramètres
    Alors chaque outil présente une documentation claire en français et en anglais
    Et les types de données sont strictement décrits via JSON Schema
```
