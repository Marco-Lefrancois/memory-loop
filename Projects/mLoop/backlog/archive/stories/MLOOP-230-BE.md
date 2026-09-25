---
id: MLOOP-230-BE
jira_key: ''
epic_key: EPIC-23-DATA-HYGIENE-AND-RETENTION
type: Feature
title: Moteur de Maintenance & Défragmentation SQLite (mloop memory vacuum / health)
tags:
- storage
- sqlite
- fts5
- maintenance
- vacuum
- backend
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: backend
origin: DIRECT_REQUIREMENT
source_ref: ADR-015
macro_size: M
blocked_by: []
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-230-BE : Moteur de Maintenance & Défragmentation SQLite (mloop memory vacuum / health)

---

## Description
**En tant qu'** Administrateur et Ingénieur Système mLoop,  
**je veux** disposer des commandes `mloop memory vacuum` et `mloop memory health`,  
**afin de** vérifier l'intégrité structurelle de `loop_mem.db` (429 Mo) et des bases annexes, purger les fragments FTS5 orphelins et compacter l'espace disque non alloué de manière sécurisée avec backup atomique sans verrouillage intempestif.

---

## Contexte & Périmètre

### Contexte Métier
Le fichier `loop_mem.db` grossit continuellement lors des ingestions et ré-indexations documentaires. Sans compactage, les pages libérées restent fragmentées dans le fichier SQLite et des chunks orphelins FTS5 subsistent lorsque des fichiers sources sont renommés ou supprimés. L'ADR-015 acte une maintenance explicite avec seuil de déclenchement (fragmentation > 15%) et backup temporaire atomique.

### In-Scope
- Handler dédié `src/commands/handlers/memory_maintenance.py` (≤ 300L) raccordé au registre CLI `src/swarm.py`.
- Commande `mloop memory health [--project <proj>]` :
  - Exécute `PRAGMA integrity_check` et `PRAGMA quick_check`.
  - Calcule le ratio de fragmentation (`freelist_count / page_count`) et le volume récupérable.
  - Détecte les chunks FTS5 orphelins (dont le chemin source n'existe plus sur disque).
- Commande `mloop memory vacuum [--project <proj>] [--force]` :
  - Vérifie si le taux de fragmentation dépasse 15% (ou `--force`).
  - Crée une copie de sauvegarde atomique temporaire `loop_mem.db.bak`.
  - Supprime les chunks orphelins de `docs_chunks` et `docs_fts`.
  - Exécute un `VACUUM` sécurisé puis `PRAGMA optimize`.
  - Supprime le backup `.bak` une fois l'opération certifiée réussie (rollback si échec).
  - Restitue le gain chiffré en mégaoctets et pourcentage.

### Out-of-Scope
- Altération du schéma relationnel de `loop_mem.db`.
- Tâches d'arrière-plan automatiques permanentes ou cron silencieux (invocation explicite uniquement).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — La commande `mloop memory health` calcule et affiche l'intégrité, le taux de fragmentation et les chunks orphelins en moins de 500 ms sans bloquer les lecteurs.
> - [x] **CA-2** — La commande `mloop memory vacuum` refuse l'opération si la fragmentation est inférieure à 15% sauf si le flag `--force` est fourni.
> - [x] **CA-3** — En cas de compactage, un fichier temporaire `loop_mem.db.bak` est créé avant `VACUUM` et supprimé dès la validation du nouveau fichier.
> - [x] **CA-4** — Les chunks FTS5 orphelins sont purgés avant l'exécution du `VACUUM`.
> - [x] **CA-5** — Le module `src/commands/handlers/memory_maintenance.py` respecte strictement le plafond de 300 lignes (ADR-0202) et intègre des timeouts SQLite explicites (ADR-0369).
> - [x] **CA-6** — La suite de tests unitaires sous `tests/test_memory_maintenance.py` valide le comportement nominal et la résilience en cas d'erreur I/O.

---

## Spécifications fonctionnelles détaillées

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-230 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — intégration locale et in-process du moteur de maintenance SQLite via Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py memory vacuum [--project <name>] [--force]`
- `python src/swarm.py memory health [--project <name>]`

---

## Règles d'affaires

- **Souveraineté des données & Backup Atomique** : Aucun compactage `VACUUM` ne s'exécute sans copie miroir temporaire `loop_mem.db.bak`. En cas d'échec ou d'interruption brutale, le fichier original est restauré.
- **Seuil de déclenchement** : Seuil fixé à 15% de fragmentation (`freelist_count / page_count`) pour éviter des réécritures d'E/S inutiles sur disque.
- **Résilience aux déconnexions & Timeout** : Tout appel SQLite applique un timeout explicite de 15.0 secondes (ADR-0369).
- **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes lors du `VACUUM` par verrouillage exclusif temporaire et rejet des invocations simultanées.
- **Gestion des sessions** : En cas de session CLI interrompue ou de formulaire interrompu, les verrous sont libérés et le backup temporaire est nettoyé sans laisser de résidus orphelins.
- **Contrôle des entrées** : Tout champ vide ou caractère spécial non supporté dans les paramètres CLI provoque un rejet immédiat avec code d'erreur explicite.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-015)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1** | Sécurisation et cadencement du VACUUM et purge FTS5 | **Option A (Commande Explicite & Backup Atomique)** : Commande `mloop memory vacuum` avec backup `loop_mem.db.bak`, déclenchement si fragmentation > 15%, et purge des chunks FTS5 orphelins. | [ADR-015](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cadrage des sous-commandes `memory vacuum` et `memory health` validé.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-230 formalisée et backup atomique spécifié.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Aucun composant externe bloquant.
- [x] **Estimations et découpage validés** : Taille M (2 à 3 jours), code ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q1 scellé dans l'ADR-015.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-230-BE_fact_dossier.md`](../../memory/evidence/MLOOP-230-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-015 — Gouvernance Stockage & Rétention (EPIC-23)](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md)
- 📋 **Épopée de rattachement** : [epic_data_hygiene_and_retention.md](../epics/epic_data_hygiene_and_retention.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Health & Vacuum avec Gain Mesurable)
```gherkin
Fonctionnalité: Maintenance SQLite et Défragmentation

  Scénario: Audit de santé nominal de la base memory loop
    Étant donné une base "loop_mem.db" active avec 100 pages dont 25 pages libres
    Quand l'opérateur exécute "mloop memory health"
    Alors le rapport indique une fragmentation de 25%
    Et le résultat PRAGMA integrity_check est "ok"

  Scénario: Compactage réussi avec libération d'espace
    Étant donné une base présentant un taux de fragmentation supérieur à 15%
    Quand l'opérateur lance "mloop memory vacuum"
    Alors un backup atomique temporaire "loop_mem.db.bak" est généré
    Et les chunks orphelins sont supprimés
    Et la commande VACUUM réduit la taille du fichier
    Et le backup temporaire est nettoyé
```

### Pilier 2 : Exceptions & Rejets Métier (Seuil non atteint & Saisie Invalide)
```gherkin
Fonctionnalité: Maintenance SQLite et Défragmentation

  Scénario: Refus de compactage si la fragmentation est inférieure au seuil
    Étant donné une base avec seulement 3% de pages libres
    Quand l'opérateur lance "mloop memory vacuum" sans l'option "--force"
    Alors l'opération est ignorée avec un message explicite indiquant que la base est déjà optimisée

  Scénario: Validation des saisies extrêmes et champs incomplets
    Étant donné une commande de maintenance invoquée avec un paramètre projet vide ou invalide
    Quand la validation des paramètres intervient
    Alors l'exécution est rejetée immédiatement avec un code de sortie 1 sans altérer la base de données
```

### Pilier 3 : Résilience & Mode Dégradé (Anti-Rebond, Concurrence & Restauration)
```gherkin
Fonctionnalité: Maintenance SQLite et Défragmentation

  Scénario: Protection anti-rebond et concurrence d'exécution
    Étant donné une commande "mloop memory vacuum" déjà en cours d'exécution
    Quand un second processus tente de déclencher un vacuum simultané
    Alors le second appel détecte le verrou et est immédiatement refusé sans collision
    Et une seule opération de maintenance s'exécute à la fois

  Scénario: Restauration automatique en cas d'interruption durant le VACUUM
    Étant donné une opération VACUUM interrompue par une exception I/O
    Quand le mécanisme de gestion d'erreur intercepte l'incident
    Alors la base originale est restaurée à partir de "loop_mem.db.bak"
    Et une erreur détaillée est consignée dans les logs

  Scénario: Gestion de l'expiration de session en cours de maintenance
    Étant donné une session utilisateur ou un terminal interrompu brutalement
    Quand le gestionnaire de cycle de vie détecte la fin de session
    Alors les verrous SQLite sont libérés et les fichiers de travail temporaires sont nettoyés
```

### Pilier 4 : UX & Observabilité (Rapport Chiffré Console)
```gherkin
Fonctionnalité: Maintenance SQLite et Défragmentation

  Scénario: Affichage lisible des gains de stockage
    Étant donné un vacuum ayant permis de récupérer 85 Mo d'espace disque
    Quand la commande se termine avec succès
    Alors la console affiche un tableau récapitulatif avec taille avant, taille après et pourcentage d'optimisation
```