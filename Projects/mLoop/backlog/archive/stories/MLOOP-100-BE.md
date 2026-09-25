---
id: MLOOP-100-BE
jira_key: '-'
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Feature
title: Découpage Modulaire du Moteur de Synchronisation Jira
tags: [jira, sync, refactoring, modularity, adr-0202]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-10-SOVEREIGN-EXCELLENCE] Découpage Modulaire du Moteur de Synchronisation Jira (MLOOP-100-BE)

---

## Description
**En tant qu'** Ingénieur Plateforme / Maintainer mLoop,  
**je veux** décomposer le module monolithique de synchronisation Jira en composants modulaires spécialisés strictement inférieurs à 300 lignes,  
**afin de** respecter le standard d'architecture ADR-0202, éliminer la dette technique historique et garantir une maintenabilité et auditabilité maximales sans régression.

---

## Contexte & Périmètre

### Contexte Métier
Le composant historique `src/pipelines/jira/sync_engine.py` concentre actuellement 914 lignes de logique dense (lecture d'issues, calcul de diffs, conversion de format ADF, écriture et réconciliation). Cette forte concentration complique la maintenance et viole le plafond strict des 300 lignes (ADR-0202). Ce récit orchestre le découpage en sous-modules spécialisés à responsabilité unique, tout en éliminant les clauses d'interception silencieuses au profit d'un logging contextuel avec `exc_info=True` (ADR-0369).

### In-Scope
- Décomposition de `sync_engine.py` en 3 modules spécialisés sous `src/pipelines/jira/` :
  - `sync_reader.py` : Requêtes, pagination et extraction des tickets Jira.
  - `sync_writer.py` : Envoi de mutations, créations et transitions de statuts.
  - `sync_reconciler.py` : Calcul des deltas et logique bidirectionnelle locale/distante.
- Découpage modulaire de `adf_converter.py` (364 lignes) sous le seuil des 300 lignes.
- Remplacement systématique de tout `except: pass` par `logger.debug(..., exc_info=True)` ou avertissement explicite.
- Préservation rigoureuse de l'interface publique pour compatibilité descendante.
- Non-régression prouvée sur la suite existante `tests/test_jira_sync_safe.py`.

### Out-of-Scope
- Ajout de nouvelles fonctionnalités métier au protocole de synchronisation Jira.
- Modification du schéma de configuration ou des variables d'environnement Jira.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Décomposition Modulaire et Orchestration de la Synchronisation Jira
* **Entrée Métier** : Nom du projet mLoop cible, mode de synchronisation (lecture seule, écriture ou bidirectionnel) et jeton d'authentification Jira.
* **Règles d'admissibilité & Validation** : Chaque sous-module produit doit impérativement comporter au maximum 300 lignes physiques de code et faire moins de 15 Ko sur disque (ADR-0202).
* **Traitement & Algorithme Métier** : Délégation de l'extraction documentaire à `sync_reader`, calcul différentiel pur dans `sync_reconciler`, et exécution des mutations sécurisées via `sync_writer`, le tout coordonné par une façade `sync_engine.py` allégée.
* **Résultat Métier & Mutations** : Synchronisation intègre et déterministe entre les tickets distants et les fichiers Markdown locaux du backlog, avec rapport d'audit exhaustif.
* **Cas de Rejet Métier** : Interruption immédiate et non-destructive en cas de désalignement d'URL Jira ou de collision d'écritures concurrentes.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Découpage Modulaire du Moteur de Synchronisation Jira

  # CHEMIN NOMINAL
  Scénario: Synchronisation bidirectionnelle fluide via les sous-modules spécialisés
    Étant donné un projet mLoop configuré avec un backlog distant Jira
    Quand le moteur synchronise les états et récits locaux
    Alors l'ensemble des tickets modifiés est réconcilié sans perte
    Et tous les modules sollicités respectent le seuil strict des 300 lignes

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Journalisation détaillée lors d'un échec de conversion ADF
    Étant donné un corps de ticket contenant un schéma ADF non standard
    Quand le convertisseur modulaire traite le contenu
    Alors l'erreur est interceptée et consignée avec sa trace d'exception complète
    Et aucun blocage silencieux par pass n'est exécuté

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Reprise transactionnelle sur coupure réseau distante
    Étant donné une interruption réseau au milieu du cycle d'écriture Jira
    Quand le sous-module d'écriture détecte le timeout de transport
    Alors les écritures locales non scellées sont annulées
    Et l'état du backlog local demeure rigoureusement intègre

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Rapport d'audit de conformité AST vierge d'anomalies
    Étant donné l'achèvement du refactoring des composants Jira
    Quand l'outil code-check audite les modules du répertoire jira
    Alors le statut retourné est PASS avec zéro violation
    Et la trace d'exécution confirme l'absence de fichiers monolithiques
```
