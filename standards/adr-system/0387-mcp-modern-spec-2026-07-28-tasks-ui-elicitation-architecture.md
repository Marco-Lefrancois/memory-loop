# 🏛️ ADR-0387 : Intégration des Standards MCP Modernes 2026-07-28 (Tasks, MCP Apps, Elicitation & Header Routing)

- **Statut** : ACCEPTÉ
- **Date** : 24 septembre 2026
- **Décideurs** : Marco (Utilisateur) & Antigravity (Agentic Architect)
- **En lien avec** :
  - [ADR-0001](0001-python-state-graph.md) (Python State Graph & Moteur Déterministe)
  - [ADR-0202](0202-modularite-interne-agents.md) (Modularité ≤ 300L & Décomposition)
  - [ADR-0308](0308-mcp-prompts-and-evals-engine.md) (MCP Prompts & Progressive Disclosure)
  - [ADR-0374](0374-standard-mcp-cyber-resilience-et-workflows-deterministes.md) (Cyber-Résilience MCP & Guardrails)
  - [ADR-0375](0375-project-lifecycle-5-phases-and-analysis-types.md) (Cycle de Vie Unifié en 5 Phases)
  - [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Standard de Rigueur 360° Zéro Blindspot)
  - [ADR-0386](0386-gouvernance-github-rulesets-pull-requests-et-garde-fous-phase-5-ship.md) (Gouvernance GitHub & Gate 5)

---

## 🧭 1. Contexte & Défaillances Actuelles

L'écosystème mLoop s'est historiquement structuré autour de ponts MCP locaux hébergés dans `src/bridges/` (`mcp_loop_mem.py`, `mcp_graphify.py`, `mcp_crawler.py`, `mcp_herdr.py`). 

L'analyse de l'usage en production a mis en lumière **trois limitations techniques sévères** imposées par la spécification MCP originelle (legacy 2025) :

1. **La tyrannie du Timeout synchrone sur les tâches longues** :
   Les requêtes JSON-RPC standard imposent un modèle requête/réponse synchrone. Pour les tâches d'ingénierie lourdes (tests `pytest` multi-modules, compaction de mémoire, extraction de règles métier legacy, audit de 12 récits simultanés), la connexion franchit régulièrement les plafonds de timeout (`timeout: 15000` ou `60000`), provoquant des crashs de session côté IDE hôte.

2. **L'impasse des questions interactives en mode non-supervisé (*Unattended Workers*)** :
   Le protocole *Grill-with-Docs* (Phase 2 PLAN) exige des arbitrages de l'ingénieur métier. Or, lorsqu'un worker s'exécute en sous-agent ou en arrière-plan, toute tentative de lecture interactive (`input()`) bloque indéfiniment ou fait échouer le processus. Les agents sont actuellement forcés d'adopter la règle de confinement : *« Tu ne poses JAMAIS de questions interactives »*.

3. **L'exil hors-IDE des livrables visuels interactifs** :
   mLoop produit des visualisations à forte valeur ajoutée : **Archify Cockpit** (cartographie vivante animée) et **DrawDB** (modélisation relationnelle de bases de données). Aujourd'hui, l'utilisateur est forcé de démarrer manuellement un serveur FastAPI (`python src/swarm.py dashboard`) et d'ouvrir un navigateur web externe, créant une rupture de contexte cognitive.

---

## 💡 2. Décisions d'Architecture

L'adoption de la révision **MCP 2026-07-28** et de ses extensions officielles résout ces trois impasses à travers quatre piliers d'ingénierie :

```
┌────────────────────────────────────────────────────────────────────────┐
│            ARCHITECTURE MCP MODERNE 2026-07-28 (ADR-0387)              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  PILIER 1    │             │  PILIER 2    │             │  PILIER 3    │
│  Tasks Async │             │  MCP Apps    │             │  Elicitation │
│  Pattern     │             │  (ui://)     │             │  Form Mode   │
└──────┬───────┘             └──────┬───────┘             └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                       PILIER 4                          │
       │       Stateless Core & Header Routing Multi-IDE         │
       └─────────────────────────────────────────────────────────┘
```

### Pilier 1 : Découplage Asynchrone via l'Extension `Tasks` (`io.modelcontextprotocol/tasks`)
* Remplacement du blocage synchrone pour les opérations dépassant 5 secondes.
* Le pont MCP renvoie immédiatement un **`task handle` persistant** avec les statuts : `working`, `input_required`, `completed`, `failed`, `cancelled`.
* Intégration directe avec le démon de multiplexage `herdr` et les commandes `worker-spawn` et `vibe-check`.

### Pilier 2 : Intégration Native des Visualiseurs via « MCP Apps » (`io.modelcontextprotocol/ui`)
* Les visualisateurs **Archify Cockpit** et **DrawDB ERD** sont exposés sous forme de ressources `ui://archify/cockpit` et `ui://drawdb/schema`.
* L'IDE hôte rend ces pages dans un `iframe` sandboxé directement dans l'interface de discussion de l'agent, garantissant une boucle de feedback visuelle sans quitter le code.

### Pilier 3 : Arbitrages d'Architecture Interactifs via l'« Elicitation »
* Implémentation du mode **Form Mode (In-Band)** pour le protocole *Grill-with-Docs* : l'agent émet une demande d'élicitation structurée via JSON-Schema (options A/B, choix de profils d'API, validation de DoR).
* L'IDE affiche un widget interactif bloquant uniquement la tâche ciblée, sans geler le worker ni le thread principal.

### Pilier 4 : Routage Stateless & En-têtes HTTP Modernes
* Adoption de la déclaration explicite de version via l'en-tête `MCP-Protocol-Version: 2026-07-28`.
* Injection des noms de méthodes et d'outils dans les en-têtes HTTP pour permettre un routage direct par passerelle sans parsing JSON-RPC complet.

---

## ⚖️ 3. Conséquences & Non-Régression

### Positives
* **Élimination totale des timeouts** sur les commandes lourdes mLoop.
* **Adoption facilitée pour les collègues** grâce aux maquettes et schémas visibles directement dans l'IDE.
* **Résolution propre du dialogue interactif** pour les workers autonomes via formulaires natifs.

### Rétrocompatibilité & Garde-fous (Non-Régression)
* **Mode Hybride (Graceful Degradation)** : Si un client MCP (ex: ancien client stdio) ne négocie pas l'extension `Tasks` ou `ui://`, le bridge retombe automatiquement en mode synchrone standard et renvoie l'URL localhost ou le résultat texte brut.
* **Isolation AST & Conformité ADR-0202** : Chaque nouveau module de bridge respectera strictement la limite de 300 lignes / 15 Ko.
