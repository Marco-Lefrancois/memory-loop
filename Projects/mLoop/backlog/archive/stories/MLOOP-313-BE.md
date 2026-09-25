---
id: MLOOP-313-BE
jira_key: MLOOP-313-BE
epic_key: EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION
type: Feature
title: "Harmonisation Multi-Couches des Consommateurs (_sync_backlog, wikifix, scratch_prune, Dashboard)"
tags: [sync, wikifix, dashboard, scrapers, consumers, backend]
status: DONE_TESTED
layer: backend
invest_score: 6/6
grill_me: DONE
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0391-§4"
macro_size: M
blocked_by: [MLOOP-310-BE, MLOOP-312-BE]
created_at: "2026-09-25T04:35:00Z"
updated_at: "2026-09-25T05:10:00Z"
---

# Harmonisation Multi-Couches des Consommateurs (_sync_backlog, wikifix, scratch_prune, Dashboard)

---

## Description
**En tant qu'** ingénieur d'intégration mLoop,  
**je veux** aligner tous les consommateurs de statuts du framework (`_sync_backlog_parser.py`, `wikifix_core.py`, `scratch_prune.py`, `dashboard/routers/backlog.py`) sur le nouveau vocabulaire à 5 phases,  
**afin d'** éviter toute désynchronisation, troncature de statuts dans les tables Markdown, blocage INVEST indu ou désordre d'affichage dans le Dashboard.

---

## Contexte & Périmètre

### Contexte Métier
L'introduction des nouveaux statuts (`READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP`, `DONE`) et la sanctuarisation de `DONE_TESTED` et `SHIPPED` impactent de multiples composants périphériques qui analysent ou consomment les statuts :
1. Le parser de tables Markdown de `sprint_backlog.md` (`_sync_backlog_parser.py`), dont l'expression régulière `STATUS_VOCAB_RE` ignorait les nouveaux termes et risquait d'en tronquer la lecture.
2. Le moteur d'intégrité WikiFix (`wikifix_core.py`), qui doit considérer les nouveaux statuts dans ses filtres de tolérance INVEST.
3. La commande de nettoyage des sessions scratch (`scratch_prune.py`), qui doit purger les artefacts dès que le statut terminal `DONE` est atteint.
4. L'API du Dashboard (`dashboard/routers/backlog.py`), dont l'ordre des colonnes `STATUS_ORDER` doit refléter la chaîne canonique des 5 phases.

### In-Scope
- Mise à niveau de `STATUS_VOCAB_RE` dans `src/pipelines/sync/_sync_backlog_parser.py` : intégration de `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP`, `SHIPPED` avec tri dégressif par longueur de chaîne.
- Intégration des nouveaux statuts dans `src/pipelines/wikifix_core.py` :
  - Gardes de contenu et Sentinel (L101–130).
  - Expression régulière `_tolerated` (L202) pour ne pas bloquer sur INVEST.
- Mise à jour de `src/commands/handlers/scratch_prune.py` : ajout de `DONE` et `QA_CERTIFIED` dans `terminal_statuses`.
- Mise à jour de `src/dashboard/routers/backlog.py` : ajustement de la liste `STATUS_ORDER`.

### Out-of-Scope
- Refactorisation du modèle de données Pydantic (couvert par `MLOOP-310-BE`).
- Rédaction des spécifications normatives (couverte par `MLOOP-314-FULL`).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — Un récit portant `READY_FOR_QA` ou `QA_CERTIFIED` dans la colonne Statut de `sprint_backlog.md` est fidèlement extrait sans troncature par `parse_backlog_status_maps()`.
> - [x] **CA-2** — `wikifix` audite les projets sans lever d'erreur INVEST sur les récits en `READY_FOR_QA` ou `QA_CERTIFIED`.
> - [x] **CA-3** — La commande `scratch_prune` détecte le statut `DONE` comme terminal et purge les artefacts de travail temporaires associés.
> - [x] **CA-4** — Le Dashboard organise les colonnes du Drawer selon la séquence canonique : `DRAFT ➔ IN_ANALYZE ➔ READY_FOR_GROOMING ➔ READY_FOR_DEV ➔ IN_DEV ➔ READY_FOR_QA ➔ QA_CERTIFIED ➔ DONE`.
> - [x] **CA-5** — Aucun test de `tests/test_sync_sprint_backlog.py` n'est régressé.

### Opérations Métier & Logique Backend

#### 1. Parsing Robuste de Statut — `_sync_backlog_parser.STATUS_VOCAB_RE`
* **Entrée Métier** : Cellule texte de statut issue de `sprint_backlog.md`.
* **Règles d'admissibilité & Validation** : Reconnaissance exacte des 15 statuts autorisés mLoop.
* **Traitement & Algorithme Métier** : Compilation d'une regex ordonnée par longueur décroissante pour garantir que `READY_FOR_QA` ne soit pas tronqué en `READY_FOR_DEV` ou ignoré.
* **Résultat Métier & Mutations** : Extraction sans ambiguïté du statut SSOT.
* **Cas de Rejet Métier** : Statuts invalides ignorés par le parser.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)

#### Matrice des Contrats API
- **OQ-313 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — harmonisation interne des parsers Markdown, scripts de purge et ordonnancement de routeurs locaux (`src/pipelines/sync/_sync_backlog_parser.py`, `src/pipelines/wikifix_core.py`, `src/commands/handlers/scratch_prune.py`), sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

---

## Règles d'affaires

- **Non-Régression de Parsing Markdown** : Les séparateurs et balises textuelles dans les tables de sprint backlog doivent pouvoir accueillir les statuts longs sans corruption de parsing.
- **Cycle de Vie du Scratch Space** : Les artefacts de session ne doivent pas encombrer le stockage une fois que le récit atteint un état d'achèvement (`DONE`, `SHIPPED`).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-313-BE_fact_dossier.md`](../../memory/evidence/MLOOP-313-BE_fact_dossier.md)
- ⚖️ **Épopée Cadre** : [`backlog/epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md`](../epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Parser de Backlog** : [`src/pipelines/sync/_sync_backlog_parser.py`](../../../src/pipelines/sync/_sync_backlog_parser.py)
- 📜 **Moteur WikiFix** : [`src/pipelines/wikifix_core.py`](../../../src/pipelines/wikifix_core.py)
- 📜 **Décision d'Architecture** : [ADR-0391 — Harmonisation Cycle de Vie 5 Phases](../../standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Harmonisation Multi-Couches des Consommateurs

  # CHEMIN NOMINAL (Happy Path & Parsing Backlog)
  Scénario: Extraction nominale des nouveaux statuts depuis une table Markdown de backlog
    Étant donné un fichier sprint_backlog.md contenant des lignes avec "READY_FOR_QA" et "QA_CERTIFIED"
    Quand parse_backlog_status_maps analyse le document
    Alors les statuts complets sont extraits sans troncature
    Et la cartographie des statuts est fidèlement synchronisée

  # EXCEPTIONS & REJETS (Statuts non reconnus)
  Scénario: Gestion tolérante des cellules corrompues dans les tableaux
    Étant donné une cellule de statut corrompue dans le sprint backlog
    Quand le parser de synchronisation lit la ligne
    Alors le motif est ignoré sans lever d'exception bloquante
    Et les autres récits valides de la table sont correctement parsés

  # RÉSILIENCE TECHNIQUE (Purge sans délai d'attente ni concurrence)
  Scénario: Purge automatique des répertoires scratch lors du passage à DONE
    Étant donné un récit qui atteint le statut terminal DONE
    Quand scratch_prune est exécuté
    Alors les artefacts de travail temporaires associés sont purgés sans délai d'attente ni timeout
    Et aucun blocage de fichier concurrent n'interrompt le nettoyage

  # UX & OBSERVABILITÉ (Ordonnancement du Dashboard sans champ vide)
  Scénario: Restitution ordonnée des colonnes du Drawer de backlog sans valeur null
    Étant donné un appel au routeur de backlog du Dashboard
    Quand la liste ordonnée des récits est générée
    Alors les colonnes respectent l'ordre séquentiel des 5 phases sans valeur null ni champ vide
    Et le journal trace la génération réussie sans token expiré
```
