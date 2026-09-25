---
id: MLOOP-023-BE
jira_key: '-'
epic_key: EPIC-3-SAFETY-GOVERNANCE
type: Feature
title: Optimisation RHO et Registre d'Hypothèses Rejetées
tags: [safety, rho, optimizer, retrospective, auto-learning]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-3-SAFETY-GOVERNANCE] Optimisation RHO et Registre d'Hypothèses Rejetées (MLOOP-023-BE)

---

## Description
**En tant qu'** Agent d'Amélioration Récursive et de Sécurité Système,  
**je veux** disposer d'un moteur de rétrospective physique (RHO Optimizer) consignant les règles déterministes et maintenant un registre immuable des hypothèses rejetées,  
**afin d'** ancrer les découvertes efficaces, éviter l'amnésie des agents et éliminer la dérive de règles obsolètes.

---

## Contexte & Périmètre

### Contexte Métier
Le composant Retrospective Harness Optimization (RHO) assure la transition entre l'observation des anomalies d'exécution et leur remédiation permanente. Il bifurque les anomalies mécaniques vers des vérificateurs déterministes AST et consigne les contraintes négatives dans un registre auditable (`rho_impact.yaml`) pour immuniser les sessions futures contre la répétition d'erreurs.

### In-Scope
- Moteur d'optimisation rétrospective `optimize_rho` dans `src/pipelines/rho_optimizer.py`.
- Registre persistant des hypothèses rejetées dans `src/pipelines/rho_registry.py` (`get_rho_impact_file`, `record_rejected_hypothesis`, `get_rejected_hypotheses`).
- Classification automatique déterministe vs jugement via `classify_anomaly`.
- Hygiène périodique et marquage des règles obsolètes `TOMBSTONE` via `dream_collector`.
- Suite de tests unitaire complète sous `tests/test_rho_optimizer.py`.

### Out-of-Scope
- Altération automatique de modèles de fondation externes.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Enregistrement d'Hypothèse Rejetée
* **Entrée Métier** : Nom du projet, mot-clé déclencheur, motif fonctionnel de rejet, portée (`project` ou `global`).
* **Règles d'admissibilité & Validation** : Élimination déterministe des doublons stricts sur le couple (mot-clé, motif).
* **Traitement & Algorithme Métier** : Sérialisation YAML atomique dans `rho_impact.yaml` avec horodatage UTC et verdict `REJECTED`.
* **Résultat Métier & Mutations** : Entrée persistée accessible sans injection de dépendances.
* **Cas de Rejet Métier** : Erreur I/O capturée et journalisée en mode résilient.

#### 2. Bifurcation Déterministe et Hygiène RHO
* **Entrée Métier** : Règle proposée lors d'une rétrospective.
* **Traitement & Algorithme Métier** : Si l'anomalie est mécanique (placeholders, syntaxe, compaction), injection dans `standards/linters/deterministic_rules.json`. Si sémantique, ajout sous `rho_rules.yaml`.
* **Résultat Métier & Mutations** : Règle active opposable ou mise en tombeau (`TOMBSTONE`) en cas de contradiction avec les ADRs.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Optimisation RHO et Registre d'Hypothèses Rejetées

  # CHEMIN NOMINAL
  Scénario: Consignation nominale d'une hypothèse rejetée dans le registre
    Étant donné un projet client actif et un motif de rejet architectural
    Quand l'agent enregistre l'hypothèse via record_rejected_hypothesis
    Alors l'entrée est ajoutée au fichier rho_impact.yaml
    Et la consultation get_rejected_hypotheses retourne l'élément consigné

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Détection et avertissement sur mot-clé déjà rejeté
    Étant donné un mot-clé préalablement enregistré dans le registre des rejets
    Quand une nouvelle tentative d'optimisation porte sur ce même mot-clé
    Alors le moteur émet un avertissement d'anti-amnésie WikiSkill

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Bifurcation mécanique déterministe préservant le contexte LLM
    Étant donné une consigne portant sur la compaction de commentaires ou chaînes
    Quand l'optimisation RHO est exécutée
    Alors la règle est automatiquement bifurquée vers deterministic_rules.json
    Et aucun jeton de prompt n'est gaspillé pour une règle mécanique

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Collecteur nocturne Dream Collector marquant les règles obsolètes
    Étant donné des règles RHO actives contredites par un nouvel ADR
    Quand le Dream Collector est exécuté
    Alors les règles concernées passent au statut TOMBSTONE avec mention explicite du motif
```
