---
id: MLOOP-310-BE
jira_key: MLOOP-310-BE
epic_key: EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION
type: Feature
title: "Unification du Modèle d'États StoryStatus & Rétrocompatibilité Tolérante"
tags: [core, state, lifecycle, typing, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0390-§1"
macro_size: S
blocked_by: []
created_at: "2026-09-25T04:35:00Z"
updated_at: "2026-09-25T04:44:00Z"
---

# Unification du Modèle d'États StoryStatus & Rétrocompatibilité Tolérante

---

## Description
**En tant que** développeur framework et moteur de cycle de vie mLoop,  
**je veux** disposer d'un modèle d'états `StoryStatus` unifié intégrant `READY_FOR_QA`, `QA_CERTIFIED` et `READY_TO_SHIP` avec un parsing tolérant et sans duplication de chaînes brutes,  
**afin d'** aligner rigoureusement la taxonomie des récits sur les 5 phases officielles mLoop tout en sanctuarisant la rétrocompatibilité des anciens statuts (`DONE_TESTED`, `SHIPPED`).

---

## Contexte & Périmètre

### Contexte Métier
Le cycle de vie des récits au sein du framework mLoop structure le travail des agents et des humains en 5 phases universelles (ADR-0375) : Ingest, Plan, Build, Validate, Ship.  
Auparavant, le noyau d'état (`src/state/_state_core.py`) présentait une dichotomie artificielle entre un mode "Client" et un mode "mLoop", privant le framework d'états formels pour les phases 4 (Validate / QA) et 5 (Ship). De plus, l'ensemble `_GRILLED_STATUSES` reposait sur des chaînes de caractères littérales déconnectées de l'enum et omettait le statut terminal `SHIPPED`.  
Lors de la session Grill-Me 1:1 du 25/09/2026, le Product Owner a acté le maintien strict de `DONE_TESTED` et `SHIPPED` dans l'énumérateur afin de préserver l'inviolabilité des 91 récits archivés sans migration destructive, tout en intégrant les nouveaux membres requis pour le pipeline moderne.

### In-Scope
- Ajout des membres d'énumération `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP` dans `StoryStatus` (`src/state/_state_core.py`).
- Conservation formelle de `DONE_TESTED` et `SHIPPED` au sein de `StoryStatus` pour garantir une compatibilité ascendante sans faille.
- Remplacement du set de chaînes brutes `_GRILLED_STATUSES` par une collection typée s'appuyant directement sur `StoryStatus` et intégrant les nouveaux statuts ainsi que `SHIPPED` et `DONE`.
- Sécurisation de la méthode de classe `StoryStatus.from_raw(raw: str)` : normalisation insensible à la casse, gestion des tirets et espaces, et repli défensif fail-open sur `StoryStatus.OPEN`.
- Alignement des propriétés `grilled` et `jira_sync_eligible` de `SprintBacklogItem`.
- Enrichissement de la suite de tests unitaires `tests/test_story_status.py`.

### Out-of-Scope
- Modification de la table de transition FSM `ALLOWED_TRANSITIONS` (couverte par `MLOOP-312-BE`).
- Nettoyage du hardcoding des verticaux clients dans `state_machine.py` (couvert par `MLOOP-311-BE`).
- Mise à niveau des expressions régulières de synchronisation Markdown (couverte par `MLOOP-313-BE`).
- Formalisation normative de l'ADR (couverte par `MLOOP-314-FULL`).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — L'enum `StoryStatus` expose explicitement les constantes `READY_FOR_QA`, `QA_CERTIFIED` et `READY_TO_SHIP`.
> - [x] **CA-2** — L'appel `StoryStatus.from_raw()` parse avec succès toutes les variantes de casse et de formatage des nouveaux statuts (ex: `"ready-for-qa"` ➔ `StoryStatus.READY_FOR_QA`).
> - [x] **CA-3** — `StoryStatus.from_raw("DONE_TESTED")` retourne exactement `StoryStatus.DONE_TESTED` sans mutation sémantique.
> - [x] **CA-4** — `StoryStatus.from_raw("SHIPPED")` retourne exactement `StoryStatus.SHIPPED`.
> - [x] **CA-5** — `_GRILLED_STATUSES` intègre `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP`, `DONE` et `SHIPPED`.
> - [x] **CA-6** — Pour un `SprintBacklogItem` instancié avec un de ces nouveaux statuts, `item.grilled` et `item.jira_sync_eligible` retournent `True`.
> - [x] **CA-7** — 100% des tests de `tests/test_story_status.py` sont au vert sans régression sur les statuts historiques.

### Opérations Métier & Logique Backend

#### 1. Parsing & Normalisation — `StoryStatus.from_raw(raw: str) -> StoryStatus`
* **Entrée Métier** : Chaîne brute issue du frontmatter YAML d'un fichier de récit ou d'une cellule de table Markdown.
* **Règles d'admissibilité & Validation** : Entrée non nulle ; si vide ou inconnue, repli déterministe sur `StoryStatus.OPEN`.
* **Traitement & Algorithme Métier** :
  1. Nettoyage des espaces de tête et queue (`strip()`).
  2. Passage en majuscules (`upper()`).
  3. Remplacement des espaces et tirets par des underscores (`replace(" ", "_").replace("-", "_")`).
  4. Résolution de l'instance d'enum correspondante. En cas de `ValueError`, retour de `StoryStatus.OPEN`.
* **Résultat Métier & Mutations** : Instance typée de `StoryStatus`.
* **Cas de Rejet Métier** : Aucun crash (fail-open garanti).

#### 2. Évaluation de Maturation — `SprintBacklogItem.grilled` et `jira_sync_eligible`
* **Entrée Métier** : Instance de `SprintBacklogItem`.
* **Règles d'admissibilité & Validation** : Le statut du récit doit appartenir à `_GRILLED_STATUSES`.
* **Traitement & Algorithme Métier** : Vérification de présence du statut dans la collection `_GRILLED_STATUSES`.
* **Résultat Métier & Mutations** : Booléen `True` si post-Gate 2, `False` sinon.
* **Cas de Rejet Métier** : Récits en `DRAFT`, `OPEN`, `IN_ANALYZE`, `IN_PLAN`, `ON_HOLD`, `ERROR` retournent `False`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)

#### Matrice des Contrats API
- **OQ-310 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — composant de modélisation d'état pur en mémoire Python (`src/state/_state_core.py`), sans interface HTTP ni route REST distante `[API de soumission à définir]` ; toute interaction s'effectue via les types Python internes `StoryStatus` et `SprintBacklogItem` (ADR-0319).

---

## Règles d'affaires

- **Inviolabilité de l'Historique des Récits** : Les statuts historiques `DONE_TESTED` et `SHIPPED` doivent continuer d'être reconnus et manipulés sans altération pour garantir l'intégrité des 91 récits archivés de mLoop.
- **Fail-Open au Parsing de Statut** : Tout statut inconnu ou corrompu dans un fichier Markdown doit retomber silencieusement sur `StoryStatus.OPEN` afin de ne jamais bloquer le démarrage de l'orchestrateur.
- **Cohérence des Statuts Post-Grooming** : Dès qu'un récit entre en phase de développement ou de qualification (`IN_DEV`, `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP`, `DONE`), il est considéré comme "grillé" et éligible à la réconciliation Jira.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-310-BE_fact_dossier.md`](../../memory/evidence/MLOOP-310-BE_fact_dossier.md)
- ⚖️ **Épopée Cadre** : [`backlog/epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md`](../epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Noyau d'État SSOT** : [`src/state/_state_core.py`](../../../src/state/_state_core.py)
- 📜 **Protocole de Cycle de Vie** : [`standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`](../../../standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)
- 📜 **Décision d'Architecture** : [ADR-0390 — Harmonisation Cycle de Vie 5 Phases](../../standards/adr-system/0390-harmonisation-cycle-de-vie-recits-5-phases.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Unification du Modèle d'États StoryStatus & Rétrocompatibilité Tolérante

  # CHEMIN NOMINAL (Happy Path & Nouveaux Statuts)
  Scénario: Résolution nominale des nouveaux statuts du cycle 5 phases
    Étant donné une chaîne de caractères représentant un nouveau statut "READY_FOR_QA", "QA_CERTIFIED" ou "READY_TO_SHIP"
    Quand StoryStatus.from_raw est invoqué avec cette chaîne
    Alors l'énumérateur correspondant est retourné
    Et un élément de backlog associé à ce statut possède la propriété grilled à Vrai
    Et cet élément est déclaré éligible à la synchronisation Jira

  # EXCEPTIONS & TOLÉRANCE DE FORMATAGE (Règles d'affaires)
  Scénario: Normalisation tolérante de variantes textuelles avec casse et séparateurs
    Étant donné une chaîne de caractères brute comportant des minuscules, des espaces ou des tirets comme "ready for qa" ou "qa-certified"
    Quand StoryStatus.from_raw est invoqué avec cette variante
    Alors le statut est normalisé et résolu sans erreur vers l'énumérateur cible
    Et aucune exception n'est levée

  # RÉSILIENCE TECHNIQUE & RÉTROCOMPATIBILITÉ (Anciens Récits, Délai d'attente et Concurrence)
  Scénario: Préservation stricte des statuts historiques DONE_TESTED et SHIPPED sous concurrence
    Étant donné un récit historique du backlog archivé portant le statut "DONE_TESTED" ou "SHIPPED"
    Et plusieurs threads accédant simultanément au parsing sans délai d'attente excessif ni timeout
    Quand StoryStatus.from_raw parse ce statut
    Alors StoryStatus.DONE_TESTED ou StoryStatus.SHIPPED est strictement retourné
    Et l'historique des 91 récits archivés n'est pas altéré
    Et la propriété grilled reste à Vrai

  # UX & FAIL-OPEN (Statuts inconnus, données partielles et valeurs nulles)
  Scénario: Repli défensif fail-open sur valeur de statut corrompue, champ vide ou valeur null
    Étant donné une entrée constituée d'un champ vide, de données partielles ou d'une valeur null
    Quand StoryStatus.from_raw est exécuté
    Alors le statut par défaut StoryStatus.OPEN est retourné
    Et le système poursuit son traitement sans interrompre l'orchestrateur
    Et aucun jeton ou token expiré d'authentification n'interfère avec ce calcul local
```
