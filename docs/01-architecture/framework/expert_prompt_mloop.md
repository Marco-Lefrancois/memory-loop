# 🧠 PROMPT EXPERT : Génération du Memory Loop Autonomous Engine (mLoop v2.0.0)

**Contexte pour l'Agent ou le LLM qui recevra ce prompt :**
Vous agissez en tant qu'Architecte Logiciel Senior et Spécialiste en IA Agentique. Votre mission est de créer ou de mettre à jour l'architecture complète du **Memory Loop Autonomous Engine (mLoop v2.0.0)** au standard **Agent Plugins 1.0 (ADR-0309)**.

---

## 🎯 INSTRUCTIONS DE SYSTÈME ET D'ARCHITECTURE

### 1. Le Paradigme : Kernel-Pipeline & Agent Plugins 1.0 (AP 1.0)
*   **Kernel (`src/swarm.py`)** : Orchestrateur agnostique centralisant les commandes CLI (`resume`, `sync`, `wikifix`, `calibrate`, `graph-run`, `aoep`, `plugin-validate`, `plugin-export`, `jira_sync`).
*   **Agent Plugins 1.0 (ADR-0309)** : Empaquetage standardisé (`.agents/plugin.json`, `.agents/mcp.json`, dossiers `.agents/skills/`).
*   **Topologie Graph Engineering DAG** : Execution DAG Multi-Agents (Pattern Diamant, Scoper, Reducer Node pure Python, Risk Router, Evaluator Node).

### 2. L'Ontologie des 5 Piliers v2.0.0
Initialiser la structure mentale (`.agents/`) :
*   **Memory** : Graphe Cognitif (Graphify L3 In-Memory & AST).
*   **Skills** : 21+ compétences portables documentées avec `SKILL.md` (Divulgation Progressive).
*   **Soul (`soul.json`)** : Ton Zero-Fluff, posture Senior Tech Lead.
*   **Session Recall** : Checkpoints `.mloop_tmp/checkpoints/` et `python src/swarm.py focus`.
*   **Validation** : Audit Gherkin 4 Piliers, suite `aoep`, INVEST Score et `EvidencePackEngine`.

### 3. Le Cycle Spec-Driven en 5 Phases & Matrice d'Outillage
1.  **Phase 1 SPEC** : Ingestion documentaire sous `reference/` vers `docs/00-ingested/` via `ingest`.
2.  **Phase 2 PLAN** : Architecture verticaux, *Grill with Docs*, `CONTEXT.md` et stories dans `backlog/stories/`.
3.  **Phase 3 BUILD** : Development (TDD pour mLoop `src/`, assisté pour client) sous verrou `story_guard.py`.
4.  **Phase 4 VALIDATE** : Audit Gherkin, calculation INVEST, `wikifix` et EvidencePack JSON synchrone (`memory/evidence/`).
5.  **Phase 5 SHIP** : Synchronisation Graphify (`sync`), gouvernance Jira Story-Only (`jira_sync`) et auto-étalonnage (`calibrate` 8/8 PASS).

---

## 🛠️ LIVRABLES ATTENDUS

1.  **Arborescence Standardisée** :
    ```text
    /
    ├── .agents/
    │   ├── plugin.json (AP 1.0)
    │   ├── mcp.json
    │   ├── soul.json
    │   ├── agents/
    │   └── skills/ (21+ skills)
    ├── reference/
    ├── docs/
    │   ├── 00-ingested/
    │   ├── 01-architecture/
    │   └── 04-transverse/
    ├── backlog/
    │   ├── sprint_backlog.md
    │   ├── STORY_MAPPING.md
    │   └── stories/
    ├── memory/
    │   ├── knowledge_graph.json
    │   └── evidence/
    ├── src/
    │   └── swarm.py (Kernel CLI)
    └── AGENTS.md
    ```
2.  **Séquence d'Amorçage Obligatoire (AGENTS.md)** :
    `resume` $\rightarrow$ `loop_mem_search` $\rightarrow$ `graphify query` $\rightarrow$ `vibe-check` $\rightarrow$ `focus`.
3.  **Zero-Ask Evidence Enforcement** : Generation synchrone obligatoire de l'EvidencePack sans interrompre l'utilisateur.
