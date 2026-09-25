---
id: MLOOP-234-FULL
jira_key: ''
epic_key: EPIC-23-DATA-HYGIENE-AND-RETENTION
type: Feature
title: Harnais de Surveillance E2E de la Santé du Stockage & Intégration Vibe-Check
tags:
- vibe-check
- storage
- monitoring
- e2e
- hygiene
- fullstack
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: fullstack
origin: DIRECT_REQUIREMENT
source_ref: ADR-015
macro_size: M
blocked_by:
- MLOOP-230-BE
- MLOOP-231-BE
- MLOOP-232-BE
- MLOOP-233-BE
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-234-FULL : Harnais de Surveillance E2E de la Santé du Stockage & Intégration Vibe-Check

---

## Description
**En tant que** Responsable Qualité et Architecte mLoop,  
**je veux** que le guardrail Vibe-Check intègre un contrôle automatisé de la santé et du volume de la mémoire (`Check 24 : Hygiène & Plafond de Stockage Mémoire`),  
**afin de** détecter proactivement toute dérive volumétrique (base fragmentée, logs excessifs, cache orphelin) avec alertes calibrées (WARNING à 500 Mo, FAIL si corruption) et valider l'ensemble du cycle de rétention par un harnais E2E.

---

## Contexte & Périmètre

### Contexte Métier
Le guardrail Vibe-Check est la porte pré-vol incontournable avant toute action sur mLoop. L'ADR-015 stipule l'intégration d'un Check 24 mesurant la volumétrie globale et l'intégrité de `memory/`, calibrant un avertissement non bloquant en cas de dérive (> 500 Mo cumulés, fragmentation SQLite > 20%, log non rotaté > 10 Mo) et un blocage fatal uniquement en cas de corruption de base de données.

### In-Scope
- Ajout du Check 24 dans le sous-module Vibe-Check dédié (`src/pipelines/vibe_check/_vc_storage.py`, ≤ 300L).
- Métriques surveillées en moins de 100 ms :
  - Taille cumulée de `memory/` (seuil WARNING : 500 Mo).
  - Taux de fragmentation de `loop_mem.db` (seuil WARNING : 20%).
  - Intégrité SQLite via `PRAGMA quick_check` en moins de 50 ms (seuil FAIL si anomalie).
  - Présence de logs actifs non rotatés > 10 Mo (seuil WARNING).
  - Présence de dépôts orphelins sous `memory/crawler/repos/` (seuil WARNING).
- Harnais de test E2E sous `tests/test_storage_health_e2e.py` validant l'ensemble du cycle :
  - Simulation de base fragmentée + logs volumineux + jumeaux expirés.
  - Détection par Vibe-Check (statut WARNING).
  - Exécution des commandes de maintenance (`vacuum`, `rotate`, `prune`).
  - Validation du retour de Vibe-Check à l'état nominal PASS.
- Synchronisation SSOT du guide CLI (`mloop guide --sync`).

### Out-of-Scope
- Alertes par email ou intégrations de notification tierces externes.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — Le Vibe-Check exécute le Check 24 en moins de 100 ms et signale correctement les alertes WARNING.
> - [x] **CA-2** — Une corruption physique de base de données déclenche un statut FAIL bloquant immédiat.
> - [x] **CA-3** — Le test E2E valide la transition complète : Dérive -> Détection WARNING -> Remédiation -> Rétablissement PASS.
> - [x] **CA-4** — Le guide CLI SSOT `CLI_PIPELINE_GUIDE.md` est mis à jour et validé à 100% de parité.
> - [x] **CA-5** — Les modules Python implémentés respectent scrupuleusement le plafond de 300 lignes (ADR-0202).
> - [x] **CA-6** — La suite complète des tests de non-régression est au vert (100% passants).

---

## Spécifications fonctionnelles détaillées

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-234 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — intégration locale et in-process du harnais de certification et du check de stockage Vibe-Check via Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py vibe-check [--project <name>]`

---

## Règles d'affaires

- **Seuils d'Alerte Gradués** : Les alertes volumétriques (> 500 Mo, fragmentation > 20%, log > 10 Mo) émettent un statut WARNING non-bloquant pour préserver la vélocité. Seule la corruption physique de base de données émet un statut FAIL bloquant.
- **Performance Pré-Vol** : Le Check 24 doit s'exécuter en moins de 100 ms sans impacter le temps de boot CLI.
- **Résilience E2E** : Le scénario de test E2E certifie la boucle fermée complète de détection et de remédiation.
- **Concurrence & Anti-Rebond** : Protection contre les exécutions de Vibe-Check simultanées avec cache de statut court.
- **Gestion des sessions** : En cas de coupure inattendue, le rapport d'audit est préservé sans état corrompu.
- **Contrôle des entrées** : Tout argument CLI non reconnu est rejeté avant l'analyse de santé.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-015)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q4b** | Surveillance Vibe-Check et seuils d'alerte | **Option A (WARNING 500 Mo / FAIL Corruption)** : Intégration du Check 24 avec avertissement à 500 Mo et blocage strict en cas de corruption. | [ADR-015](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cadrage du Check 24 et du scénario E2E de certification validé.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-234 formalisée et seuils gradués spécifiés.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Raccordement au moteur Vibe-Check existant.
- [x] **Estimations et découpage validés** : Taille M (2 à 3 jours), code ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q4b scellé dans l'ADR-015.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-234-FULL_fact_dossier.md`](../../memory/evidence/MLOOP-234-FULL_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-015 — Gouvernance Stockage & Rétention (EPIC-23)](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md)
- 📋 **Épopée de rattachement** : [epic_data_hygiene_and_retention.md](../epics/epic_data_hygiene_and_retention.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Contrôle Pré-Vol Vibe-Check Passant)
```gherkin
Fonctionnalité: Surveillance et Certification de Santé du Stockage

  Scénario: Validation pré-vol nominale sans dérive de stockage
    Étant donné un répertoire "memory/" sain de 350 Mo
    Et une base SQLite sans fragmentation excessive
    Quand la commande "mloop vibe-check --project mLoop" est lancée
    Alors le Check 24 "Hygiène & Plafond de Stockage Mémoire" affiche le statut PASS
```

### Pilier 2 : Exceptions & Rejets Métier (Alerte Dérive & Blocage Corruption)
```gherkin
Fonctionnalité: Surveillance et Certification de Santé du Stockage

  Scénario: Alerte de seuil volumétrique non bloquante
    Étant donné le volume de "memory/" dépassant 510 Mo
    Quand le Vibe-Check est exécuté
    Alors le Check 24 retourne un statut WARNING explicite
    Et l'exécution globale n'est pas interrompue

  Scénario: Blocage fatal en cas de corruption SQLite
    Étant donné un fichier SQLite retournant une erreur au quick_check
    Quand le Vibe-Check est exécuté
    Alors le Check 24 retourne un statut FAIL bloquant immédiat

  Scénario: Validation des arguments CLI non reconnus
    Étant donné une option CLI invalide passée au Vibe-Check
    Quand le contrôle des entrées est effectué
    Alors la commande renvoie un message d'erreur et refuse l'exécution
```

### Pilier 3 : Résilience & Mode Dégradé (Anti-Rebond, Concurrence & Cycle E2E)
```gherkin
Fonctionnalité: Surveillance et Certification de Santé du Stockage

  Scénario: Protection anti-rebond lors des vérifications pré-vol
    Étant donné deux vérifications Vibe-Check lancées au même instant
    Quand les processus contrôlent la base de données
    Alors un verrou partagé en lecture garantit une exécution sans conflit

  Scénario: Cycle complet de remédiation automatisée
    Étant donné un état initial en dérive avec logs de 12 Mo et twins périmés
    Quand les routines "mloop memory vacuum", "mloop logs rotate" et "mloop crawler prune" sont appliquées
    Alors le volume disque est drastiquement réduit
    Et le Vibe-Check subséquent repasse immédiatement au statut PASS

  Scénario: Gestion de fin de session en cours d'audit de santé
    Étant donné une interruption du signal terminal durant le Vibe-Check
    Quand l'audit est stoppé
    Alors aucune ressource n'est laissée verrouillée
```

### Pilier 4 : UX & Observabilité (Rendu Synthétique dans le Bilan Vibe-Check)
```gherkin
Fonctionnalité: Surveillance et Certification de Santé du Stockage

  Scénario: Clarté de la restitution des métriques dans le tableau pré-vol
    Étant donné l'affichage du bilan Vibe-Check
    Quand les 24 checks sont énumérés
    Alors la ligne Check 24 mentionne distinctement la volumétrie totale et le statut d'intégrité
```