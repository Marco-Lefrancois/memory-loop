---
id: MLOOP-013-BE
jira_key: '-'
epic_key: EPIC-2-HYBRID-MEMORY
type: Feature
title: Démon de Préchargement d'Engrammes Asynchrone
tags: [memory, preloader, engrams, cache, ram, performance]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-2-HYBRID-MEMORY] Démon de Préchargement d'Engrammes Asynchrone (MLOOP-013-BE)

---

## Description
**En tant que** Moteur d'Orchestration mLoop,  
**je veux** précharger de manière asynchrone les clusters de la mémoire sémantique en RAM lors du changement de contexte actif,  
**afin d'** annuler la latence d'accès disque lors de la phase de réflexion de l'agent.

---

## Contexte & Périmètre

### Contexte Métier
Inspiré par le concept d'Offloading de DSpark, ce récit vise à optimiser l'accès au graphe de connaissances. Lorsqu'un récit passe à l'état actif, le démon interroge la mémoire pour précharger en cache RAM les engrammes liés (fichiers, concepts, règles d'exclusion).

### In-Scope
- Fonctions `preload_story_context` et `clear_preloaded_context`.
- Auto-recall passif sémantique dans la mémoire SQLite.
- Plafonnement du cache en mémoire et éviction explicite.
- Suite de tests unitaire de préchargement.

### Out-of-Scope
- Clustering multi-nœuds en mémoire partagée réseau.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Préchargement d'Engrammes en Mémoire
* **Entrée Métier** : Identifiant de la story active (`story_id`) et nom du projet.
* **Règles d'admissibilité & Validation** : Présence du graphe de connaissances ou de la base d'observations du projet.
* **Traitement & Algorithme Métier** : Résolution 1-hop dans le graphe et stockage dans `_PRELOAD_CACHE`.
* **Résultat Métier & Mutations** : Rétention en RAM des nœuds sémantiques et métadonnées associées.
* **Cas de Rejet Métier** : Traitement gracieux en mode dégradé si le graphe est vide ou indisponible.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Démon de Préchargement d'Engrammes Asynchrone

  # CHEMIN NOMINAL
  Scénario: Préchargement réussi des nœuds de graphe en RAM
    Étant donné une story active et un graphe de connaissances contenant 10 nœuds
    Quand le démon exécute preload_story_context
    Alors les nœuds pertinents sont mis en cache RAM
    Et le statut retourné confirme le nombre d'engrammes préchargés

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Purge du cache lors du changement de récit
    Étant donné un cache mémoire contenant des engrammes d'une story terminée
    Quand clear_preloaded_context est déclenché
    Alors la clé correspondante est supprimée de la mémoire
    Et l'espace mémoire est libéré

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Tolérance en l'absence de graphe de connaissances
    Étant donné un projet vierge sans fichier knowledge_graph.json
    Quand le préchargement est sollicité
    Alors le démon retourne 0 nœuds préchargés sans lever d'erreur
    Et le système poursuit son cycle normalement

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Télémétrie de la consommation mémoire du cache
    Étant donné l'exécution du préchargement en mémoire vive
    Quand la réponse du démon est inspectée
    Alors le volume de mémoire consommée en kilo-octets est retourné
    Et le décompte d'auto-recall est affiché
```
