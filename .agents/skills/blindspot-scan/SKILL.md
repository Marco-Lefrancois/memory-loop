---
name: blindspot-scan
description: Audit proactif d'angles morts techniques (compatibilité runtimes, dépendances diamant, race conditions). Use when analyzing third-party dependencies, refactoring core architecture, or detecting multi-codebase blindspots.
---

# Skill : Blind-Spot & Comparative Scan (ADR-0306)

## Overview
Ce skill réutilisable permet aux agents (`plan`, `orchestrator`, `build`) d'exécuter un audit proactif d'angles morts techniques et une analyse comparative inter-codebases dès qu'une nouvelle dépendance, une migration ou un composant d'architecture est analysé.

---

## Directives d'Investigation Croisée

### 1. Audit Proactif des 4 Vecteurs d'Angles Morts
Lors de toute analyse technique, explorez la codebase et la documentation sous 4 angles agnostiques :

1. **Matrice de Compatibilité Runtimes / Frameworks** :
   * Inspectez les cibles de build (`csproj`, `package.json`, `build.gradle`, etc.) et comparez-les aux prérequis exigés par les dépendances tierces.
2. **Conflits de Dépendances Transitives ("Diamant") & Blast Radius** :
   * Exécutez `python src/swarm.py code-impact --symbol <NomDuComposant>` ou l'outil MCP `codegraph_explore` pour calculer l'arbre complet d'impact et la propagation des changements.
   * Recherchez les librairies tierces empaquetées ou partagées (`Newtonsoft`, `Mopups`, `lodash`, `jackson`, etc.) pour détecter d'éventuelles collisions de versions.
3. **Séquencement, Race Conditions & Dispatch Dynamique** :
   * Inspectez les points d'entrée (`MauiProgram.cs`, `index.js`, `main.py`, `App.tsx`) et vérifiez si l'initialisation asynchrone d'un SDK peut provoquer des fuites de données ou des crashs avec des composants synchrones (analytics, logging).
   * Utilisez CodeGraph pour cartographier les ponts natifs (Swift ↔ ObjC, React Native TurboModules/Fabric) et les émissions d'événements.
4. **Contraintes Debug vs Production & Couverture des Tests** :
   * Vérifiez l'impact des optimisations de build (`Trimming`, `NativeAOT`, `Tree-shaking`, minification) qui fonctionnent en local/Debug mais risquent d'éliminer des symboles vitaux en Production/Release.
   * Exécutez `python src/swarm.py code-affected` pour identifier exactement la suite de tests unitaires et d'intégration à revalider.

---

### 2. Dimension d'Analyse Comparative & Demande Active de Baseline

* **Scan Multi-Codebases** :
  * Si le projet comporte plusieurs applications sœurs (ex: `App A`, `App B`, `App C`), comparez l'implémentation du composant dans chaque dossier d'application pour faire émerger les divergences.
* **Réflexe de Demande Active de Baseline** :
  * Si aucune codebase comparative n'est présente dans le workspace, posez proactivement la question :
    > *"Existe-t-il une application de référence, une codebase comparative ou une version legacy pour valider ce comportement ?"*

---

### 3. Production Déterministe de la Trinité d'Artefacts

En cas d'impasse ou de risque majeur identifié :
1. **Rédiger l'OQ-XXX** : Ajouter l'entrée dans `docs/04-transverse/00-questions-ouvertes.md`.
2. **Créer le Spike `US-SPIKE-XXX.md`** : Positionner la story au statut `OPEN` et en **Priorité #1** dans `sprint_backlog.md` (avec test obligatoire en build Release).
3. **Rédiger le Mémo Technique** : Synthèse explicative destinée aux développeurs/fournisseurs.
