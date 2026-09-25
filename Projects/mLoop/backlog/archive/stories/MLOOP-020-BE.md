---
id: MLOOP-020-BE
jira_key: '-'
epic_key: EPIC-3-SAFETY-GOVERNANCE
type: Feature
title: Verrou Physique Story Guard et Confinement d'Écriture SCC
tags: [safety, story-guard, scc, boundary, confinement]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-3-SAFETY-GOVERNANCE] Verrou Physique Story Guard et Confinement d'Écriture SCC (MLOOP-020-BE)

---

## Description
**En tant que** Gardien de Sécurité et Sentinelle d'Intégrité de Phase 3 (Build),  
**je veux** disposer d'un middleware de validation déterministe (`validate_story_state`) interceptant tout accès d'écriture de fichier,  
**afin d'** interdire physiquement toute mutation de code ou d'artefact en dehors du périmètre strict des composants déclarés dans le Story Constraint Contract (SCC) du récit actif.

---

## Contexte & Périmètre

### Contexte Métier
En Phase 3, un agent de développement autonome peut involontairement corrompre des modules tiers s'il ne respecte pas le contrat de délimitation (SCC). Le composant `src/bridges/story_guard.py` garantit un confinement physique en validant l'état du graphe, l'unicité du statut de travail et l'appartenance des chemins cibles aux composants autorisés de la story active.

### In-Scope
- Fonction de validation `validate_story_state` dans `src/bridges/story_guard.py`.
- Validation de l'existence de l'état persistant (`graph.json`) du projet.
- Vérification de l'unicité du récit actif ou résolution via variable d'environnement `MLOOP_ACTIVE_STORY_ID`.
- Contrôle d'appartenance du fichier cible (`check_file`) aux composants du SCC de la story active avec rejet immédiat (`sys.exit(1)`).
- Suite de tests unitaire dédiée dans `tests/test_story_guard.py`.

### Out-of-Scope
- Remplacement du disjoncteur financier (géré par `circuit_breaker.py`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Validation de l'État du Récit Actif
* **Entrée Métier** : Nom du projet client et chemin optionnel du fichier cible à modifier.
* **Règles d'admissibilité & Validation** : Présence obligatoire de l'état persistant du projet. Identification formelle d'une story active en cours de cadrage ou de build.
* **Traitement & Algorithme Métier** : Comparaison normalisée insensible à la casse des chemins avec les composants déclarés dans le SCC.
* **Résultat Métier & Mutations** : Autorisation d'accès si le chemin est inclus dans un composant déclaré.
* **Cas de Rejet Métier** : Rejet immédiat et blocage de l'opération si le fichier cible est étranger au SCC.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Verrou Physique Story Guard et Confinement d'Écriture SCC

  # CHEMIN NOMINAL
  Scénario: Autorisation d'écriture d'un fichier inclus dans le composant du SCC
    Étant donné une story active avec composant "src/bridges" déclaré dans son SCC
    Quand l'agent demande la validation d'accès sur "src/bridges/story_guard.py"
    Alors Story Guard autorise l'accès sans lever d'exception

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet bloquant lors d'une tentative d'écriture hors périmètre SCC
    Étant donné une story active restreinte au composant "src/bridges"
    Quand l'agent tente de modifier un fichier non déclaré "src/core/lifecycle.py"
    Alors Story Guard bloque l'accès avec code de sortie d'erreur
    Et affiche la liste des composants autorisés

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Mode tolérant lorsque la story ne déclare aucun composant restrictif
    Étant donné une story active sans liste de composants définie dans son SCC
    Quand la validation d'accès est invoquée
    Alors Story Guard émet un avertissement de contournement et permet la poursuite

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Alerte explicite si aucun récit actif n'est identifié
    Étant donné un projet sans récit au statut de travail actif
    Quand Story Guard est appelé sans fichier spécifique
    Alors un avertissement est émis pour prévenir toute dérive de contexte
```
