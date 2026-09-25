---
id: MLOOP-104-FE
jira_key: '-'
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Feature
title: Visualiseur Interactif Force-Directed Graph dans le Cockpit Web
tags: [dashboard, graph-ui, visualizer, force-directed, cytoscape, cockpit]
status: SHIPPED
layer: frontend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-10-SOVEREIGN-EXCELLENCE] Visualiseur Interactif Force-Directed Graph dans le Cockpit Web (MLOOP-104-FE)

---

## Description
**En tant que** Lead Développeur / Pilote mLoop,  
**je veux** disposer d'un canevas interactif de visualisation de graphe par forces directes (Force-Directed Graph) dans le cockpit web,  
**afin d'** explorer visuellement les nœuds d'ADR, les règles de gouvernance et les dépendances entre stories en identifiant immédiatement les clusters et chemins d'impact critiques.

---

## Contexte & Périmètre

### Contexte Métier
Le cockpit web de supervision (`http://127.0.0.1:8080`) dispose d'un onglet Graph Database exposant les données tabulaires et statistiques de la base SQLite `StandardsGraph`. Cependant, l'analyse des relations complexes et des chemins d'impact à plusieurs sauts est fastidieuse sous forme textuelle. L'intégration d'une visualisation graphique vectorielle fluide (via Cytoscape.js ou Force Graph Canvas léger embarqué localement sans CDN externe) apporte une compréhension spatiale immédiate de la topologie du projet.

### In-Scope
- Intégration du composant canevas interactif dans `src/dashboard/static/index.html` et son router dédié.
- Rendu des nœuds typés avec codes visuels distincts : ADRs (bleu/violet), RHO Rules (ambre), User Stories (émeraude).
- Rendu des arêtes pondérées avec mise en exergue des relations d'impact direct au survol (hover 1-hop).
- Filtres interactifs par type d'entité, niveau d'impact et épopée parente.
- Tiroir latéral (drawer) contextuel affichant les détails complets du nœud sélectionné au clic.
- Respect rigoureux des 4 états de surface de l'interface (vide, chargement, affichage réseau et panneau d'inspection).

### Out-of-Scope
- Édition directe ou modification en glisser-déposer de la base de données via l'interface graphique.
- Recours à des bibliothèques logées sur des CDN tiers nécessitant une connexion internet active.

---

## Critères d'acceptation

### Spécifications de l'Interface & UX

- **Macrostructure & États de surface** : L'écran respecte les 4 états de surface : Initial/Vide (indication claire si aucun graphe n'est synchronisé), Chargement (animation discrète pendant la récupération des nœuds SQLite), Rendu Réseau (graphe spatialisé fluide) et Panneau d'inspection latéral (métadonnées détaillées du nœud cliqué).
- **États d'Interaction (signifiants)** :
  - *Default* : Tous les nœuds et arêtes sont affichés avec une opacité standard de 80%.
  - *Hover* : Le nœud survolé et ses voisins directs 1-hop sont mis en surbrillance à 100%, tandis que le reste du graphe passe en arrière-plan estompé (opacité 20%).
  - *Click / Active* : Centrage automatique de la caméra sur le nœud sélectionné et ouverture du tiroir latéral d'informations.
  - *Filtre / Bouton Bascule* : Filtrage instantané des nœuds par catégorie sans rechargement complet de la page.
- **Feedback Utilisateur** : Indicateur visuel du nombre exact de nœuds et arêtes visibles, badge de statut de fraîcheur de la base SQLite et bouton de réinitialisation du zoom (Fit to View).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Visualiseur Interactif Force-Directed Graph dans le Cockpit Web

  # CHEMIN NOMINAL
  Scénario: Rendu fluide du réseau de connaissances et sélection de nœud
    Étant donné un utilisateur naviguant sur l'onglet Graph Database du cockpit
    Quand la page charge les entités de la base de données locale
    Alors le canevas affiche la topologie complète des nœuds et arêtes interconnectés
    Et le clic sur un nœud d'ADR ouvre le tiroir latéral affichant son résumé et ses règles dérivées

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Affichage explicite de l'état vide en l'absence de données de graphe
    Étant donné une base SQLite nouvellement initialisée sans aucun nœud
    Quand le visualiseur tente d'afficher le canevas
    Alors un état de surface vide explicite invite à exécuter la commande de synchronisation
    Et aucun plantage de script JavaScript ne se produit

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Maintien d'un framerate fluide sur un volume important de nœuds
    Étant donné un graphe dense comportant plus de 500 nœuds et 1000 relations
    Quand l'utilisateur effectue un zoom ou un panoramique rapide
    Alors l'animation de rendu demeure fluide sans saccade visible de l'interface
    Et le moteur de simulation physique stabilise les positions rapidement

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Surbrillance contextuelle des relations 1-hop au survol
    Étant donné l'affichage du réseau de connaissances
    Quand le pointeur survole un nœud de story spécifique
    Alors seuls ses antécédents et descendants directs restent lumineux
    Et les nœuds non connectés voient leur opacité temporairement atténuée
```
