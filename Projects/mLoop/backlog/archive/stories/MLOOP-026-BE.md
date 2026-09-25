---
id: MLOOP-026-BE
jira_key: '-'
epic_key: EPIC-3-SAFETY-GOVERNANCE
type: Feature
title: Infrastructure de Désapprentissage Agentique
tags: [unlearning, rho, safety, knowledge-graph, cascade]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-3-SAFETY-GOVERNANCE] Infrastructure de Désapprentissage Agentique (MLOOP-026-BE)

---

## Description
**En tant que** Responsable Qualité / Moteur,  
**je veux** exécuter la purge ordonnée d'un concept et la désactivation en cascade de ses règles dérivées via le moteur de désapprentissage,  
**afin de** garantir qu'un concept obsolète ou révoqué est éliminé sans corrompre l'intégrité du graphe de connaissances ni propager de règles invalides.

---

## Contexte & Périmètre

### Contexte Métier
Le désapprentissage agentique (Agentic Unlearning) permet d'éliminer des connaissances devenues fausses ou préjudiciables sans déstabiliser le système complet. Lorsqu'une décision d'architecture (ADR) ou une règle métier est révoquée, le pipeline purge le nœud dans le graphe sémantique local et désactive en cascade toutes les règles de garde RHO correspondantes, garantissant une cohérence stricte.

### In-Scope
- Pipeline de désapprentissage `src/pipelines/unlearn.py` (`run_unlearn`).
- Suppression ciblée du concept dans `knowledge_graph.json`.
- Nettoyage des arêtes orphelines attachées au concept révoqué.
- Désactivation des règles RHO dépendantes dans `rho_rules.yaml`.
- Suite de tests unitaire `tests/test_unlearning.py`.

### Out-of-Scope
- Fine-tuning ou ré-entraînement de modèles de fondation externes.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Désapprentissage Cascade et Dépréciation de Règles
* **Entrée Métier** : Nom du projet mLoop et identifiant textuel du concept à désapprendre.
* **Règles d'admissibilité & Validation** : Le projet doit exister avec un répertoire mémoire contenant le graphe de connaissances.
* **Traitement & Algorithme Métier** : Recherche du concept dans `knowledge_graph.json`, suppression du nœud et de ses arêtes incidentes, puis filtrage et mise à jour des règles dans `rho_rules.yaml`.
* **Résultat Métier & Mutations** : Dictionnaire récapitulant le statut de purge, le nombre de nœuds retirés et le nombre de règles RHO désactivées.
* **Cas de Rejet Métier** : Projet inexistant ou concept introuvable dans le référentiel des connaissances actives.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Infrastructure de Désapprentissage Agentique

  # CHEMIN NOMINAL
  Scénario: Désapprentissage réussi d'un concept obsolète avec cascade
    Étant donné un graphe contenant un concept obsolète lié à une règle RHO
    Quand le pipeline de désapprentissage est exécuté sur ce concept
    Alors le nœud et ses liaisons sont supprimés du graphe de connaissances
    Et la règle RHO associée est retirée du référentiel actif

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Tentative de purge sur un concept inexistant
    Étant donné un graphe sans occurrence du concept cible
    Quand l'ordre de désapprentissage est transmis
    Alors aucun nœud n'est altéré
    Et le résultat indique zéro suppression effectuée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Préservation des concepts sains non impactés
    Étant donné un graphe comportant des concepts valides aux côtés du concept révoqué
    Quand le désapprentissage en cascade termine son cycle
    Alors l'ensemble des concepts sains et leurs règles associées sont rigoureusement préservés

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Rapport d'audit de désapprentissage explicite
    Étant donné la complétion d'une opération de désapprentissage
    Quand le résultat d'exécution est retourné
    Alors le rapport détaille le statut, le concept ciblé et le décompte exact des mutations
```
