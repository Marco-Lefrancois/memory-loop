# Intégration Native du Graph Engineering dans le Framework mLoop

Ce document constitue la référence d'architecture et le plan d'implémentation pour le moteur de **Graph Engineering Natif (Multi-Agent DAG)** de mLoop, basé sur les meilleures pratiques (Pattern Diamant, Evidence Packs structurés, Reducers déterministes et Risk-Based Routing).

---

## Vue d'Ensemble de l'Architecture Graph Engineering pour mLoop

```
                            ┌────────────────────────┐
                            │    1. SCOPER NODE      │
                            │  (Wayfinder Engine /   │
                            │  Gemini 3.6 Pro Task)  │
                            └───────────┬────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
  ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
  │ 2a. FAN-OUT NODE 1 │     │ 2b. FAN-OUT NODE 2 │ ... │ 2n. FAN-OUT NODE N │
  │  (Spec/Story Task) │     │  (Spec/Story Task) │     │  (Spec/Story Task) │
  └──────────┬─────────┘     └──────────┬─────────┘     └──────────┬─────────┘
             │                          │                          │
             └──────────────────────────┼─────────────────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │   3. BARRIER NODE      │
                            │ (Wait for all sub-tasks)│
                            └───────────┬────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │ 4. REDUCE & DUP NODE   │
                            │  (Pure Python Code:    │
                            │  Merge, Deduplicate &  │
                            │  Build EvidencePack)   │
                            └───────────┬────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │ 5. RISK ROUTER NODE    │
                            │  (Categorize Evidence) │
                            └─────┬──────────────┬───┘
                                  │              │
        ┌─────────────────────────┘              └────────────────────────┐
        ▼ (Low / Medium Risk)                                             ▼ (High / Critical Risk)
┌──────────────────────┐                                 ┌─────────────────────────────────┐
│ 6a. FAST-TRACK QA    │                                 │ 6b. DEEP CRITIC PANEL           │
│ (WikiFix + Gherkin)  │                                 │ (EvaluatorNode + Multi-Agent    │
│                      │                                 │  Review + INVEST + ADR Audit)   │
└──────────┬───────────┘                                 └────────────────┬────────────────┘
           │                                                              │
           └────────────────────────────┬─────────────────────────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │  7. CONVERGENCE LOOP   │
                            │   (Self-Healing Max 3) │
                            └───────────┬────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │ 8. FINAL JUDGMENT &    │
                            │      SYNC NODE         │
                            │  (SQLite Sync & Status)│
                            └────────────────────────┘
```

---

## Directives d'Architecture & Arbitrages Validés

- **Fichiers source impactés** : `src/pipelines/evidence.py`, `src/pipelines/graph_router.py`, `src/pipelines/evaluator_node.py`, `src/pipelines/wayfinder.py`, `src/swarm.py`.
- **Journal d'Observabilité** : Sauvegarde systématique dans `backlog/graph_execution_log.json`.
- **Isolation des Nœuds Parallèles** : Utilisation de sous-dossiers isolés `.mloop_tmp/fanout/node_<id>/` avec fusion déterministe par le `ReducerNode` Python (option `--use-worktree` configurable).

---

## Structure des Composants

### 1. Evidence Module (`src/pipelines/evidence.py`)
- `EvidenceItem` : Contrat atomique typé pour le transport des preuves (`target_file`, `line_range`, `rule_ref`, `confidence`, `risk_level`).
- `EvidencePack` : Collection de preuves sur chaque arête du DAG ("An Edge Should Carry Evidence").
- `EvidenceReducer` : Code node déterministe pour la fusion et déduplication des EvidencePacks sans coût d'API.

### 2. Moteur GraphRouter (`src/pipelines/graph_router.py`)
- Typage des nœuds : `NodeCategory.LLM_AGENT`, `NodeCategory.DETERMINISTIC_CODE`, `NodeCategory.HYBRID`.
- Routage par le risque : `RiskLevel.LOW`, `RiskLevel.MEDIUM`, `RiskLevel.HIGH`, `RiskLevel.CRITICAL`.
- Pattern Diamant et génération synchrone/asynchrone de la trace d'exécution JSON.

### 3. Evaluator Node (`src/pipelines/evaluator_node.py`)
- Routage par le risque (*Fast-Track* pour faible risque vs *Deep Review* pour `RM-XXX` et ADR).
- Production d'un `EvidencePack` d'évaluation structuré.

### 4. Conversion Wayfinder & CLI (`src/pipelines/wayfinder.py` & `src/swarm.py`)
- `WayfinderEngine.to_dag()` : Conversion des cartes Wayfinder en graphes exécutables.
- Commande CLI : `python src/swarm.py graph-run --project <projet>`.
