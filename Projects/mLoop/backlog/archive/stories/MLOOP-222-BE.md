---
id: MLOOP-222-BE
jira_key: ""
epic_key: EPIC-22-TOOLING-ECOSYSTEM-HARNESS
type: Feature
title: "Pipeline Décisionnel Wayfinder (Cartographie de Décisions & Sous-Agents Asynchrones AFK)"
tags: [wayfinder, fog-of-war, decision-map, afk-agents, backend]
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: "Marco (PO)"
validated_at: "2026-09-24"
layer: backend
origin: DIRECT_REQUIREMENT
source_ref: "KN-052"
macro_size: M
blocked_by: []
created_at: "2026-09-24"
updated_at: "2026-09-24"
---

# 📖 MLOOP-222-BE : Pipeline Décisionnel Wayfinder (Cartographie de Décisions & Sous-Agents Asynchrones AFK)

---

## Description
**En tant qu'** Orchestrateur mLoop et Product Owner,  
**je veux** pouvoir initialiser et faire progresser une carte décisionnelle Wayfinder (`wayfinder:map`) via les commandes `mloop wayfinder init-map` et `mloop wayfinder resolve`,  
**afin de** lever méthodiquement le brouillard de guerre sur les initiatives complexes en distinguant les arbitrages humains (HITL) des investigations asynchrones d'agents (AFK) avant toute spécification technique.

---

## Contexte & Périmètre

### Contexte Métier
Dans les projets d'ingénierie logicielle d'envergure, démarrer prématurément par la rédaction de code ou de spécifications détaillées sans dissiper le brouillard de guerre conduit à des impasses architecturales. Wayfinder formalise une cartographie de décisions où chaque ticket représente un nœud d'incertitude. Afin d'optimiser l'efficacité opérationnelle, mLoop sépare les tickets nécessitant un arbitrage humain synchrone (HITL) des tickets d'investigation documentaire pouvant être délégués en tâche de fond à des sous-agents asynchrones (AFK).

### In-Scope
- Évolution de `src/pipelines/wayfinder.py` (respect strict du plafond ≤ 300L, ADR-0202).
- Initialisation de la carte sous `Projects/<project>/memory/wayfinder/wayfinder_map.md`.
- Typologie duale formalisée des tickets :
  - **HITL (Human-in-the-Loop)** : Décision humaine interactive (arbitrage produit, choix technologique).
  - **AFK (Away-from-Keyboard)** : Recherche documentaire et benchmarking confiés à un sous-agent `/research` asynchrone sans blocage terminal.
- Commande `mloop wayfinder frontier --project <proj>` listant les tickets décidables à la frontière du brouillard.
- Commande `mloop wayfinder resolve --project <proj> --ticket <id> --decision <text>` enregistrant la résolution et débloquant les dépendances aval vers `to-spec`.

### Out-of-Scope
- Remplacement du stockage Markdown canonique par une base de données relationnelle complexe.
- Synchronisation bidirectionnelle avec des outils de ticketing tiers externes.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [ ] **CA-1** — La commande `mloop wayfinder init-map` génère une carte valide sous `Projects/<project>/memory/wayfinder/wayfinder_map.md`.
> - [ ] **CA-2** — La frontière (`wayfinder frontier`) liste de manière exacte les tickets non bloqués en distinguant HITL et AFK.
> - [ ] **CA-3** — La commande `mloop wayfinder resolve` consigne la décision et déverrouille les nœuds dépendants.
> - [ ] **CA-4** — Les anomalies de saisie (champ vide, caractère spécial prohibé, valeur null) sont rejetées avec message explicite.
> - [ ] **CA-5** — Le module Python respecte le plafond modulaire de 300 lignes (ADR-0202).
> - [ ] **CA-6** — La suite de tests unitaires sous `tests/test_wayfinder_pipeline.py` est au vert à 100%.

### Opérations Métier & Logique Backend

#### 1. Initialisation de la carte — `mloop wayfinder init-map --project <proj> --goal <text>`
* **Entrée Métier** : Nom du projet et objectif global (`goal`).
* **Règles d'admissibilité & Validation** : Le projet doit exister ; le but ne doit pas être un champ vide.
* **Traitement & Algorithme Métier** :
  1. Vérifier l'arborescence projet.
  2. Créer le répertoire `Projects/<proj>/memory/wayfinder/` si inexistant.
  3. Générer le fichier `wayfinder_map.md` avec la structure standardisée (Destination, Frontière, Nœuds explorés).
* **Résultat Métier & Mutations** : Création du fichier `wayfinder_map.md`.
* **Cas de Rejet Métier** : Dossier projet manquant ; objectif vide.

#### 2. Résolution d'un ticket — `mloop wayfinder resolve --project <proj> --ticket <id> --decision <text>`
* **Entrée Métier** : Identifiant de ticket et texte d'arbitrage.
* **Règles d'admissibilité & Validation** : Le ticket doit exister dans l'état ouvert sur la frontière.
* **Traitement & Algorithme Métier** :
  1. Charger la carte Wayfinder.
  2. Mettre à jour l'état du ticket vers `RESOLVED` avec l'arbitrage consigné.
  3. Réévaluer les dépendances pour avancer la frontière.
  4. Réécrire la carte de façon atomique.
* **Résultat Métier & Mutations** : Mise à jour de `wayfinder_map.md`.
* **Cas de Rejet Métier** : Ticket inconnu ; décision vide ; conflit de dépendance non résolu.

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-222 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — moteur de graphe décisionnel et gestion de la frontière Wayfinder exécutés in-process via CLI Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py wayfinder init-map --project <name> --goal <text>`
- `python src/swarm.py wayfinder frontier --project <name>`
- `python src/swarm.py wayfinder resolve --project <name> --ticket <id> --decision <text>`

---

## Règles d'affaires

- **Sanctuarisation de la Destination** : Aucune initiative ne peut évoluer sans un objectif formalisé consigné dans la carte.
- **Étanchéité des Rôles HITL vs AFK** : Les tickets nécessitant un jugement humain restent en attente synchrone ; les tickets AFK d'investigation sont traitables en arrière-plan sans bloquer la console.
- **Résilience & Délai d'Attente** : En cas de délégation d'investigation AFK, un délai d'attente maximal (timeout) est défini pour éviter les tâches zombies.
- **Concurrence & Anti-Rebond** : L'accès à la carte est protégé par verrou inter-processus afin d'empêcher les corruptions dues à des résolutions concurrentes ou double-clic.
- **Session & Déconnexion** : Les tickets résolus persistent localement de manière déterministe indépendamment d'une session expirée ou d'une erreur d'authentification 401.
- **Intégrité des Données** : Rejet de toute résolution portant des données partielles, une valeur null ou un champ vide.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-014)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q3** | Pipeline Wayfinder & Typologie HITL / AFK | **Option A (Frontière & Résolution Continue)** : Carte sous `Projects/<project>/memory/wayfinder/wayfinder_map.md`, séparation étanche HITL (humain) vs AFK (sous-agent asynchrone), et commande `resolve`. | [KN-052](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-052_wayfinder_fog_of_war.md) · [ADR-014](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cycle de cartographie et typologie HITL/AFK explicités.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-222 formalisée, contrats CLI définis.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Stockage Markdown canonique sans dépendance externe.
- [x] **Estimations et découpage validés** : Taille M (2 à 3 jours), modularité ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q3 scellé dans l'ADR-014.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-222-BE_fact_dossier.md`](../../memory/evidence/MLOOP-222-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-014 — Intégration Opérationnelle Tooling (EPIC-22)](../../../docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md)
- 📜 **Fiche de Savoir** : [KN-052 Wayfinder Fog of War](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-052_wayfinder_fog_of_war.md)
- 📋 **Épopée de rattachement** : [epic_tooling_ecosystem_harness.md](../epics/epic_tooling_ecosystem_harness.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Happy Path — Initialisation & Résolution de Ticket)
```gherkin
Fonctionnalité: Pipeline Décisionnel Wayfinder

  Scénario: Initialisation réussie d'une carte décisionnelle
    Étant donné un projet existant "mLoop"
    Quand l'opérateur exécute "mloop wayfinder init-map --project mLoop --goal 'Refonte CLI'"
    Alors le fichier "Projects/mLoop/memory/wayfinder/wayfinder_map.md" est créé
    Et la section "Destination" consigne l'objectif avec succès

  Scénario: Résolution d'un ticket HITL à la frontière
    Étant donné un ticket ouvert "T-01" présent sur la frontière
    Quand le Product Owner résout le ticket via "mloop wayfinder resolve --project mLoop --ticket T-01 --decision 'Option A validée'"
    Alors le statut du ticket passe à "RESOLVED"
    Et les tickets dépendants deviennent éligibles sur la frontière
```

### Pilier 2 : Exceptions & Rejets Métier (Saisie Invalide & Nœud Inexistant)
```gherkin
Fonctionnalité: Pipeline Décisionnel Wayfinder

  Scénario: Tentative de résolution d'un ticket inexistant
    Étant donné un identifiant de ticket "T-999" absent de la carte
    Quand l'opérateur tente de le résoudre
    Alors la commande échoue avec un rejet explicite
    Et la carte conserve son intégrité antérieure

  Scénario: Résolution avec champ vide ou décision manquante
    Étant donné une requête portant une décision vide ou tronquée
    Quand la commande de résolution est transmise
    Alors l'opération est refusée sans écriture sur le disque
```

### Pilier 3 : Résilience & Mode Dégradé (Concurrence & Timeout)
```gherkin
Fonctionnalité: Pipeline Décisionnel Wayfinder

  Scénario: Protection contre la concurrence et le double-clic de résolution
    Étant donné deux agents tentant de résoudre simultanément le même ticket
    Quand le verrou inter-processus intervient
    Alors la première résolution est consignée
    Et la seconde tentative signale que le ticket est déjà clos sans altérer l'index

  Scénario: Délai d'attente (timeout) sur sous-agent de recherche AFK
    Étant donné un sous-agent d'investigation AFK n'ayant pas répondu dans le délai imparti
    Quand le superviseur évalue l'état de la tâche
    Alors un timeout est levé et le ticket reste investigable en mode dégradé
```

### Pilier 4 : UX & Observabilité (Clarté de la Frontière & Accessibilité)
```gherkin
Fonctionnalité: Pipeline Décisionnel Wayfinder

  Scénario: Affichage ergonomique de la frontière de décision
    Étant donné une carte comportant des tickets HITL et AFK
    Quand l'opérateur exécute "mloop wayfinder frontier --project mLoop"
    Alors la liste des décisions pendantes est restituée de façon lisible avec distinction claire des rôles
    Et les raccourcis de commande de résolution sont affichés
```