---
id: MLOOP-025-BE
jira_key: '-'
epic_key: EPIC-3-SAFETY-GOVERNANCE
type: Feature
title: Suite d'Évaluation de Gouvernance AOEP-v0
tags: [governance, aoep, safety, evaluation, invariants]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-3-SAFETY-GOVERNANCE] Suite d'Évaluation de Gouvernance AOEP-v0 (MLOOP-025-BE)

---

## Description
**En tant que** Responsable Qualité / Moteur,  
**je veux** exécuter la suite de tests AOEP-v0 (Always-On Evaluation Protocol),  
**afin d'** évaluer la capacité du système à gérer la temporalité, l'oubli et le respect des invariants négatifs et frontières du Story Constraint Contract (SCC) sur la durée.

---

## Contexte & Périmètre

### Contexte Métier
Les benchmarks IA traditionnels mesurent l'acuité immédiate, mais ignorent la gouvernance (expiration de permissions, propagations d'oubli, rollbacks). Cette fonctionnalité valide l'étanchéité de l'arc arrière de persistance, garantissant que les agents mLoop obéissent à leurs limites dans le temps et n'agissent jamais sur des informations révoquées ou en dehors de leur périmètre de composants autorisé.

### In-Scope
- Suite de tests unitaire `tests/test_aoep_governance.py`.
- Validation de la frontière d'obligation par le Story Guard (`test_obligation_pass_boundary_rejection`).
- Cécité garantie face aux faits purgés (`test_negative_invariant_blindness`).
- Idempotence du rechargement de l'état système (`test_crash_recovery_idempotency`).

### Out-of-Scope
- Évaluation qualitative subjective des réponses conversationnelles du LLM.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Évaluation des Invariants de Gouvernance et Bornes d'Obligation
* **Entrée Métier** : Identifiant de projet mLoop et fichier cible soumis à modification par un agent.
* **Règles d'admissibilité & Validation** : Le fichier cible doit impérativement figurer dans la liste des composants approuvés de la story en cours d'analyse.
* **Traitement & Algorithme Métier** : Vérification stricte des autorisations SCC via `Story Guard`, contrôle d'absence totale d'entités révoquées dans le cache mémoire en mémoire vive, et chargement idempotent de l'état de boucle.
* **Résultat Métier & Mutations** : Autorisation d'accès accordée ou interruption immédiate du processus avec code de sortie d'échec.
* **Cas de Rejet Métier** : Rejet immédiat si le composant n'est pas autorisé ou si une référence à un concept purgé est détectée.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Suite d'Évaluation de Gouvernance AOEP-v0

  # CHEMIN NOMINAL
  Scénario: Validation des invariants de gouvernance et conformité d'accès
    Étant donné un composant déclaré dans le périmètre autorisé de la story active
    Quand le Story Guard évalue la demande d'écriture
    Alors l'accès est formellement autorisé sans exception

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet strict d'écriture hors composant autorisé
    Étant donné un composant non enregistré dans le contrat SCC de la story
    Quand l'agent tente une opération de modification
    Alors le Story Guard rejette l'opération et interrompt l'exécution

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Idempotence de la restauration après crash système
    Étant donné un état système persisté sur disque
    Quand deux restaurations successives sont déclenchées
    Alors les états résultants sont rigoureusement identiques et intègres

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Cécité totale aux concepts révoqués dans le cache mémoire
    Étant donné la purge complète du cache préchargé en mémoire
    Quand une recherche d'entités est exécutée
    Alors aucun concept révoqué n'est retourné et le cache demeure vide
```
