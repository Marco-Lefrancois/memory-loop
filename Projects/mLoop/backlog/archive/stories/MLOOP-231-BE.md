---
id: MLOOP-231-BE
jira_key: ""
epic_key: EPIC-23-DATA-HYGIENE-AND-RETENTION
type: Feature
title: "Middleware de Rotation & Archivage Rotatif des Journaux (events.jsonl, traces.json)"
tags: [logging, rotation, archive, gzip, retention, backend]
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

# 📖 MLOOP-231-BE : Middleware de Rotation & Archivage Rotatif des Journaux (events.jsonl, traces.json)

---

## Description
**En tant qu'** Développeur et Observateur mLoop,  
**je veux** que les fichiers de traçabilité (`events.jsonl`, `global_execution_traces.json`, `fact_search_log.jsonl`) fassent l'objet d'une rotation automatique lorsqu'ils atteignent le seuil de 5.0 Mo,  
**afin d'** éviter l'engorgement du disque, accélérer le chargement des dashboards et archiver les traces historiques de manière compressée (`.gz`) sous une politique de rétention glissante de 30 jours.

---

## Contexte & Périmètre

### Contexte Métier
Les fichiers de logs et d'événements cumulatifs grandissent en continu au fil des exécutions multi-agents. L'absence de rotation alourdit la mémoire vive consommée par le Dashboard web et pose un risque de saturation disque. L'ADR-015 tranche pour une rotation automatique dès 5 Mo, compression gzip atomique et rétention glissante de 30 jours, avec lecture Dashboard confinée au journal actif.

### In-Scope
- Middleware de rotation intégré dans `src/utils/logger.py` ou module dédié `src/utils/log_rotator.py` (≤ 300L).
- Seuil de déclenchement : taille du journal >= 5.0 Mo.
- Mécanisme atomique de rotation :
  - Renommage en `memory/logs/archive/<base_name>.<timestamp>.jsonl`.
  - Compression gzip synchrone vers `<base_name>.<timestamp>.jsonl.gz`.
  - Suppression du fichier intermédiaire non compressé.
  - Réouverture transparente d'un fichier journal actif vide.
- Nettoyage glissant automatique : purge des archives `.gz` âgées de plus de 30 jours.
- Commande CLI `mloop logs rotate [--force]`.

### Out-of-Scope
- Streaming distant vers un SIEM externe ou stack ELK.
- Décompression automatique de tout l'historique lors des requêtes courantes du Dashboard (seul le log actif est lu en temps réel).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — La rotation se déclenche automatiquement lorsque la taille du fichier dépasse 5.0 Mo.
> - [x] **CA-2** — L'archive résultante est compressée au format `.gz` valide sous `memory/logs/archive/`.
> - [x] **CA-3** — Aucune perte d'événement n'intervient lors de la rotation (atomicité de l'opération).
> - [x] **CA-4** — Les archives `.gz` datant de plus de 30 jours sont automatiquement élaguées.
> - [x] **CA-5** — Le code respecte le plafond de 300 lignes (ADR-0202) et utilise des verrous d'écriture non bloquants.
> - [x] **CA-6** — La suite de tests unitaires sous `tests/test_log_rotation.py` est au vert avec simulation d'écritures concurrentes.

---

## Spécifications fonctionnelles détaillées

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-231 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — intégration locale et in-process du middleware de rotation des logs via Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py logs rotate [--force]`

---

## Règles d'affaires

- **Souveraineté des traces & Compression Atomique** : Toute rotation archive le log actif sous forme compressée `.gz`. Aucun fichier n'est tronqué sans avoir été au préalable archivé.
- **Seuil calibré à 5 Mo** : Compromis optimal entre vitesse de parsing JSON en mémoire et fréquence d'archivage.
- **Rétention 30 jours** : Couvre l'intégralité d'un cycle de sprint sans saturer le disque des environnements de dev.
- **Résilience & Non-blocage** : Tout appel d'écriture en cas d'archive en cours de compression bascule en écriture temporaire sans perte de données.
- **Concurrence & Anti-Rebond** : Protection contre les rotations multiples simultanées par verrou atomique.
- **Validation des entrées** : Rejet immédiat de toute commande invoquée avec des arguments invalides.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-015)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q2** | Politique de rotation des logs et accessibilité | **Option A (Rotation 5 Mo & Gzip 30j)** : Rotation dès 5 Mo, compression gzip sous `memory/logs/archive/`, rétention glissante 30 jours et lecture Dashboard restreinte au fichier actif. | [ADR-015](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cadrage de la rotation à 5 Mo et de la rétention 30 jours validé.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-231 formalisée et compression `.gz` spécifiée.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Aucun service externe requis.
- [x] **Estimations et découpage validés** : Taille S (1 à 2 jours), code ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q2 scellé dans l'ADR-015.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-231-BE_fact_dossier.md`](../../memory/evidence/MLOOP-231-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-015 — Gouvernance Stockage & Rétention (EPIC-23)](../../../docs/01-architecture/ADR-015_epic-23_gouvernance_stockage_persistant_et_retention.md)
- 📋 **Épopée de rattachement** : [epic_data_hygiene_and_retention.md](../epics/epic_data_hygiene_and_retention.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Rotation & Compression Gzip à 5 Mo)
```gherkin
Fonctionnalité: Rotation et Archivage des Journaux

  Scénario: Déclenchement automatique de la rotation au franchissement du seuil
    Étant donné un fichier journal "events.jsonl" atteignant 5.1 Mo
    Quand un nouvel événement est émis via le logger
    Alors le fichier est immédiatement rotaté et compressé en "events.<timestamp>.jsonl.gz"
    Et un nouveau fichier "events.jsonl" est initialisé pour les écritures suivantes
```

### Pilier 2 : Exceptions & Rejets Métier (Fichier verrouillé & Espace disque)
```gherkin
Fonctionnalité: Rotation et Archivage des Journaux

  Scénario: Échec de compression ou verrouillage temporaire par un lecteur
    Étant donné un fichier journal momentanément verrouillé en lecture
    Quand la routine de rotation tente le renommage
    Alors elle n'interrompt pas l'application et retente l'opération à l'événement suivant

  Scénario: Validation des saisies extrêmes et options erronées
    Étant donné une invocation CLI "mloop logs rotate --invalid-arg"
    Quand le parseur d'arguments analyse la ligne de commande
    Alors la commande échoue avec un code de sortie 2 et un message d'aide
```

### Pilier 3 : Résilience & Mode Dégradé (Anti-Rebond, Concurrence & Rétention 30j)
```gherkin
Fonctionnalité: Rotation et Archivage des Journaux

  Scénario: Protection anti-rebond et rotation concurrente
    Étant donné deux threads déclenchant simultanément un dépassement de seuil
    Quand le mécanisme de rotation intervient
    Alors un verrou atomique garantit une seule rotation
    Et le second thread écrit dans le nouveau fichier sans perte de message

  Scénario: Élagage automatique des archives obsolètes
    Étant donné le répertoire d'archives contenant des fichiers de plus de 30 jours
    Quand la maintenance périodique s'exécute
    Alors les archives expirées sont supprimées du disque
    Et les archives de moins de 30 jours sont préservées intactes

  Scénario: Gestion de fin de session en cours de traitement
    Étant donné un arrêt brutal de la session d'exécution
    Quand le signal d'interruption est intercepté
    Alors les flux ouverts sont vidés sur le disque sans fichier corrompu
```

### Pilier 4 : UX & Observabilité (Commande Manuelle & Statut)
```gherkin
Fonctionnalité: Rotation et Archivage des Journaux

  Scénario: Déclenchement forcé via la CLI
    Étant donné l'administrateur souhaitant archiver les traces immédiatement
    Quand il exécute "mloop logs rotate --force"
    Alors tous les journaux éligibles sont compressés et le bilan est affiché sur la console
```