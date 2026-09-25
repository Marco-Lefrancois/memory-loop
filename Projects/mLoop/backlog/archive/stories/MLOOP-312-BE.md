---
id: MLOOP-312-BE
jira_key: MLOOP-312-BE
epic_key: EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION
type: Feature
title: "Graphe de Transitions Déterministe & Auto-Clôture Gate 5 sans Validation Humaine"
tags: [core, fsm, lifecycle, gates, automation, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0391-§3"
macro_size: M
blocked_by: [MLOOP-310-BE, MLOOP-311-BE]
created_at: "2026-09-25T04:35:00Z"
updated_at: "2026-09-25T05:08:00Z"
---

# Graphe de Transitions Déterministe & Auto-Clôture Gate 5 sans Validation Humaine

---

## Description
**En tant qu'** orchestrateur du cycle de vie mLoop,  
**je veux** un graphe `ALLOWED_TRANSITIONS` aligné sur le flux déterministe à 5 phases (`IN_DEV ➔ READY_FOR_QA ➔ QA_CERTIFIED ➔ DONE`) et une Gate 5 entièrement automatisée (`requires_human: False`) sans confirmation humaine redondante lorsque tous les feux sont au vert,  
**afin de** fluidifier la chaîne d'intégration continue, éliminer les blocages manuels superflus et respecter le principe Zero Fluff.

---

## Contexte & Périmètre

### Contexte Métier
L'ancienne machine à états mLoop comportait une contradiction logique majeure : autoriser la transition directe de `IN_DEV` à `DONE_TESTED` avant même que la suite de qualification de sprint (Phase 4 : VALIDATE) ne soit jouée. De plus, la Gate 5 (Phase 5 : SHIP & SYNC) imposait jusqu'alors une validation humaine manuelle (`requires_human: True`), obligeant l'humain à valider passivement une livraison alors que 100% des tests pré-vol, linters et contrôles de sécurité étaient déjà automatisés et verts.  
Lors du Macro-Grill du 25/09/2026, le PO a acté le nouveau flux unifié, la rétrogradation directe vers `IN_DEV` en cas d'échec de la qualification QA, et la clôture 100% autonome de la Gate 5 vers `DONE`.

### In-Scope
- Mise à jour du graphe canonique `ALLOWED_TRANSITIONS` dans `src/pipelines/state_machine.py` :
  - `READY_FOR_DEV` ➔ `[IN_DEV, IN_REVIEW, ON_HOLD]`
  - `IN_DEV` ➔ `[READY_FOR_QA, DONE_TESTED, IN_REVIEW, ON_HOLD, ERROR]` (maintien passerelle `DONE_TESTED`)
  - `READY_FOR_QA` ➔ `[QA_CERTIFIED, IN_DEV, IN_REVIEW, ON_HOLD, ERROR]` (rétrogradation directe vers `IN_DEV`)
  - `QA_CERTIFIED` ➔ `[READY_TO_SHIP, DONE, SHIPPED, IN_REVIEW, IN_DEV]`
  - `READY_TO_SHIP` ➔ `[DONE, SHIPPED, IN_REVIEW]`
  - `DONE` et `SHIPPED` ➔ `[IN_REVIEW, IN_ANALYZE]` (réouverture exceptionnelle)
- Mise à jour de `GATE_DEFINITIONS[5]["requires_human"] = False` dans `src/core/lifecycle/_lc_models.py`.
- Autorisation de l'auto-clôture vers `DONE` par l'agent/pipeline de release lorsque le bilan pré-vol est vierge de tout échec (0 FAIL).

### Out-of-Scope
- Refactorisation des expressions régulières de parsing du backlog (couverte par `MLOOP-313-BE`).
- Rédaction de l'ADR formelle (couverte par `MLOOP-314-FULL`).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — La transition `IN_DEV ➔ READY_FOR_QA` est autorisée par la FSM sans erreur.
> - [x] **CA-2** — La transition `READY_FOR_QA ➔ QA_CERTIFIED` est autorisée par la FSM suite au passage de `validate-sprint`.
> - [x] **CA-3** — En cas d'échec de la certification QA, la transition rétrograde `READY_FOR_QA ➔ IN_DEV` est autorisée.
> - [x] **CA-4** — La transition `QA_CERTIFIED ➔ DONE` est autorisée de manière 100% autonome par la FSM.
> - [x] **CA-5** — `GATE_DEFINITIONS[5]["requires_human"]` est configuré à `False`.
> - [x] **CA-6** — Tout saut illégitime (ex: `DRAFT ➔ READY_FOR_QA` ou `IN_ANALYZE ➔ DONE`) lève immédiatement `StateTransitionError`.

### Opérations Métier & Logique Backend

#### 1. Validation de Transition — `validate_transition(current_status, target_status)`
* **Entrée Métier** : Statut d'origine et statut de destination souhaité.
* **Règles d'admissibilité & Validation** : La paire `(current_status, target_status)` doit appartenir à `ALLOWED_TRANSITIONS`.
* **Traitement & Algorithme Métier** :
  1. Résoudre les énumérateurs `StoryStatus`.
  2. Vérifier la présence de `target_status` dans la liste autorisée pour `current_status`.
  3. Si la transition est absente, lever `StateTransitionError` avec journalisation explicite.
* **Résultat Métier & Mutations** : Autorisation de passage de statut.
* **Cas de Rejet Métier** : Sauts de phase non autorisés.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)

#### Matrice des Contrats API
- **OQ-312 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — moteur de graphe de transitions et règles de validation de portes internes (`src/pipelines/state_machine.py`, `src/core/lifecycle/_lc_models.py`), sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

---

## Règles d'affaires

- **Séquentialité Inviolable des 5 Phases** : Un récit ne peut sauter une phase canonique. Il doit obligatoirement être certifié par la QA (Phase 4) avant d'être éligible à la clôture finale `DONE` (Phase 5).
- **Zero Fluff Delivery** : Dès lors que tous les tests unitaires, d'intégration, de sécurité et d'intégrité sont au vert, l'auto-livraison ne requiert aucune approbation humaine manuelle.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-312-BE_fact_dossier.md`](../../memory/evidence/MLOOP-312-BE_fact_dossier.md)
- ⚖️ **Épopée Cadre** : [`backlog/epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md`](../epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Moteur de Machine à États** : [`src/pipelines/state_machine.py`](../../../src/pipelines/state_machine.py)
- 📜 **Modèles de Cycle de Vie** : [`src/core/lifecycle/_lc_models.py`](../../../src/core/lifecycle/_lc_models.py)
- 📜 **Décision d'Architecture** : [ADR-0391 — Harmonisation Cycle de Vie 5 Phases](../../standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Graphe de Transitions Déterministe & Auto-Clôture Gate 5 sans Validation Humaine

  # CHEMIN NOMINAL (Happy Path & Clôture 5 Phases)
  Scénario: Déroulement nominal complet du cycle des 5 phases jusqu'à la clôture automatique
    Étant donné un récit au statut READY_FOR_DEV
    Quand le récit progresse successivement par IN_DEV, READY_FOR_QA et QA_CERTIFIED
    Alors chaque transition intermédiaire est autorisée sans blocage
    Et le passage final de QA_CERTIFIED à DONE s'effectue automatiquement sans exiger de confirmation humaine

  # EXCEPTIONS & REJETS (Sauts illégitimes)
  Scénario: Rejet immédiat d'un saut de phase illicite
    Étant donné un récit au statut DRAFT ou IN_ANALYZE
    Quand une transition directe vers DONE ou READY_FOR_QA est tentée
    Alors une exception StateTransitionError est levée
    Et le statut du récit demeure inchangé

  # RÉSILIENCE TECHNIQUE (Rétrogradation directe sur échec QA)
  Scénario: Rétrogradation directe de READY_FOR_QA vers IN_DEV lors d'un échec de test
    Étant donné un récit au statut READY_FOR_QA soumis à la qualification QA
    Quand les tests de non-régression subissent un échec ou un timeout
    Alors la FSM autorise la rétrogradation immédiate vers IN_DEV sans délai d'attente
    Et le développeur peut corriger le code sans réouvrir une session Sentinel

  # UX & OBSERVABILITÉ (Audit de Gate 5 autonome)
  Scénario: Validation de Gate 5 autonome sans blocage de nom d'agent ni champ vide
    Étant donné la suite de validation pré-vol exécutée avec 100% de succès
    Quand Gate 5 est évaluée
    Alors requires_human est évalué à Faux sans valeur null ni champ vide
    Et la transition vers DONE est scellée dans les journaux sans token expiré
```
