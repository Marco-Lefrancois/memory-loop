# 🏛️ Épopée — `EPIC-25-OPENCODE-ECOSYSTEM-HARNESS` : Intégration Avancée & Exploitation des Innovations OpenCode.ai

---

> **Référence d'Architecture** : [ADR-0377](../../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) (Runtimes d'Agents Aval & Herdr) · [ADR-0308](../../../../standards/adr-system/0308-continuous-semantic-evaluation-harness.md) · [ADR-0202](../../../../standards/adr-system/0202-modularite-interne-agents.md) (Modularité ≤ 300L) · [ADR-0375](../../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) (Traçabilité Radicale) · [ADR-0376](../../../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot)  
> **Composant(s)** : `Bridges/OpenCode` · `Core/HerdrAdapter` · `CLI/OpenCode` · `Pipelines/Sync` · `Tools/OpenCode`  
> **Origine / Déclencheur** : Veille technologique OpenCode (v1.18.x) : apparition du protocole ACP (Agent Client Protocol), architecture serveur/client headless (`opencode serve`), session forking déterministe, et support déclaratif des sous-agents sous `.opencode/agents/`.  
> **Statut** : `READY_FOR_DEV` — 5/5 récits validés Palier 2 (`status: READY_FOR_DEV`, `grill_me: DONE`) (PO Marco 2026-09-25)  
> **Décideurs** : PO mLoop / Architecte Agentique  

---

## 🎯 1. Contexte & Intention Stratégique

L'écosystème **mLoop** s'appuie sur une séparation stricte entre :
* **Système 1 Déterministe** : Index SQLite FTS5 (Fact-Search), Graphify, Hypergraphe, Vibe-Check, EvidencePacks.
* **Système 2 Cognitif** : Orchestrateurs et workers d'implémentation autonomes (OpenCode, Claude Code, Cline, Codex).

La plateforme **OpenCode** ([opencode.ai](https://opencode.ai)) a introduit dans ses versions v1.18.30+ des ruptures majeures qui permettent à mLoop de franchir un cap d'industrialisation :
1. **L'Agent Client Protocol (ACP)** : standardisation d'un protocole JSON-RPC typé entre éditeurs/harnais et agents (co-développé avec Zed et JetBrains). Cela ouvre la voie au remplacement des sessions de terminal PTY fragiles par un canal de communication binaire direct et sans artefact.
2. **Le Découplage Serveur Headless (`opencode serve`)** : capacité à piloter des agents d'implémentation par API HTTP REST en arrière-plan sans ouvrir de fenêtre de console.
3. **Le Session Forking Déterministe (`--fork`)** : capacité à brancher une conversation d'agent à un message précis pour tester des variantes architecturales sans perdre le contexte ni repartir de zéro.
4. **La Parité Miroir Multi-Agents (`.opencode/agents/`)** : définition d'agents primaires et secondaires (`subagent_depth: 1`, `@mentions`) directement interopérables avec les personas mLoop (`explorer`, `critic`, `craftsman`).
5. **Les Outils & Plugins TypeScript Natifs (`.opencode/tools/`)** : injection d'outils personnalisés directement consommables par le LLM d'OpenCode.

L'objectif de cette épopée est de doter mLoop d'un pont d'interopérabilité de première classe avec OpenCode, capitalisant sur ces avancées pour accélérer les cycles de développement des stories et fiabiliser les workers.

---

## 🧭 2. Vérité Terrain & Ancrage Normatif

> En application de l'**ADR-0375** (Traçabilité Radicale) et de l'**ADR-0376** (Zéro Blindspot), cette épopée s'ancre sur les sources vérifiées suivantes :

* **Source Officielle** : Spécification OpenCode CLI & Documentation `opencode.ai/docs`
* **Standard Industriel** : `Agent Client Protocol (ACP) Specification` (Zed Industries / JetBrains / OpenCode)
* **Dossier de Preuves Local** : `docs/guides/codegraph_guide.md`, `docs/guides/herdr_guide.md`, `standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md`

---

## 🗂️ 3. Décomposition des Récits (Backlog Slicing)

L'épopée est découpée en 5 récits verticaux indépendants (INVEST) :

| Identifiant | Type | Titre | Scope & Valeur Produite | Macro-Taille |
| :--- | :---: | :--- | :--- | :---: |
| **`MLOOP-250-BE`** | Feature | **Parité Miroir Automatique des Personas (`.agents/agents/` $\rightarrow$ `.opencode/agents/`)** | Synchronise les rôles mLoop (`explorer`, `critic`, `craftsman`) dans OpenCode pour permettre l'invocation native via `@mention`. | **S** |
| **`MLOOP-251-BE`** | Feature | **Bridge d'Outils Natifs TypeScript mLoop pour OpenCode (`.opencode/tools/`)** | Expose `fact_search` (FTS5) et `vibe_check` sous forme de tools TypeScript natifs appelables directement par le LLM. | **M** |
| **`MLOOP-252-BE`** | Feature | **Intégration du Session Forking dans les Rituels Grill-Me & Doubt-Driven** | Permet à l'orchestrateur de bifurquer une session OpenCode (`--fork`) lors d'arbitrages de stories ou de revues contradictoires. | **M** |
| **`MLOOP-253-BE`** | Enabler | **Adaptateur Protocolaire Expérimental OpenCode ACP (JSON-RPC)** | Construit un client ACP en Python remplaçant les PTY virtuels pour piloter les workers de stories sans pollution terminal. | **L** |
| **`MLOOP-254-FULL`** | Feature | **Commandes CLI mLoop d'Orchestration & Validation E2E OpenCode** | Ajoute les commandes souveraines `mloop opencode-sync` et `mloop opencode-status` avec validation continue pré-vol. | **M** |

---

## 🛡️ 4. Matrice d'Impact en 7 Couches (ADR-0376)

1. **Blueprints / Standards** : Enrichissement de l'ADR-0377 pour y inclure le protocole ACP et la topologie multi-agents OpenCode.
2. **Protocols** : Formalisation du protocole de synchronisation miroir `.agents/` vers `.opencode/`.
3. **ADR System** : Référencement croisé avec ADR-0308 (Évaluation sémantique) et ADR-0346 (Runtimes aval).
4. **Agents** : Capacité pour les agents mLoop d'être projetés en sous-agents OpenCode natifs.
5. **Skills** : Interaction directe des skills avec les outils `.opencode/tools/`.
6. **Code (`src/`)** : Création du package `src/bridges/opencode/` (< 300L par module).
7. **Tests & Vibe-Check** : Couverture unitaire et intégration dans la suite `pytest tests/`.
