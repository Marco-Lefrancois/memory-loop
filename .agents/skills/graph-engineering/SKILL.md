---
name: graph-engineering
description: "Orchestration du graphe DAG Multi-Agents, sous-graphes NetworkX et EvidencePacks. Use when navigating semantic knowledge graphs, managing DAG execution topology, or querying architectural entity relationships."
disable-model-invocation: false
---

# 🕸️ Skill Graph Engineering (DAG Multi-Agents)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Ce skill active l'orchestration avancée en graphe d'agents spécialisés (Directed Acyclic Graph - DAG) pour mLoop. Il permet de passer du paradigme "Prompt Unique" au paradigme "Système Distribué d'Agents et de Nœuds de Code Déterministe".

## 🗺️ Principes d'Exécution en 5 Étapes

1. **Scope** : Définition formelle du périmètre sous `Projects/<nom_projet>/backlog/`.
2. **Fan-Out** : Découpage dynamique et parallélisation des sous-tâches par sous-système ou fichier.
3. **Barrier Node** : Synchronisation et barrière de validation avant réduction.
4. **Reducer Node** : Nœud de code déterministe Python fusionnant et dédupliquant les preuves sans coût LLM.
5. **Synthesize / Evaluator Node** : Revue critique indépendante basée sur le risque (*Fast Track* vs *Deep Review*).

## 🏛️ Structure des Preuves & Ancrage
Toutes les arêtes du graphe véhiculent des preuves typées sous `Projects/<nom_projet>/memory/evidence/` (`target_file`, `line_range`, `rule_ref`, `confidence`, `risk_level`) ancrées sur `standards/adr-system/`.

## 🛡️ Résilience & Dégradation Gracieuse
En cas d'échec d'un nœud agentique dans le DAG, isoler le sous-graphe en erreur, journaliser la défaillance dans `memory/logs/` et poursuivre l'exécution des branches indépendantes sans bloquer l'ensemble du graphe.

## 🚀 Commande CLI & OpenCode Shortcut

```powershell
# Exécution CLI
python src/swarm.py graph-run --project <nom_projet>

# Raccourci OpenCode
/loop-graph-run <nom_projet>
```
