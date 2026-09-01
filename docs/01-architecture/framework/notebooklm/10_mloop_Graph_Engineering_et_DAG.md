# mLoop - 10. Graph Engineering & Topologie DAG Multi-Agents

## 1. Vue d'Ensemble du Moteur DAG
mLoop remplace les chaînes d'agents linéaires verbeuses par un moteur d'orchestration basé sur un **Graphe Orienté Acyclique (DAG)** et le **Pattern Diamant**. Cette architecture garantit une exécution parallèle contrôlée, la synchronisation déterministe des tâches et l'audit rigoureux du risque.

```
       ┌──────────┐
       │  SCOPER  │ (Nœud LLM : Cadrage du périmètre & découpage)
       └────┬─────┘
            │
      ┌─────┴───────────────┐ (FAN-OUT : Tâches parallèles)
      ▼                     ▼
┌───────────┐         ┌───────────┐
│ Nœud BE   │         │ Nœud FE   │
└─────┬─────┘         └─────┬─────┘
      └──────┐       ┌──────┘
             ▼       ▼
       ┌──────────────────┐
       │   BARRIER NODE   │ (Synchronisation)
       └─────────┬────────┘
                 ▼
       ┌──────────────────┐
       │   REDUCER NODE   │ (Pure Code Python : Merge & Deduplicate EvidencePacks)
       └─────────┬────────┘
                 ▼
       ┌──────────────────┐
       │ RISK ROUTER NODE │
       └────┬────────┬────┘
 (Low Risk) │        │ (High/Critical Risk)
            ▼        ▼
     ┌───────────┐ ┌──────────────┐
     │Fast Track │ │ Deep Review  │ (EvaluatorNode + Gherkin + INVEST + ADR Audit)
     └─────┬─────┘ └──────┬───────┘
           └──────┬───────┘
                  ▼
       ┌──────────────────┐
       │  FINAL JUDGMENT  │ (Sauvegarde du journal d'exécution JSON)
       └──────────────────┘
```

## 2. Nœuds Clés de la Topologie
1. **Scoper Node (`node_spec`)** : Analyse le besoin initial et découpe la requête en tâches parallèles (Fan-Out).
2. **Parallel Task Nodes (`node_plan_be`, `node_plan_fe`)** : Exécutent l'analyse spécialisée sur chaque sous-domaine de manière isolée.
3. **Barrier & Reducer Node (`node_reducer`)** : Nœud déterministe en Pure Code Python (0ms de latence LLM). Il fusionne, déduplique et valide la structure des artefacts `EvidencePack` produits par les nœuds amont.
4. **Risk Router Node** : Évalue le niveau de risque de la modification (impact architectural, sécurité, dépendances).
   * **Fast Track** : Si le risque est Faible (Low), validation directe et passage à la finalisation.
   * **Deep Review (Evaluator Node)** : Si le risque est Élevé/Critique (High/Critical), déclenchement d'un audit approfondi (4 Piliers Gherkin, INVEST, audit ADR).
5. **Final Judgment Node** : Consigne le verdict et le journal d'exécution complet dans `backlog/graph_execution_log.json`.

## 3. State Checkpointing & Reprise Idempotente
* **Checkpoints** : À chaque transition de nœud, l'état du DAG est sauvegardé sous `.mloop_tmp/checkpoints/<initiative>.json`.
* **Reprise en cas de panne** : En cas de coupure ou d'erreur, la commande `python src/swarm.py graph-run --project <p> --resume` reprend l'exécution exactement au nœud interrompu sans relancer les étapes déjà validées.

## 4. Les 8 Piliers d'Optimalité en Python Engineering
Le moteur Python de mLoop respecte 8 principes d'ingénierie stricte :
1. **Generators & Lazy Evaluation** : Traitement streaming dans `wikifix.py` et `calibrate.py` (< 30 Mo RAM).
2. **Context Managers (`with`)** : Isolation et fermeture garantie des fichiers et bases SQLite.
3. **Resilience Network (`@robust_api_call`)** : Backoff exponentiel avec jitter contre le Rate Limiting (429).
4. **Token Budget Guard** : Calcul rapide et tronquage prioritaire des contextes sous le plafond (8000 jetons).
5. **State Checkpointing** : Persistance réactive de l'état du workflow.
6. **Pure Code Reducer** : Fusion sans surcoût LLM des packs d'évidence.
7. **Dataclasses & Pydantic** : Typage fort pour `EvidencePack`, `EvidenceItem`, `EvaluationResult`.
8. **Declarative Composition (`__or__`)** : Surcharge de l'opérateur pipe (`|`) pour enchaîner les étapes de pipeline.
