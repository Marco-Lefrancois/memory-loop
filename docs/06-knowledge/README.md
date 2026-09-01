# 📚 Bibliothèque du Savoir (Knowledge Vault) — Memory Loop

Ce répertoire constitue la **Bibliothèque du Savoir Curé et Distillé** de Memory Loop.
Il stocke des fiches de connaissances atomiques, normalisées au format **Open Knowledge Format (OKF v0.1)**, permettant une réutilisation immédiate par les agents IA sans bruit sémantique.

---

## 🗂️ Domaines du Savoir

```mermaid
graph TD
    classDef domain fill:#dbeafe,stroke:#2563eb,color:#1e3a8a;
    
    Vault["Knowledge Vault (docs/06-knowledge/)"]
    Vault --> D1["01-agentic-patterns/ (Topologies DAG, Herdr, Swarm)"]:::domain
    Vault --> D2["02-memory-epistemic/ (LLM-Wiki, Grounding, AOEP)"]:::domain
    Vault --> D3["03-graph-engineering/ (Dual-Engine Graphify/CodeGraph)"]:::domain
    Vault --> D4["04-model-governance/ (LiteLLM, Pricing, Anti-Sycophancy)"]:::domain
    Vault --> D5["05-software-spec/ (4 Piliers Gherkin, INVEST, No-Code)"]:::domain
```

### 1. [01-agentic-patterns/](01-agentic-patterns/)
- `KN-001` : [Topologie DAG en Diamant et Barrière de Synchronisation](01-agentic-patterns/KN-001_diamond_dag_topology.md)
- `KN-002` : [Multiplexage PTY et Isolation de Contexte Herdr](01-agentic-patterns/KN-002_herdr_pty_multiplexing.md)

### 2. [02-memory-epistemic/](02-memory-epistemic/)
- `KN-010` : [Paradigme LLM-Wiki v2 et Format OKF](02-memory-epistemic/KN-010_llm_wiki_v2_okf_standard.md)
- `KN-011` : [Grounding Épistémique et Découplage des Preuves (DeepPaperNote)](02-memory-epistemic/KN-011_epistemic_grounding_deeppapernote.md)

### 3. [03-graph-engineering/](03-graph-engineering/)
- `KN-020` : [Double Moteur de Graphes Sémantique & AST (Graphify + CodeGraph)](03-graph-engineering/KN-020_dual_engine_graph_codegraph_graphify.md)

### 4. [04-model-governance/](04-model-governance/)
- `KN-030` : [Routage Multi-Modèles LiteLLM, Forensics & Gestion Budgétaire](04-model-governance/KN-030_litellm_model_routing_pricing.md)

### 5. [05-software-spec/](05-software-spec/)
- `KN-040` : [Standard BDD Gherkin 4 Piliers, INVEST et Pureté Déclarative](05-software-spec/KN-040_gherkin_4_pillars_invest.md)
