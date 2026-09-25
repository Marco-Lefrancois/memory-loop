---
id: MLOOP-002-BE
jira_key: '-'
epic_key: EPIC-1-CORE-LOOP
type: Feature
title: Orchestrateur Asymétrique et Routage Système 2 vs Système 1
tags: [core, orchestrator, asymmetric-routing, system1, system2]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-1-CORE-LOOP] Orchestrateur Asymétrique et Routage Système 2 vs Système 1 (MLOOP-002-BE)

---

## Description
**En tant que** Noyau du Framework mLoop,  
**je veux** disposer d'un orchestrateur hybride asymétrique,  
**afin de** router automatiquement les tâches sémantiques de haut niveau (SPEC, PLAN) vers le Système 2 (LLM Cloud à fort budget de réflexion) et les tâches de validation et d'exécution (BUILD, VALIDATE, SHIP) vers le Système 1 (Automates locaux déterministes).

---

## Contexte & Périmètre

### Contexte Métier
mLoop repose sur une séparation hermétique entre la réflexion cognitive (Système 2) et l'exécution mécanique (Système 1). Ce récit implémente l'orchestrateur central distribuant les traitements selon la phase active du `LoopState`, en s'appuyant sur une structure de classes d'agents réutilisables.

### In-Scope
- Classe `AsymmetricOrchestrator` exposant `execute_step(state: LoopState) -> LoopState`.
- Routage conditionnel strict basé sur `current_phase`.
- Interdiction des appels LLM durant les phases déterministes.
- Suite de tests unitaire de routage.

### Out-of-Scope
- Orchestration distribuée multi-clusters.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Routage Dynamique par Phase
* **Entrée Métier** : Instance de `LoopState` avec phase active (`SPEC`, `PLAN`, `BUILD`, `VALIDATE`, `SHIP`).
* **Règles d'admissibilité & Validation** : Respect strict du cloisonnement : Système 2 réservé à SPEC/PLAN, Système 1 pour les phases mécaniques.
* **Traitement & Algorithme Métier** : Aiguillage vers l'agent dérivé de `BaseAgent` et exécution synchrone.
* **Résultat Métier & Mutations** : Mise à jour de l'état et consignation dans le journal d'activité.
* **Cas de Rejet Métier** : Transition en phase ERROR en cas de défaillance non rattrapée de l'agent.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Orchestrateur Asymétrique et Routage Système 2 vs Système 1

  # CHEMIN NOMINAL
  Scénario: Routage Système 2 en phase de Spécification
    Étant donné un état LoopState initialisé à la phase SPEC
    Et un orchestrateur configuré avec un agent Système 2
    Quand l'orchestrateur exécute l'étape
    Alors la tâche est routée vers l'agent Système 2
    Et l'activité est consignée dans le journal de l'état

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Fallback en phase ERROR lors d'un échec de l'agent
    Étant donné un état LoopState en phase SPEC
    Et un agent Système 2 qui lève une exception non gérée
    Quand l'orchestrateur exécute l'étape
    Alors l'orchestrateur intercepte l'erreur et bascule l'état en ERROR
    Et le message d'erreur est archivé dans le journal

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Routage Système 1 déterministe en phase de Validation
    Étant donné un état LoopState initialisé à la phase VALIDATE
    Quand l'orchestrateur exécute l'étape
    Alors aucun appel LLM externe n'est déclenché
    Et la validation est prise en charge par l'automate local Système 1

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Traçabilité du temps d'exécution par étape
    Étant donné l'exécution d'une étape par l'orchestrateur
    Quand l'étape se termine avec succès
    Alors le temps d'exécution en millisecondes est journalisé
    Et la trace d'activité est visible dans le rapport d'état
```
