# Architecture Graph Engineering (DAG Multi-Agents Natif mLoop)

Ce document décrit l'intégration du **Graph Engineering** au cœur du backend d'état et d'architecture mLoop.

---

## 🏛️ Vue d'Ensemble

Le moteur d'orchestration mLoop remplace les interactions linéaires verbeuses par une topologie de **Graphe Orienté Acyclique (DAG)** basée sur le **Pattern Diamant** :

```
       ┌──────────┐
       │  SCOPER  │ (Nœud LLM : Cadrage du périmètre & tâches)
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
       │  FINAL JUDGMENT  │ (Sauvegarde log JSON sous backlog/graph_execution_log.json)
       └──────────────────┘
```

---

## 📚 Références & Documents Associés

Toutes les spécifications détaillées, le plan d'implémentation et le walkthrough de validation sont conservés de manière permanente sous `docs/01-architecture/framework/graph_engineering/` :

1. 📄 **[Plan d'Implémentation](file:///c:/Memory%20Loop/docs/01-architecture/framework/graph_engineering/01-graph_engineering_implementation_plan.md)** : Modèle théorique, découpage des composants et choix d'isolation par sous-dossiers isolés.
2. 📄 **[Walkthrough & Rapport de Validation](file:///c:/Memory%20Loop/docs/01-architecture/framework/graph_engineering/02-graph_engineering_walkthrough.md)** : Trace des tests et validation par la suite de guardrails `python src/swarm.py audit-loop`.
3. 📄 **[Registre des Tâches](file:///c:/Memory%20Loop/docs/01-architecture/framework/graph_engineering/03-graph_engineering_tasks.md)** : Grille des phases de réalisation (Phases 1 à 5).

---

## 🛠️ Utilisation CLI

```powershell
# Exécution de la topologie Graph Engineering sur un projet
python src/swarm.py graph-run --project <nom_du_projet>

# Conversion automatique d'une carte Wayfinder en graphe DAG
python src/swarm.py wayfinder --initiative <nom_initiative>
python src/swarm.py graph-run --project <nom_du_projet> --title <nom_initiative>
```
