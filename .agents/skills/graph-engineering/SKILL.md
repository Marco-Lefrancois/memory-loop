---
name: graph-engineering
description: "Graph Engineering: Orchestration du graphe DAG Multi-Agents (Pattern Diamant, EvidencePacks, Risk Routing)."
disable-model-invocation: false
---

# 🕸️ Skill Graph Engineering (DAG Multi-Agents)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Ce skill active l'orchestration avancée en graphe d'agents spécialisés (Directed Acyclic Graph - DAG) pour mLoop. Il permet de passer du paradigme "Prompt Unique" au paradigme "Système Distribué d'Agents et de Nœuds de Code Déterministe".

## 🗺️ Principes d'Exécution

1. **Pattern Diamant (`Scope` ➔ `Fan-Out` ➔ `Barrier` ➔ `Reduce` ➔ `Synthesize`)** :
   - **Scope** : Définition du périmètre de l'initiative.
   - **Fan-Out** : Découpage dynamique et parallélisation des sous-tâches par sous-système/fichier.
   - **Barrier Node** : Synchronisation avant réduction.
   - **Reducer Node** : Nœud de code déterministe Python fusionnant et dédupliquant les preuves sans coût LLM.
   - **Synthesize / Evaluator Node** : Revue critique indépendante basée sur le risque (*Fast Track* vs *Deep Review*).

2. **Structure des Preuves (`EvidencePacks`)** :
   Toutes les arêtes du graphe véhiculent des preuves typées (`target_file`, `line_range`, `rule_ref`, `confidence`, `risk_level`) et non du bavardage textuel.

## 🚀 Commande CLI & OpenCode Shortcut

```powershell
# Exécution CLI
python src/swarm.py graph-run --project <nom_projet>

# Raccourci OpenCode
/loop-graph-run <nom_projet>
```
