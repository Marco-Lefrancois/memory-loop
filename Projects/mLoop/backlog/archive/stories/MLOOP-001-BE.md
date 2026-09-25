---
id: MLOOP-001-BE
jira_key: '-'
epic_key: EPIC-1-CORE-LOOP
type: Feature
title: Moteur d'état LoopState et Transitions de Phases Pydantic v2
tags: [core, state-machine, pydantic, loop-state]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-1-CORE-LOOP] Moteur d'état LoopState et Transitions de Phases Pydantic v2 (MLOOP-001-BE)

---

## Description
**En tant que** Noyau du Framework mLoop,  
**je veux** disposer d'un moteur d'état typé et validé via Pydantic v2,  
**afin d'** interdire les transitions d'états incohérentes et garantir la robustesse du cycle Spec-Plan-Build-Validate-Ship.

---

## Contexte & Périmètre

### Contexte Métier
Le moteur d'état mLoop orchestre le flux cognitif des agents. Sans validation stricte des transitions, le système risque la dérive stochastique ou des boucles de rétroaction infinies. Ce récit implémente l'énumération des phases (`LoopPhase`), les schémas de résultats de chaque phase, et le contrôle transactionnel des transitions dans `LoopState`.

### In-Scope
- Modèle `LoopState` sous Pydantic v2.
- Validation transactionnelle de phase et graphe d'adjacence autorisé.
- Disjoncteur de boucle infinie sur révisions multiples (seuil de 5 révisions).
- Suite de tests unitaires de transition d'état.

### Out-of-Scope
- Persistence multi-noeuds distribuée.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Contrôle des Transitions d'États
* **Entrée Métier** : État actuel du projet et phase cible demandée (`next_phase`).
* **Règles d'admissibilité & Validation** : Vérification de l'adjacence autorisée selon le graphe des phases (SPEC vers PLAN, PLAN vers VALIDATE, etc.).
* **Traitement & Algorithme Métier** : Méthode `can_transition_to` et `validate_integrity` validant la présence des artefacts requis.
* **Résultat Métier & Mutations** : Mutation de la phase active vers la nouvelle phase et archivage de l'ancienne phase.
* **Cas de Rejet Métier** : Rejet immédiat avec `IntegrityError` si l'artefact prérequis est manquant ou si la transition est interdite.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur d'état LoopState et Transitions de Phases Pydantic v2

  # CHEMIN NOMINAL
  Scénario: Transition nominale de Spec vers Plan
    Étant donné un état initialisé à la phase SPEC
    Et un artefact d'analyse AnalysisResult valide et complet
    Quand la transition vers la phase PLAN est déclenchée
    Alors l'état passe avec succès à la phase PLAN
    Et la phase précédente est enregistrée à SPEC

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet de transition vers Plan si l'analyse est absente
    Étant donné un état initialisé à la phase SPEC sans artefact d'analyse
    Quand la transition vers la phase PLAN est tentée
    Alors la transition est refusée
    Et une erreur d'intégrité de type IntegrityError est levée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Circuit breaker après dépassement du seuil de 5 révisions
    Étant donné un état à la phase VALIDATE ayant déjà accumulé 5 révisions
    Quand un retour à la phase PLAN est tenté avec une nouvelle révision
    Alors l'état est forcé à la phase ERROR
    Et une exception MaxRevisionsReached est propagée

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Journalisation explicite lors d'un basculement d'état
    Étant donné un état LoopState configuré
    Quand une transition valide est exécutée
    Alors un événement horodaté est consigné dans le journal de session
    Et l'historique des phases précédentes est préservé
```
