---
id: MLOOP-233-BE
jira_key: ""
epic_key: EPIC-23-DATA-HYGIENE-AND-RETENTION
type: Feature
title: "Nettoyage Automatique & Rétention des Artefacts de Session (memory/scratch/, checkpoints)"
tags: [scratch, checkpoints, session, retention, pruning, backend]
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: "Marco (PO)"
validated_at: "2026-09-24"
layer: backend
origin: DIRECT_REQUIREMENT
source_ref: "ADR-015"
macro_size: S
blocked_by: []
created_at: "2026-09-24"
updated_at: "2026-09-24"
---

# 📖 MLOOP-233-BE : Nettoyage Automatique & Rétention des Artefacts de Session (memory/scratch/, checkpoints)

---

## Description
**En tant qu'** Développeur et Agent mLoop,  
**je veux** que les dossiers temporaires de session (`memory/scratch/`, `memory/tmp/`, `memory/compaction/history/`) soient nettoyés automatiquement lors de la clôture des récits (`DONE_TESTED` / `SHIPPED`) ou via `mloop scratch prune`,  
**afin d'** éviter l'accumulation silencieuse de scripts jetables et de prompts orphelins tout en plafonnant les sauvegardes checkpoints à 10 versions.

---

## Contexte & Périmètre

### Contexte Métier
Les exécutions de sous-agents génèrent continuellement des artefacts jetables (`worker_*_prompt.md`, `worker_*_report.md`, scripts de test). Ces fichiers perdent leur utilité opérationnelle une fois le travail validé. L'ADR-015 établit une purge automatique lors de la transition à `DONE_TESTED`, un bornage strict des checkpoints (10 max) et une commande manuelle de maintenance.

### In-Scope
- Handler dédié `src/commands/handlers/scratch_prune.py` (≤ 300L) raccordé au registre CLI.
- Commande `mloop scratch prune [--project <proj>] [--older-than-hours 48] [--all]` :
  - Purge des fichiers résiduels dans `Projects/<proj>/memory/scratch/` et `memory/tmp/`.
  - Conservation obligatoire des artefacts de preuves consolidés sous `memory/evidence/`.
- Hook de transition de cycle de vie :
  - Déclenché lors du passage d'un récit au statut `DONE_TESTED` ou `SHIPPED`.
  - Purge ciblée des fichiers dont le nom contient l'ID du récit clôturé (ex: `worker_*_MLOOP-233-BE_*.md`).
- Rétention des checkpoints de compaction :
  - Plafonnement FIFO à 10 fichiers sous `memory/compaction/history/`.
  - Suppression automatique des plus anciens au-delà de ce quota.

### Out-of-Scope
- Altération ou suppression des dossiers de preuves formelles (`memory/evidence/`).
- Suppression des plans d'architecture archivés sous `memory/plan/`.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — La commande `mloop scratch prune` supprime les artefacts jetables sans toucher aux fichiers de session active.
> - [x] **CA-2** — La transition d'un récit vers `DONE_TESTED` déclenche le nettoyage des fichiers scratch associés.
> - [x] **CA-3** — Le dossier `memory/compaction/history/` ne contient jamais plus de 10 checkpoints après passage de la routine.
> - [x] **CA-4** — Les fichiers sous `memory/evidence/` et `memory/plan/` sont sanctuarisés et jamais altérés.
> - [x] **CA-5** — Le module Python respecte strictement la limite de 300 lignes (ADR-0202).
> - [x] **CA-6** — La suite de tests unitaires sous `tests/test_scratch_prune.py` est au vert avec couverture des hooks de transition.

---

## Spécifications fonctionnelles détaillées

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-233 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — intégration locale et in-process du nettoyeur scratch via Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py scratch prune [--project <name>] [--older-than-hours 48] [--all]`

---

## Règles d'affaires

- **Sanctuarisation des Preuves** : Les répertoires `memory/evidence/` et `memory/plan/` sont strictement protégés et exclus de toute opération de nettoyage scratch.
- **Plafonnement FIFO des Checkpoints** : Exactement 10 checkpoints récents sont conservés sous `memory/compaction/history/`. Tout fichier excédentaire est supprimé par ordre chronologique.
- **Résilience du Hook** : L'échec éventuel de la suppression d'un artefact temporaire ne bloque jamais la transition de statut du récit.
- **Concurrence & Anti-Rebond** : Protection contre les nettoyages concurrents pour éviter les conflits d'accès sur les fichiers en cours d'écriture.
- **Gestion des sessions** : En cas de session CLI interrompue, aucun fichier incomplet n'est laissé dans un état intermédiaire.
- **Contrôle des entrées** : Tout argument d'heures invalide est rejeté avec un message d'aide explicite.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-015)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q4a** | Nettoyage de scratch et rétention des checkpoints | **Option A (Purge au Ship & Quota 10 Checkpoints)** : Purge automatique des résidus jetables `worker_*` à `DONE_TESTED`, et plafonnement FIFO strict à 10 checkpoints. | [ADR-015](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cadrage de la purge de scratch et du quota de 10 checkpoints validé.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-233 formalisée et sanctuarisation evidence garantie.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Raccordement au hook de transition de statut du state machine.
- [x] **Estimations et découpage validés** : Taille S (1 à 2 jours), code ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q4a scellé dans l'ADR-015.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-233-BE_fact_dossier.md`](../../memory/evidence/MLOOP-233-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-015 — Gouvernance Stockage & Rétention (EPIC-23)](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md)
- 📋 **Épopée de rattachement** : [epic_data_hygiene_and_retention.md](../epics/epic_data_hygiene_and_retention.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Nettoyage Scratch & Plafonnement Checkpoints)
```gherkin
Fonctionnalité: Hygiène de Session Scratch et Checkpoints

  Scénario: Élagage réussi des artefacts jetables au-delà du délai
    Étant donné un dossier "memory/scratch/" contenant 15 scripts temporaires datant de plus de 48 heures
    Quand l'opérateur exécute "mloop scratch prune --older-than-hours 48"
    Alors les 15 scripts temporaires sont supprimés
    Et les fichiers de moins de 48 heures sont conservés

  Scénario: Maintien du plafond strict des checkpoints
    Étant donné 14 checkpoints présents sous "memory/compaction/history/"
    Quand la routine de rétention s'exécute
    Alors les 4 checkpoints les plus anciens sont purgés
    Et exactement 10 checkpoints récents subsistent
```

### Pilier 2 : Exceptions & Rejets Métier (Sanctuarisation Evidence & Plans)
```gherkin
Fonctionnalité: Hygiène de Session Scratch et Checkpoints

  Scénario: Tentative de purge sur dossier protégé
    Étant donné la présence de dossiers canoniques "memory/evidence/" et "memory/plan/"
    Quand la commande "mloop scratch prune --all" est invoquée
    Alors aucun fichier dans ces répertoires sanctuarisés n'est effacé

  Scénario: Validation des paramètres de délai invalides
    Étant donné une invocation CLI avec "--older-than-hours abc"
    Quand le contrôle des arguments s'exécute
    Alors la commande s'interrompt avec un message d'erreur et un code de sortie 2
```

### Pilier 3 : Résilience & Mode Dégradé (Anti-Rebond, Concurrence & Hook de Transition)
```gherkin
Fonctionnalité: Hygiène de Session Scratch et Checkpoints

  Scénario: Protection anti-rebond et exécutions concurrentes de nettoyage
    Étant donné un nettoyage scratch déjà en cours
    Quand une seconde requête de purge est initiée
    Alors la seconde requête attend la fin du verrou sans lever d'erreur bloquante

  Scénario: Purge automatique déclenchée par la transition de statut
    Étant donné des fichiers "worker_prompt_MLOOP-233-BE.md" dans scratch
    Quand le récit "MLOOP-233-BE" passe au statut "DONE_TESTED"
    Alors le hook supprime automatiquement les artefacts temporaires de ce récit
    Et l'opération n'interrompt pas le flux de clôture en cas d'erreur de suppression

  Scénario: Gestion de fin de session en cours de purge
    Étant donné une interruption de session utilisateur durant le nettoyage
    Quand le processus est arrêté
    Alors les suppressions terminées restent cohérentes sans laisser de fichiers corrompus
```

### Pilier 4 : UX & Observabilité (Rapport Console Déterministe)
```gherkin
Fonctionnalité: Hygiène de Session Scratch et Checkpoints

  Scénario: Confirmation console claire
    Étant donné une purge réussie de 22 fichiers scratch
    Quand la commande se termine
    Alors la console affiche le nombre d'éléments supprimés et la liste des dossiers assainis
```