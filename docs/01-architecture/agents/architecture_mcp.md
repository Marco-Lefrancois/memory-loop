# Architecture et Modèle Backend / Skills (mLoop)

Pour éliminer la bureaucratie des scripts rigides et la redondance des appels API LLM, l'écosystème **Memory Loop** opère comme un **Backend d'État (State & Validation)** entièrement piloté par votre **IDE Agentique** (Antigravity, Claude Code, OpenCode).

Le "Cerveau" (Orchestration, Planification, Audit) réside intégralement dans l'IDE (via les `.agents/skills/`), tandis que le "Moteur" mLoop (`src/`) fournit le cadre déterministe de validation et d'intégration via le standard MCP (Model Context Protocol).

## Couche 1 : L'Ontologie du Coworker (L'ÊTRE - IDE Agentique)
Cette couche définit l'identité et les capacités de votre IDE.
1. **Memory** : Mémoire à long terme stockée sous forme de graphe SQLite (Graphify), interrogée par l'IDE via les serveurs MCP (`mcp_loop_mem.py`).
2. **Skills (Compétences)** : Les directives Markdown injectées dans l'IDE (ex: `plan`, `build`). Elles remplacent les anciens scripts Python d'orchestration.
3. **Soul (Identité)** : Le persona professionnel, défini dans `.agents/soul.json`.
4. **Session Recall** : L'IDE maintient le contexte de la session active via l'historique conversationnel.

## Couche 2 : Le Protocole Opérationnel (Le FAIRE - Backend mLoop)
Le socle applicatif Python se concentre strictement sur l'intégrité de l'état.
1. **Délégation Sémantique (A-P-QA)** : L'IDE orchestre le cycle : `[A] Analyze` -> `[P] Plan` -> `[QA] Functional Audit`.
2. **Cadre de Directives** : Alignement strict sur `directives/tech.md` et `business.md`.
3. **Linter Sémantique (WikiFix)** : L'IDE invoque la pipeline Python `python src/swarm.py wikifix` pour l'audit sémantique (Auto-Healing des callouts, vérification de l'isolation technique).
4. **Synchronisation (Jira Sync)** : Intégration déterministe avec les plateformes externes (`python src/swarm.py jira_sync`).
5. **Score INVEST** : La frontière ultime. Aucun backlog n'est validé sans un excellent score INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable).

## Le Catalogue des Skills IDE
L'infrastructure ne dépend plus d'agents Python isolés, mais de **compétences (Skills)** injectées dynamiquement dans l'IDE Agentique, lui conférant différentes postures cognitives selon la phase :
- **`plan`** (Strategic & Business Analysis Skill) : Modélisation DDD, élaboration d'options ToT, arbitrage MCTS et découpage du backlog en **stories verticales** via le protocole *Grill with Docs*. Maintient en temps réel `sprint_backlog.md` et consigne les décisions dans les ADRs.
- **`validate`** (Quality Assurance & INVEST Skill) : Invoque le linter mLoop en arrière-plan (`src/swarm.py wikifix`), évalue la couverture Gherkin et calcule le Score INVEST final pour sceller une Story (Definition of Ready).

## Ponts MCP (Model Context Protocol)
mLoop expose son état via des serveurs MCP natifs situés dans `src/bridges/`.
- `mcp_loop_mem.py` : Accès en lecture/écriture à l'état de LoopState, recherche FTS5 SQLite, linter Gherkin temps réel (`check_story_compliance`), et préchargement RAM asynchrone (`loop_mem_preload_context`).
- `mcp_graphify.py` : Passerelle MCP native vers le graphe de connaissances Graphify NetworkX (`graph_query`, `graph_path`, `graph_explain`).
- `mcp_proxy_router.py` : Routeur intelligent d'aiguillage vers les pipelines Python mLoop.
- `mcp_crawler.py` : Utilitaires d'ingestion sémantique web.
- `context7` : Recherche enrichie sur la documentation technique externe et les bibliothèques.
*L'IDE doit privilégier l'utilisation de ces ponts MCP pour interroger la mémoire du projet sans briser l'encapsulation.*

## Coding Guidelines & Architecture Rules
- **tripartite Asymmetric Architecture**: Keep local mechanics (crawler, graph parsing, system commands) under `src/agents/system1/`. Keep cognitive logic (ToT, MCTS, backlog generation) under `src/agents/system2/`.
- **Pure State Transitions**: All agents must inherit from `src/agents/base.py:BaseAgent` and strictly implement:
  `def execute(self, state: LoopState) -> LoopState`
  State must be typed and validated using **Pydantic v2** (`src/state.py`).
- **Unified Workspace Compliance**: Every managed project lives inside `Projects/<project-name>/` and must strictly match the unified directory structure (directives, journal, reference, memory, backlog, src).
