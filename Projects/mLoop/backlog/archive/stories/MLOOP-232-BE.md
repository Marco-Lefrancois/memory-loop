---
id: MLOOP-232-BE
jira_key: ""
epic_key: EPIC-23-DATA-HYGIENE-AND-RETENTION
type: Feature
title: "Gestionnaire de Cycle de Vie & TTL du Cache Crawler (mloop crawler prune)"
tags: [crawler, cache, ttl, markdown-twins, retention, backend]
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

# 📖 MLOOP-232-BE : Gestionnaire de Cycle de Vie & TTL du Cache Crawler (mloop crawler prune)

---

## Description
**En tant qu'** Développeur et Agent de Recherche mLoop,  
**je veux** que le cache d'ingestion web (`memory/crawler/`) dispose d'une politique d'invalidation temporelle (TTL 60 jours) et d'une commande `mloop crawler prune`,  
**afin de** purger les dépôts externes clonés orphelins (ex: `repos/openai_codex` — 67 Mo) et éliminer les Markdown Twins périmés tout en garantissant l'immunité absolue des pages marquées `pinned: true`.

---

## Contexte & Périmètre

### Contexte Métier
Le crawler accumule des milliers de pages web et des clones Git entiers. Au fil du temps, des dizaines de mégaoctets de données non consultées encombrent le disque. L'ADR-015 fixe la règle : TTL par défaut de 60 jours sur les Markdown Twins, élimination des clones sous `memory/crawler/repos/` non déclarés dans `source_manifest.json`, et sanctuarisation des pages protégées par un flag `pinned: true` ou `source: permanent`.

### In-Scope
- Handler dédié `src/commands/handlers/crawler_prune.py` (≤ 300L) raccordé à la CLI mLoop.
- Commande `mloop crawler prune [--project <proj>] [--ttl-days 60] [--dry-run]` :
  - Analyse des fichiers sous `memory/crawler/cache/`.
  - Exemption stricte de suppression pour les fichiers dont le frontmatter contient `pinned: true` ou `source: permanent`.
  - Suppression des fichiers non épinglés dont la date de dernier accès/modification excède la durée TTL.
  - Détection et purge des sous-répertoires de dépôts sous `memory/crawler/repos/` non référencés dans `docs/00-ingested/source_manifest.json`.
- Restitution d'un bilan chiffré : nombre de fichiers et dossiers supprimés, volume libéré.
- Support du commutateur `--dry-run` pour prévisualiser les suppressions.

### Out-of-Scope
- Altération des documents pérennes consolidés dans `docs/00-ingested/` ou `reference/`.
- Modification de la logique de crawling et de rendu Markdown Twin.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — La commande en mode `--dry-run` liste avec exactitude les éléments ciblés sans modifier le disque.
> - [x] **CA-2** — Les Markdown Twins étiquetés `pinned: true` ou `source: permanent` ne sont JAMAIS supprimés quel que soit leur âge.
> - [x] **CA-3** — Les Markdown Twins âgés de plus de 60 jours (ou paramètre `--ttl-days`) sont purgés lors de l'exécution réelle.
> - [x] **CA-4** — Les dépôts non déclarés dans `source_manifest.json` sont purgés de `memory/crawler/repos/`.
> - [x] **CA-5** — Le module Python respecte strictement la limite de 300 lignes (ADR-0202).
> - [x] **CA-6** — La suite de tests unitaires sous `tests/test_crawler_prune.py` est au vert avec couverture des cas de protection.

---

## Spécifications fonctionnelles détaillées

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-232 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — intégration locale et in-process de la commande crawler prune via Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py crawler prune [--project <name>] [--ttl-days 60] [--dry-run]`

---

## Règles d'affaires

- **Immunité Pinned** : Tout document dont les métadonnées YAML contiennent `pinned: true` ou `source: permanent` est sanctuarisé de manière absolue et ignoré par le ramasse-miettes.
- **Rattachement au Manifeste Source** : Les dépôts Git clonés sous `memory/crawler/repos/` doivent être audités vis-à-vis de `source_manifest.json` avant toute suppression.
- **Résilience aux timeouts** : Tout calcul d'inventaire volumétrique applique des timeouts bornés (10 secondes maximum).
- **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes lors du nettoyage pour éviter les suppressions partielles.
- **Gestion des sessions** : En cas de coupure de session ou de terminal interrompu, l'état reste cohérent grâce à la suppression fichier par fichier.
- **Contrôle des entrées** : Tout argument numérique invalide pour `--ttl-days` provoque un rejet explicite.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-015)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q3** | Cycle de vie du cache crawler et gestion des dépôts | **Option A (TTL 60j & Immunité Pinned)** : TTL de 60 jours, purge des clones orphelins hors manifest, et sanctuarisation absolue des pages `pinned: true`. | [ADR-015](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cadrage de `crawler prune`, du TTL 60j et de l'immunité `pinned: true` validé.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-232 formalisée et critères de purge spécifiés.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Intégration sur le moteur crawler existant.
- [x] **Estimations et découpage validés** : Taille S (1 à 2 jours), code ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q3 scellé dans l'ADR-015.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-232-BE_fact_dossier.md`](../../memory/evidence/MLOOP-232-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-015 — Gouvernance Stockage & Rétention (EPIC-23)](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md)
- 📋 **Épopée de rattachement** : [epic_data_hygiene_and_retention.md](../epics/epic_data_hygiene_and_retention.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Purge Sélective & Immunité Pinned)
```gherkin
Fonctionnalité: Élagage du Cache Crawler

  Scénario: Élagage réussi des jumeaux expirés avec respect des pages épinglées
    Étant donné un jumeau "page_old.md" âgé de 75 jours sans marqueur
    Et un jumeau "page_pinned.md" âgé de 90 jours avec "pinned: true"
    Quand l'opérateur exécute "mloop crawler prune --ttl-days 60"
    Alors "page_old.md" est supprimé du disque
    Et "page_pinned.md" demeure intact dans le cache
```

### Pilier 2 : Exceptions & Rejets Métier (Mode Dry-Run & Options Invalides)
```gherkin
Fonctionnalité: Élagage du Cache Crawler

  Scénario: Simulation sans effet de bord via dry-run
    Étant donné 50 fichiers éligibles à la suppression
    Quand la commande est exécutée avec l'option "--dry-run"
    Alors la liste des 50 fichiers et le volume calculé sont affichés
    Et aucun fichier n'est altéré sur le disque

  Scénario: Validation des saisies et arguments TTL invalides
    Étant donné une invocation avec un paramètre "--ttl-days -5"
    Quand la validation des paramètres est effectuée
    Alors la commande rejette l'entrée avec un message d'erreur explicite
```

### Pilier 3 : Résilience & Mode Dégradé (Anti-Rebond, Concurrence & Dépôts Orphelins)
```gherkin
Fonctionnalité: Élagage du Cache Crawler

  Scénario: Protection anti-rebond et exécutions concurrentes
    Étant donné un élagage du cache déjà en cours
    Quand une seconde commande "mloop crawler prune" est initiée
    Alors la seconde commande détecte le verrou et s'arrête sans conflit

  Scénario: Purge d'un dépôt cloné orphelin hors manifest
    Étant donné un clone "memory/crawler/repos/sample_repo" absent de "source_manifest.json"
    Quand la commande "mloop crawler prune" est lancée
    Alors le dossier du dépôt est purgé de manière récursive
    Et le volume libéré est ajouté au bilan global

  Scénario: Gestion de l'expiration de session en cours de purge
    Étant donné une session utilisateur interrompue prématurément
    Quand l'interruption survient
    Alors les suppressions déjà terminées restent cohérentes sans laisser de fichiers partiellement effacés
```

### Pilier 4 : UX & Observabilité (Rapport Consolidation Console)
```gherkin
Fonctionnalité: Élagage du Cache Crawler

  Scénario: Affichage du bilan d'hygiène du crawler
    Étant donné une purge ayant nettoyé 120 fichiers et 65 Mo
    Quand l'exécution s'achève
    Alors la console restitue un rapport structuré avec le décompte par catégorie
```