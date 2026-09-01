# Évolution Architecturale de Memory Loop (mLoop)

Ce document retrace l'évolution de l'architecture du projet Memory Loop, depuis son approche initiale par scripts locaux jusqu'à son architecture cognitive et déterministe actuelle (IDE-Driven, Graph Engineering DAG & Agent Plugins 1.0).

## 1. L'Approche Scriptée Initiale (v1.x)
À cette époque, tout passait par des scripts Python procéduraux. L'orchestrateur devait tout gérer et les agents fonctionnaient en silos, souvent avec des risques de perte de contexte ou de modifications de code imprévisibles (YOLO).

```mermaid
flowchart TD
    User(["Humain"]) --> Kernel["Orchestrateur Python (loop.py)"]
    
    Kernel --> Scrum["Agent Scrum (scrum.py)"]
    Kernel --> CodeAgent["Agents d'exécution locaux"]
    
    Scrum --> Backlog[/"Gestion manuelle du Backlog"/]
    CodeAgent --> Code[/"Fichiers source (Modifications directes)"/]
    
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef agent fill:#ffe0b2,stroke:#ff9800,stroke-width:2px;
    Scrum:::agent
    CodeAgent:::agent
```

## 2. Le Pivot "IDE-Driven Framework" (v2.0.0)
La grande scission : l'éditeur de code (l'IDE) devient le "Cerveau" intelligent qui pilote le projet grâce aux *Skills Markdown Portables*, tandis que le code Python de mLoop devient un moteur de validation et d'état déterministe (le "Muscle").

```mermaid
flowchart TD
    subgraph Couche1 ["Couche 1 : L'IDE (Le Cerveau)"]
        IDE["IDE Agentique (ex: Antigravity)"] --> Skills["Compétences Portables AP 1.0"]
        Skills --> S_Plan["Skill : Plan (Grill-with-Docs)"]
        Skills --> S_Analyze["Skill : Analyze (Graphify)"]
        Skills --> S_Validate["Skill : Validate (INVEST & Evidence)"]
    end

    subgraph Couche2 ["Couche 2 : mLoop Kernel (Le Moteur)"]
        Backend["Python Kernel (swarm.py)"] --> QA["Pipeline d'Audit (WikiFix & Calibrate)"]
        QA --> Status["EvidencePack & State Health"]
    end

    Couche1 -. "Délègue la validation finale à" .-> Couche2
    
    classDef brain fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;
    classDef muscle fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    Couche1:::brain
    Couche2:::muscle
```

## 3. L'Écosystème Spec-Driven en 5 Phases & Graphify L3
Le système mature tel qu'il est aujourd'hui : intégration de la mémoire à long terme (Graphify L3 In-Memory & AST via MCP `mcp_loop_mem.py`), exécution 100% locale, et la barrière stricte des contrats (PRD/SCC) avec l'humain dans la boucle (Grill with Docs). L'agent ne touche pas au code source de l'application cliente.

```mermaid
flowchart TD
    subgraph Memoire ["Mémoire & Contexte"]
        MCP["Serveurs MCP (mcp_loop_mem)"]
        Graphify[("Graphe Sémantique & AST (L3 RAM Cache)")]
        MCP <-->|Search-First| Graphify
    end

    subgraph Cycle ["Le Cycle en 5 Phases"]
        direction LR
        Spec("1. SPEC") --> Plan("2. PLAN")
        Plan --> Build("3. BUILD")
        Build --> Validate("4. VALIDATE")
        Validate --> Ship("5. SHIP")
    end

    Plan --> PRD{"PRD / SCC\n(4 Piliers Gherkin)"}
    HITL(["Grill with Docs\n(Humain dans la boucle)"]) -. "Approuve" .-> PRD
    PRD -. "Audité par EvidencePack" .-> Validate

    IDE["IDE Agentique\n(Cursor, VS Code, Antigravity)"] <-->|MCP| MCP
    IDE --> Cycle
    
    classDef mem fill:#fff3e0,stroke:#ffb300,stroke-width:2px;
    classDef contract fill:#fce4ec,stroke:#e91e63,stroke-width:2px;
    Memoire:::mem
```

## 4. L'Écosystème Persistant, Graph DAG & Agent Plugins 1.0 (ADR-0309)
L'intégration du décodage spéculatif, du **Graph Engineering DAG Multi-Agents (Pattern Diamant)**, du standard **Agent Plugins 1.0** et du moteur **Calibrate Engine** complète l'architecture :

- **Graph Engineering DAG** : Topologie multi-agents (Scoper -> Fan-Out -> Reducer -> Risk Router -> Evaluator Node -> Final Judgment) avec State Checkpointing idempotent (`.mloop_tmp/checkpoints/`).
- **Standard Agent Plugins 1.0 (ADR-0309)** : Empaquetage portable du framework (`.agents/plugin.json`, `.agents/mcp.json`, 21+ skills) exportable vers multi-IDE (`python src/swarm.py plugin-export`).
- **Confidence Gate & RAM Cache** : Filtrage syntaxique ultraléger (< 10 ms) et préchargement d'engrammes en RAM pour requêtes sémantiques à 0ms de latence disque.
- **EvidencePackEngine & Suite AOEP-v0** : Audit d'état persistant (`memory/evidence/`), traçabilité par Tombstones et auto-étalonnage continu (`calibrate` 8/8 PASS).

```mermaid
flowchart TD
    Draft["Brouillon de Spécification"] --> Gate{"Confidence Gate\n(Syntactic Filter)"}
    Gate -. "REJECT (<70)" .-> Fix["Auto-Correction Locale"]
    Gate -. "PASS (>=70)" .-> DAG["Topologie Graph Engineering DAG"]
    
    subgraph RAM ["Mémoire RAM"]
        Cache["_PRELOAD_CACHE\n(Engrammes 1-Hop)"]
    end
    
    DAG <-->|Zero-Latency Read| Cache
    
    subgraph Governance ["Gouvernance & Sécurité"]
        AOEP["Suite AOEP-v0 & EvidencePacks"]
        Calibrate["Moteur Calibrate & RHO"]
    end
    
    Governance -. "Contrôle & Auto-Repair" .-> DAG
```"]
    end
    
    Governance -. "Contrôle en continu" .-> DeepReasoning
```

