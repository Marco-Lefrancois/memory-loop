# Architecture Conceptuelle : Positionnement de Memory Loop (mLoop v2.0.0)

Le diagramme ci-dessous illustre comment **Memory Loop (mLoop v2.0.0)** se positionne comme le cœur névralgique de la **Couche 1 (L'ÊTRE)**, incarnant les 5 piliers et la conception poussée des agents.

```mermaid
graph TD
    classDef mloop fill:#2563eb,stroke:#1d4ed8,stroke-width:3px,color:#fff,font-weight:bold
    classDef layer fill:#f8fafc,stroke:#94a3b8,stroke-width:2px,color:#0f172a,stroke-dasharray: 5 5
    classDef pillar fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef subprop fill:#f59e0b,stroke:#b45309,stroke-width:1px,color:#fff
    classDef infra fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff

    subgraph DevCycle ["🔄 Agent Development Cycle & Calibrate Engine"]
        direction LR
        HarnessDev[Harness] --> Evals --> Calibrate[Calibrate Engine 8/8] --> BetterAgent[Better Agent]
    end

    subgraph L1 ["🎯 LAYER 1 : CONTEXT (L'Ontologie mLoop v2.0.0)"]
        direction TB
        MLOOP{"⚙️ MEMORY LOOP (mLoop v2.0.0)"}:::mloop
        
        subgraph Pillars ["Les 5 Piliers Fondamentaux de mLoop"]
            direction LR
            Mem("🧠 Memory (L3 RAM & AST)"):::pillar
            Sk("🛠️ Skills (AP 1.0)"):::pillar
            So("👻 Soul (Directives)"):::pillar
            SR("🔄 Session Recall (Focus)"):::pillar
            Val("🛡️ Validation (EvidencePacks)"):::pillar
        end
        
        subgraph Concept ["Agents Conception & Standard AP 1.0"]
            direction TB
            subgraph SAC ["Plugin Export (ADR-0309)"]
                direction LR
                C_Do(".agents/plugin.json"):::subprop --> C_Obs(".agents/mcp.json"):::subprop --> C_Cur(".agents/skills/"):::subprop --> C_Imp("plugin-export"):::subprop
            end
            subgraph SoulDef ["Soul Definition"]
                direction LR
                S_Style("Zero-Fluff"):::subprop --- S_Ton("Senior Tech Lead"):::subprop --- S_Regles("AGENTS.md"):::subprop
            end
        end

        MLOOP --> Pillars
        Sk -.-> SAC
        So -.-> SoulDef
    end

    subgraph L2 ["⚡ LAYER 2 : HARNESS (Moteur Graph Engineering DAG)"]
        direction LR
        IDE("IDE Agentique (Cursor/Antigravity)"):::infra --- Kernel("Kernel Python (swarm.py / graph-run)"):::infra
    end

    subgraph L3 ["🧠 LAYER 3 : MODEL (Routage Hybride Sovereign)"]
        direction LR
        Gemini("Gemini (3 Flash / 3.1 Pro)"):::infra --- LocalModels("DeepSeek R1 / Llama"):::infra
    end

    %% Relations Globales
    L3 ==>|Fournit la puissance cognitive| L2
    L2 ==>|Orchestre la validation & EvidencePacks| L1
    BetterAgent -.->|S'incarne dans| MLOOP
```

### Analyse du positionnement de mLoop (v2.0.0) :

1. **Les 3 Couches (Layers)** : mLoop habite le **Layer 1 (Context)**. Il utilise le Layer 2 pour exécuter ses topologies DAG (`graph-run`) et valider l'intégrité déterministe via le Kernel (`src/swarm.py`).
2. **Les 5 Piliers v2.0.0** : Memory (L3 RAM Cache), Skills Portables (AP 1.0), Soul (Zero-Fluff), Session Recall (Focus lock), Validation (EvidencePacks & 4 Piliers Gherkin).
3. **Layer 3 (Modèles Stratifiés & Confidence Gate)** : Routage souverain. Les modèles de raisonnement Cloud/Local pilotent la stratégie, tandis que le Confidence Gate et le Reducer Node Python assurent la gouvernance physique.
