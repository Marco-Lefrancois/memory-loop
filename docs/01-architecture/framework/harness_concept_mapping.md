
## Annexe : Cartographie Exacte du Concept "Harness" dans mLoop (v2.0.0)

Pour répondre à la taxonomie d'un système de *Harness*, voici l'alignement de mLoop v2.0.0 sur les piliers fondamentaux :

### 1. Orchestration (Le Cerveau IDE-Driven & Topologie DAG)

Dans mLoop, l'Orchestrateur associe **l'IDE Agentique** (Système 2) à l'exécution de topologies **Graph Engineering (DAG Multi-Agents)** (Système 1).

*   **Memory (Mémoire à Long Terme)** : Implémentée via le Graphe de Connaissances **Graphify** (`knowledge_graph.json` et `graphify-out/graph.json`), indexation AST et RAG sémantique *L3 In-Memory*, accessible via `graphify query` et le pont MCP `mcp_loop_mem.py`.
*   **Context Constructor (Constructeur de Contexte)** : Assembly dynamique du contexte avec Token Budget Guard (< 8000 jetons) et préchargement d'engrammes en RAM Cache (`loop_mem_preload_context`).
*   **Reasoning Substrate (Substrat de Raisonnement)** : Les modèles sous-jacents (Gemini 3 Flash/Pro, DeepSeek R1 local) sculptés par `.agents/soul.json` et les directives (`tech.md`, `business.md`, `AGENTS.md`).
*   **Skill Router (Routeur de Compétences & AP 1.0)** : Routage dynamique vers les 21+ compétences portables au standard **Agent Plugins 1.0** (manifeste `.agents/plugin.json`, `.agents/mcp.json`). Divulgation progressive à la demande.
*   **Tools & Subagents (Topologie DAG Multi-Agents)** :
    *   *Outils* : Ponts MCP locaux (`mcp_loop_mem.py`, `mcp_crawler.py`) et Kernel CLI (`src/swarm.py`).
    *   *Topologie DAG* : Nœuds spécialisés (Scoper, Fan-Out, Barrier, Reducer Node pure Python, Risk Router, Evaluator Node).

### 2. Gouvernance & Validation Déterministe (Le Moteur Kernel)

Gouvernance extraite du LLM et ancrée dans le moteur déterministe Python :

*   **Gouvernance & Story Guard** : Assurée par `story_guard.py` qui verrouille physiquement les écritures hors-périmètre du contrat (SCC).
*   **Evidence Enforcement** : Generation autonome de packs d'évidence d'audit `memory/evidence/<STORY_ID>_evidence.json` via `EvidencePackEngine`.
*   **Vérification & Auto-Repair** : Duo déterministe `python src/swarm.py wikifix` et `python src/swarm.py calibrate` (auto-étalonnage 8/8 PASS). Audit des 4 Piliers Gherkin, suite `aoep` et score INVEST.
*   **Gouvernance Jira (Story-Only)** : Synchronisation bidirectionnelle exclusive en tickets de type Story (`jira_sync`).
