---
id: MLOOP-223-FE
jira_key: ''
epic_key: EPIC-22-TOOLING-ECOSYSTEM-HARNESS
type: Feature
title: Module Dashboard pour l'Écosystème Tooling & Visualisation des Runtimes Développeur
tags:
- dashboard
- tooling
- runtimes
- ui
- frontend
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: "Marco (PO)"
validated_at: "2026-09-24"
layer: frontend
origin: DIRECT_REQUIREMENT
source_ref: KN-050, KN-051
macro_size: M
blocked_by:
- MLOOP-220-BE
- MLOOP-221-BE
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-223-FE : Module Dashboard pour l'Écosystème Tooling & Visualisation des Runtimes Développeur

---

## Description
**En tant qu'** Utilisateur et Développeur consultant le Dashboard mLoop,  
**je veux** disposer d'une tuile dédiée « Developer Runtimes & Tooling » sur la page Overview affichant la disponibilité et la configuration des outils (OpenCode CLI, Plannotator, Wayfinder, Graphify, LiteLLM),  
**afin d'** obtenir une visibilité synthétique de la santé de mon environnement de développement sans devoir exécuter des commandes manuelles de diagnostic en terminal.

---

## Contexte & Périmètre

### Contexte Métier
Le Dashboard web mLoop constitue la tour de contrôle de l'orchestration des projets. Avec la multiplication des outils de développement (OpenCode pour l'exécution, Plannotator pour l'approbation de plans, Graphify pour la base de connaissances et LiteLLM pour le routage de modèles), une vue unifiée sur la page d'accueil permet d'identifier immédiatement les dépendances manquantes ou les proxies inaccessibles.

### In-Scope
- Routeur backend FastAPI `src/dashboard/routers/tooling.py` (strictement ≤ 300L, ADR-0202).
- Route `GET /api/tooling/status` renvoyant le statut en temps réel des binaires et des services associés.
- Tuile synthétique cyber sur la page d'accueil Overview (`src/dashboard/static/index.html`) avec badges d'état colorés (vert opérationnel, orange dégradé, rouge indisponible).
- Bouton d'action directe : déclenchement de l'ouverture du dernier plan annoté sous Plannotator et copie de commande CLI OpenCode.
- Intégration ergonomique respectant les standards de contraste et d'accessibilité clavier/ARIA.

### Out-of-Scope
- Remplacement du serveur FastAPI ou modification des routeurs de statistiques existants.
- Gestion d'installations logicielles automatiques depuis l'interface web (actions en lecture et commandes assistées).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [ ] **CA-1** — La route `GET /api/tooling/status` répond en moins de 100 millisecondes avec la structure JSON attendue.
> - [ ] **CA-2** — La tuile « Developer Runtimes & Tooling » est intégrée sur la page Overview du Dashboard web mLoop.
> - [ ] **CA-3** — Les indicateurs de disponibilité reflètent fidèlement la présence des binaires sur le système local.
> - [ ] **CA-4** — L'accessibilité clavier et les balises ARIA permettent une navigation conforme sans dépendance exclusive à la souris.
> - [ ] **CA-5** — Le routeur `src/dashboard/routers/tooling.py` respecte le plafond de 300 lignes (ADR-0202).
> - [ ] **CA-6** — La suite de tests unitaires sous `tests/test_dashboard_tooling.py` est au vert à 100%.

### Opérations Métier & Logique Frontend

#### 1. Consultation de l'état des runtimes — `GET /api/tooling/status`
* **Entrée Métier** : Requête HTTP GET vers le endpoint de diagnostic.
* **Règles d'admissibilité & Validation** : Aucune authentification bloquante requise en exécution locale.
* **Traitement & Algorithme Métier** :
  1. Inspecter la présence de `opencode` sur le PATH.
  2. Vérifier l'exécutable Plannotator sous `%LOCALAPPDATA%\plannotator\plannotator.exe`.
  3. Vérifier la connectivité au port 4000 (LiteLLM).
  4. Formater la réponse JSON structurée.
* **Résultat Métier & Mutations** : Payload JSON avec statut de chaque outil.
* **Cas de Rejet Métier** : Timeout système ; corruption de configuration locale.

#### 2. Rendu de la tuile Cyber sur le Dashboard
* **Entrée Métier** : Données JSON fournies par le endpoint d'état.
* **Règles d'admissibilité & Validation** : Rendu des badges même en cas de données partielles ou d'outil indisponible.
* **Traitement & Algorithme Métier** :
  1. Réception du flux JSON via fetch asynchrone.
  2. Mise à jour dynamique du DOM sans rechargement de page.
  3. Attribution des classes de statut (opérationnel, attention, erreur).
* **Résultat Métier & Mutations** : Tuile visuelle actualisée dans le Dashboard.
* **Cas de Rejet Métier** : Coupure réseau ou absence de réponse du backend.

### Contrats d'échange API (Interface Python, CLI & HTTP)

#### Matrice des Contrats API

| Méthode | Endpoint | Description | Auth / Rôle | Statut Réponse |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/tooling/status` | Statut de disponibilité des runtimes développeur | Local / Développeur | `200 OK` |

- **OQ-223 (Exemption Complémentaire)** : Les composants d'interface web et bindings HTML/CSS s'exécutent in-browser sans endpoints d'écriture distants `[API de soumission à définir]` (ADR-0319).

---

## Règles d'affaires

- **Lecture passive par défaut** : La tuile de statut interroge le système en lecture seule sans déclencher de processus lourd en tâche de fond.
- **Résilience aux déconnexions & Timeout** : Tout appel asynchrone de l'interface vers `/api/tooling/status` applique un délai d'attente (timeout) de 3 secondes avant d'afficher un état dégradé.
- **Concurrence & Anti-Rebond** : Protection contre le double-clic sur les boutons d'action directe pour éviter les déclenchements multiples de processus.
- **Session & Erreur d'authentification** : En cas de session expirée ou d'erreur 401 sur l'API, un message d'alerte non bloquant s'affiche sur la tuile.
- **Tolérance aux pannes** : Si un binaire retourne une valeur null ou un champ vide pour sa version, le badge affiche un statut non renseigné sans faire planter l'affichage complet.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-014)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q4** | Visibilité Dashboard & Actions Directes | **Option A (Tuile Synthétique Overview)** : Endpoint FastAPI `/api/tooling/status` sous `src/dashboard/routers/tooling.py` (≤ 300L) et tuile sur la page Overview avec badges d'état. | [KN-050](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md) · [KN-051](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-051_plannotator_workflow.md) · [ADR-014](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Intégration sur la page Overview et spécification de la tuile validées.
- [x] **Architecture & Contrats clarifiés** : Route `GET /api/tooling/status` documentée dans la matrice.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Scénarios nominal, exceptions, résilience et UX/accessibilité rédigés.
- [x] **Dépendances identifiées & levées** : Raccordement aux handlers MLOOP-220-BE et MLOOP-221-BE défini.
- [x] **Estimations et découpage validés** : Taille M (2 à 3 jours), modularité ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q4 scellé dans l'ADR-014.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-223-FE_fact_dossier.md`](../../memory/evidence/MLOOP-223-FE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-014 — Intégration Opérationnelle Tooling (EPIC-22)](../../../docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md)
- 📜 **Fiches de Savoir** : [KN-050](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md) · [KN-051](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-051_plannotator_workflow.md)
- 📋 **Épopée de rattachement** : [epic_tooling_ecosystem_harness.md](../epics/epic_tooling_ecosystem_harness.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Happy Path — Chargement & Affichage de la Tuile)
```gherkin
Fonctionnalité: Visualisation Dashboard Tooling

  Scénario: Récupération réussie du statut des runtimes
    Étant donné le serveur Dashboard mLoop en fonctionnement
    Quand le client web sollicite "GET /api/tooling/status"
    Alors la réponse HTTP est 200 OK
    Et le payload contient les états des outils OpenCode, Plannotator, Wayfinder et LiteLLM

  Scénario: Affichage des badges de statut sur la page Overview
    Étant donné l'utilisateur accédant à la page d'accueil du Dashboard
    Quand la tuile Tooling charge les données du backend
    Alors les badges d'état s'affichent avec les couleurs associées à leur disponibilité
```

### Pilier 2 : Exceptions & Rejets Métier (Indisponibilité Outil & Déconnexion)
```gherkin
Fonctionnalité: Visualisation Dashboard Tooling

  Scénario: Traitement d'un runtime non installé ou non disponible
    Étant donné un outil tiers absent de l'environnement
    Quand le backend interroge son statut
    Alors la route répond avec succès mais marque l'outil au statut indisponible
    Et l'interface affiche un badge explicite invitant à son installation

  Scénario: Réponse avec champ vide ou caractère spécial inattendu
    Étant donné des données partielles retournées par le système hôte
    Quand le routeur parse la réponse
    Alors il isole l'erreur et applique une valeur par défaut sans défaillance de la page
```

### Pilier 3 : Résilience & Mode Dégradé (Timeout & Concurrence)
```gherkin
Fonctionnalité: Visualisation Dashboard Tooling

  Scénario: Coupure réseau ou délai d'attente (timeout) de l'API
    Étant donné l'indisponibilité momentanée du serveur backend
    Quand le navigateur interroge l'endpoint
    Alors le timeout de requête est atteint après 3 secondes
    Et la tuile affiche un mode dégradé avec mention explicite

  Scénario: Protection anti-rebond sur le bouton d'action Plannotator
    Étant donné un utilisateur effectuant un double-clic intempestif sur le bouton d'ouverture
    Quand le composant traite l'événement
    Alors l'action est désactivée temporairement pour empêcher le double lancement
```

### Pilier 4 : UX & Observabilité (Accessibilité Clavier, Focus & ARIA)
```gherkin
Fonctionnalité: Visualisation Dashboard Tooling

  Scénario: Navigation accessible au clavier et conformité ARIA
    Étant donné un utilisateur naviguant sans souris dans le Dashboard
    Quand il utilise la touche Tabulation pour atteindre la tuile Tooling
    Alors l'indicateur de focus clavier est visible avec un contraste suffisant
    Et les attributs ARIA communiquent l'état opérationnel des outils aux technologies d'assistance
```