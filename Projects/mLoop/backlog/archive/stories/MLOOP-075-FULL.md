---
id: MLOOP-075-FULL
jira_key: '-'
epic_key: EPIC-7-AGENTIC-OBSERVABILITY
status: SHIPPED
type: Feature
title: Explorateur Interactif Knowledge Graph et Base SQLite Souveraine
layer: fullstack
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-7-AGENTIC-OBSERVABILITY] Explorateur Interactif Knowledge Graph et Base SQLite Souveraine (MLOOP-075-FULL)

## Description
**En tant qu'** Architecte et Développeur du framework mLoop,  
**je veux** explorer visuellement le graphe de connaissances Graphify (`graph.html`) et requêter les bases SQLite locales en direct dans un 9e onglet dédié du Cockpit,  
**afin d'** inspecter les relations entre standards, modules et mémoires de façon souveraine et sans quitter l'interface d'orchestration.

---

## Contexte
Le projet mLoop possède déjà un graphe de connaissances complet généré par Graphify (`Projects/mLoop/graphify-out/graph.html` de 522 Ko) ainsi que des bases SQLite hautement structurées (`memory/standards_graph.db` selon ADR-0379 et `memory/token_ledger.db`).
Ce récit crée le 9e onglet du Cockpit 2.0 (« 🕸️ GRAPH & DATABASE ») pour intégrer le visualiseur interactif de graphe (avec bascule plein écran) et un explorateur SQLite en lecture seule permettant de parcourir les tables et relations du framework.

---

## Spécifications de l'Interface & UX

### Macrostructure & États de surface
- **Bouton Onglet Navigation** : Ajout du 9e bouton d'onglet `[ 🕸️ GRAPH & DATABASE ]` dans la barre de navigation du Cockpit.
- **Section Haute (Visualiseur de Graphe)** : Cadre d'intégration fluide du visualiseur Graphify avec commandes de zoom, filtrage de clusters et bouton plein écran.
- **Section Basse (Explorateur SQLite)** : Sélecteur de base de données (`standards_graph.db`, `token_ledger.db`), liste des tables disponibles et tableau interactif des enregistrements réels avec pagination.

### Feedback Utilisateur
- Chargement asynchrone non-bloquant du graphe avec squelette visuel.
- Copie rapide des requêtes SQL ou empreintes SHA-256 en un clic.

---

## Opérations Métier & Logique Backend

### Matrice des Opérations Backend
| Opération Métier | Contrat / Trigger | Validation & Préconditions | Succès Observable | Gestion Erreurs |
| :--- | :--- | :--- | :--- | :--- |
| **[Flux Graphe HTML]** | `GET /api/graph/html` | Projet valide spécifié (ex. `mLoop`) | Fichier HTML interactif servi avec headers MIME adaptés | Retour 404 propre si graphe non encore compilé |
| **[Métadonnées Graphe]** | `GET /api/graph/metadata` | Présence de `graph.json` ou `manifest.json` | Résumé JSON : nombre de nœuds, liens, god-nodes | Fallback sur valeurs par défaut |
| **[Exploration SQLite Read-Only]** | `GET /api/database/tables?db=<nom>` | Base autorisée dans la whitelist locale | Schéma des tables, colonnes et comptage de lignes | Rejet 403 si base non autorisée |

---

## Règles d'affaires
* **[Confinement Read-Only Absolu]** : L'explorateur SQLite ne doit exécuter aucune requête de mutation (interdiction formelle de INSERT, UPDATE, DELETE, DROP).
* **[Souveraineté des Chemins]** : Seules les bases situées sous `memory/` ou `Projects/<nom>/memory/` peuvent être ouvertes par l'API.
* **[Persistance de l'Onglet F5]** : Si l'utilisateur consulte l'onglet Graph & Database, le rechargement de la page (F5) le maintient sur cette vue via `CockpitStorage`.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Explorateur Interactif Knowledge Graph et Base SQLite Souveraine

  # 1. CHEMIN NOMINAL (Happy Path & Navigation Graphe)
  Scénario: Consultation interactive du graphe Graphify du projet mLoop
    Étant donné un projet mLoop disposant d'un export graph.html valide
    Quand l'utilisateur sélectionne l'onglet "GRAPH & DATABASE"
    Alors le graphe interactif s'affiche dans le panneau dédié
    Et l'utilisateur peut zoomer et explorer les connexions sémantiques

  # 2. EXCEPTIONS & REJETS MÉTIER (Projet sans Graphe Compilé)
  Scénario: Affichage gracieux lorsqu'un projet ne possède pas de graphe compilé
    Étant donné un projet pour lequel la commande graphify n'a pas encore été exécutée
    Quand l'utilisateur consulte l'onglet Graph & Database
    Alors un panneau d'information invite à lancer la commande "python src/swarm.py graph-run"
    Et aucun message d'erreur bloquant n'interrompt le dashboard

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Sécurité de l'Explorateur SQLite)
  Scénario: Rejet strict de toute tentative d'accès à un fichier hors périmètre
    Étant donné une requête API tentant d'ouvrir un fichier système externe
    Quand l'endpoint /api/database/tables reçoit la demande
    Alors la requête est rejetée avec un refus d'accès 403
    Et aucune donnée sensible n'est divulguée

  # 4. UX & OBSERVABILITÉ (Inspection des Tables SQLite dans le Cockpit)
  Scénario: Affichage paginé des enregistrements de la base standards_graph.db
    Étant donné la sélection de la base standards_graph.db
    Quand l'analyste clique sur la table des ADRs
    Alors le tableau affiche les colonnes et les lignes réelles
    Et la pagination permet de feuilleter les données en toute fluidité
```
