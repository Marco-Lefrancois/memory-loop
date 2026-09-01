# mLoop - 07. Piliers, Maturité Agentique & Directives

Ce chapitre cartographie les concepts fondamentaux qui structurent l'architecture de Memory Loop (mLoop), détaille la matrice de maturité de l'écosystème et fournit les règles de rédaction des directives d'affaires.

## 📋 1. Cartographie Architecturale des 5 Piliers mLoop (v2.0.0)

Dans sa version v2.0.0, l'implémentation physique et conceptuelle des 5 piliers fondateurs s'articule ainsi :

### A. Memory (Mémoire et Contexte)
*   **Objectif** : Éliminer l'amnésie des agents et assurer la continuité du projet sur le long terme.
*   **Fichiers physiques** : Le graphe sémantique (`Projects/<nom_projet>/memory/knowledge_graph.json` et `graphify-out/graph.json`) servant de SSOT.
*   **Moteur** : Moteur sémantique *L3 In-Memory* accélérant les recherches sémantiques 1-hop via le pont MCP `mcp_loop_mem.py` et les commandes CLI `graphify query` / `graphify explain` / `graphify path`.
*   **Protocole** : Règle absolue du *Search-First Protocol* (interdiction de proposer une architecture sans interroger le graphe).

### B. Skills (Compétences Portables & AP 1.0)
*   **Objectif** : Donner des capacités d'action physiques à l'agent sans surcharger son contexte global.
*   **Fichiers physiques** : Le sous-système de 21+ manifestes `.agents/skills/` (contenant `SKILL.md` et scripts associés), empaquetable au standard Agent Plugins 1.0 (`.agents/plugin.json`, `.agents/mcp.json`).
*   **Divulgation Progressive** : Chargement à la demande (`view_file`) de la compétence nécessaire selon la phase active pour préserver le budget d'instructions.
*   **Handoff** : Le skill `handoff` génère le rapport de transition `memory/sessions/handoff.md` lors de la fin de session.

### C. Soul (Identité et Garde-fous)
*   **Objectif** : Aligner le comportement cognitif de l'agent (ton Senior Tech Lead, "Zero-Fluff") et prévenir les initiatives dangereuses (Scope Creep).
*   **Fichiers physiques** : Le fichier `.agents/soul.json` et les directives strictes (`tech.md`, `business.md`, `AGENTS.md`).
*   **Protocole** : Alignement strict sur les exclusions (Negative Prompting) pour rejeter les suggestions hors-périmètre.

### D. Session Recall (Temporalité, State Checkpointing & Focus)
*   **Objectif** : Permettre le travail asynchrone sur le temps long et gérer les interruptions de session (Human-In-The-Loop).
*   **Fichiers physiques** : Le nœud d'état global `ML_ACTIVE_STATE` persistant dans le graphe, les checkpoints `.mloop_tmp/checkpoints/` et l'interface `backlog/sprint_backlog.md`.
*   **Protocole** : Verrouillage d'attention via `python src/swarm.py focus --project <p> --story <s>`. Mode *Stop & Ask (HITL strict)* figé sur le disque en cas d'ambiguïté fonctionnelle.

### E. Validation (Audit EvidencePack & Conformité QA)
*   **Objectif** : Validation déterministe s'assurant du respect strict du contrat de story et de l'absence de régressions.
*   **Fichiers physiques** : Le linter sémantique `wikifix`, le moteur `EvidencePackEngine` (`memory/evidence/<STORY_ID>_evidence.json`), la suite `aoep` et le calculateur de score INVEST.
*   **Protocole** : Validation systématique contre les **4 Piliers Gherkin** (Nominal, Rejet/Exception, Mode Dégradé, UX/Observabilité) et rétroaction RHO via `rho_rules.yaml`.

---

## 📈 2. Matrice de Maturité Agentique

L'ingénierie agentique est catégorisée en trois niveaux distincts selon l'autonomie et le maintien d'état :

### Niveau 1 : Le Pipeline Procédural (Stateless DAG)
*   **Description** : Exécution prédictible de tâches isolées (ETL, Web Crawl, Ingestion).
*   **Harness** : Minimaliste.
*   **Mémoire** : Amnésie cognitive totale. Aucun contexte persistant entre deux exécutions.

### Niveau 2 : Le Copilote Contextuel (Stateful Workspace)
*   **Description** : Partenaire interactif dans l'IDE (ex: Antigravity, Claude Code, Cursor) exécutant des compétences (`.agents/skills/`) sous supervision humaine.
*   **Mémoire** : Persistance de la session active (chat), lecture de `AGENTS.md` et des fichiers ouverts du workspace.

### Niveau 3 : L'Écosystème Cognitif (State-Machine Swarm & Graph DAG)
*   **Description** : Swarm d'agents autonomes (mLoop) pilotés par contrat, capables de planifier, d'interroger et de exécuter des topologies DAG (Pattern Diamant, Risk Router, Evidence Reducer).
*   **Mémoire** : Accès et mise à jour permanents du Graphe de Connaissances (SSOT) via MCP et state checkpointing.
*   **Gouvernance** : Utilisation stricte des contrats de story (SCC) et packs d'évidence validés déterministement par Sentinel.
*   **Sécurité** : Intégration obligatoire d'un **Coupe-circuit** (Circuit Breaker), Token Budget Guard et auto-étalonnage continu (`calibrate`).

---

## ✍️ 3. Directives & Bonnes Pratiques de Rédaction (Zero-Fluff)

Les directives (`tech.md` et `business.md`) sont les Lois Fondamentales de l'écosystème :

1.  **Le Standard Zero-Fluff** : Les modèles de raisonnement étant très sensibles au bruit de contexte, proscrire le verbiage descriptif. Remplacer les formulations vagues par des contraintes techniques ou métier strictes et impératives.
2.  **Rédiger `tech.md` (La Loi Technique)** :
    *   Préciser la stack technique et les versions exactes.
    *   Imposer les contraintes architecturales (ex: interdiction pour le domaine d'importer l'infrastructure).
    *   Exiger la couverture et le framework de test.
3.  **Rédiger `business.md` (La Loi Métier)** :
    *   Définir le glossaire (Lexique strict pour éviter la paraphrase).
    *   Lister explicitement les **Exclusions** (Negative Prompting) pour bloquer les fonctionnalités non planifiées.
4.  **L'Évolution via l'Agent Plan** : Ces fichiers ne sont pas figés. Pendant la phase de *Grill with Docs*, l'agent `plan` interroge l'utilisateur et met automatiquement à jour ces fichiers à la racine du projet pour cristalliser les décisions.
