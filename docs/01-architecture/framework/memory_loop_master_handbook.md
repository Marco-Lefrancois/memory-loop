# 📖 Manuel de Référence Master : L'Écosystème Memory Loop (mLoop)

> **Version :** v2.0.0-mLoop | **Standard :** mLoop Pure Core Protocols & Agent Plugins 1.0 (ADR-0309)
> **Status :** FULLY AUTONOMOUS (Event-Driven Cognitive Swarm & Graph DAG)
> **Destination :** Document source principal (Guide exhaustif Concepts, Méthodes, Implémentations et Outils)

---

## 🏛️ 1. L'AGENTIC COWORKER FRAMEWORK (Modèle Double Couche)

**Memory Loop - Autonomous Engine (mLoop)** est un framework de développement logiciel autonome focalisé sur l'Analyse Fonctionnelle, l'Architecture système et la Validation déterministe. Il repose sur une architecture **Harness Engineering** pour éliminer la bureaucratie des scripts rigides. L'Orchestrateur est votre **IDE Agentique**, déléguant la logique métier aux **Pipelines** (`src/pipelines/`) et les capacités aux **Skills Portables** manifestes (`.agents/skills/`).

### 🧠 Couche 1 : L'Ontologie du Coworker (L'ÊTRE)
Cette couche définit l'identité, les capacités et la résilience interne de l'agent.
1. **Memory** : Mémoire à long terme stockée sous forme de graphe (`graphify-out/` et `knowledge_graph.json`), évitant l'amnésie via le moteur sémantique L3 In-Memory.
2. **Skills (Compétences Portables AP 1.0)** : Les 21+ compétences d'action de l'agent (manifestes `.agents/skills/`), évoluant via RHO et le moteur Calibrate.
3. **Soul (Identité)** : Le persona professionnel, le ton (Zero-Fluff), la langue et les valeurs, défini dans `.agents/soul.json`.
4. **Session Recall** : Persistance de l'état actif (phase, story, focus) et checkpoints (`.mloop_tmp/checkpoints/`) permettant de reprendre le fil après une pause.

### ⚙️ Couche 2 : Le Protocole Opérationnel (Le FAIRE)
Cette couche régit l'interaction de l'agent avec le code, le projet et l'humain.
1. **Délégation Asymétrique & Graph DAG** : L'IDE gère la stratégie et délègue l'exécution aux topologies DAG (Pattern Diamant, Risk Router, Evidence Reducer).
2. **Directives-Driven** : Alignement strict sur `tech.md`, `business.md` et `AGENTS.md`.
3. **Graphe Cognitif Vivant** : "Search-First" obligatoire (`graphify query`, `loop_mem_search`). Interrogation du graphe avant de scanner le disque.
4. **Cycle Spec-Driven en 5 Phases** : Évolution stricte : `[1] SPEC` $\rightarrow$ `[2] PLAN` $\rightarrow$ `[3] BUILD` $\rightarrow$ `[4] VALIDATE` $\rightarrow$ `[5] SHIP`.
5. **Story Constraint Contract (SCC), EvidencePacks & PRD** : Frontière absolue d'exécution protégée physiquement par `story_guard.py` et auditée par `EvidencePackEngine`.

### Le Principe Zéro-Bureaucratie (Zero-Fluff)
*   **Haute Densité Informationnelle** : Toutes les interfaces CLI et logs sont textuels et épurés.
*   **Souveraineté Locale & Portabilité** : Exécution locale souveraine avec compatibilité multi-clients (Cursor, VS Code, Copilot, Codex, Kiro) via le package Agent Plugins 1.0.

---

## 👥 2. LE CATALOGUE DES AGENTS D'IDE & ROUTAGE SOUVERAIN

L'écosystème utilise un routage sémantique entièrement local et souverain pour préserver l'isolation.

### 👑 orchestrator (Session & Workflow Pilot)
* **Rôle** : Supervision du flux global, aiguillage adaptatif du cycle en 5 phases et exécution du pipeline `graph-run`.
* **Permissions** : Lecture/écriture du Graphe SSOT et pilotage du Kernel `swarm.py`.

### 🧠 plan (Strategic & Architecture Engine)
* **Rôle** : Protocole "Grill-with-Docs", gestion du `CONTEXT.md` (Ubiquitous Language), découpage du backlog en **Stories Verticaux**, et génération des PRD et SCC.
* **Permissions** : Écriture sur les SCC, le PRD, les ADRs et la matrice d'évidence.

### 🛡️ validate / sentinel (Validation & Audit QA Engine)
* **Rôle** : Audit de conformité par rapport aux directives (`tech.md`/`business.md`), contrôle des 4 piliers Gherkin, exécution du linter sémantique (`wikifix`), suite `aoep`, EvidencePackEngine et calcul du Score INVEST.
* **Permissions** : Audit global et exécution des linters déterministes.

### 🔨 build (mLoop Self-Dev Engine)
* **Rôle** : réservé exclusivement au développement guidé par les tests unitaires (TDD) du framework mLoop (`C:\Memory Loop\src`). Pour les projets clients, l'implémentation applicative est déléguée au développeur humain.

---

## 🔄 3. DÉCLENCHEMENT ÉVÉNEMENTIEL (mLoop Event Bus)

Le cycle est piloté par l'IDE et les pipelines dynamiques :
* **Boot Sequence Anti-Amnésie** : Exécution mécanique en 5 étapes CLI au démarrage de toute session.
* **Transition PLAN $\rightarrow$ BUILD $\rightarrow$ VALIDATE** : Quand le "Grill with Docs" est complété et validé, la story passe en `READY_FOR_DEV`. Lors de la livraison, Sentinel s'active pour l'audit EvidencePack et le score INVEST.
* **Validation & Auto-Repair** : `python src/swarm.py wikifix` et `python src/swarm.py calibrate` s'assurent de l'intégrité globale.

---

## 📜 4. PROTOCOLE DE PRÉVENTION DU DRIFT (Golden Rules)
1. **Isolation Applicative Client** : mLoop se consacre à l'analyse métier, l'architecture et la validation. Seul le code interne de mLoop (`src/`) peut être modifié par l'agent.
2. **Vertical Slicing Only** : Chaque story doit être livrable et fonctionnelle de bout-en-bout. Pas de découpage horizontal technique.
3. **Graphify-First (Search-First)** : Toujours interroger le graphe ou le code source localement avant de demander à l'humain.
4. **Gouvernance Jira (Story Only)** : Les synchros Jira via `python src/swarm.py jira_sync` mappent strictement les récits locaux vers des tickets de type **Story** (pas de Sub-task).
