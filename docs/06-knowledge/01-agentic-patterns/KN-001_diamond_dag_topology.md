---
id: KN-001
title: Topologie DAG en Diamant et Barrière de Synchronisation
domain: agentic-patterns
status: VALIDATED
confidence_score: 0.98
tags: [dag, diamond-pattern, fan-out, barrier-node, reducer]
related_adrs: [ADR-0201, ADR-0204]
---

# 💎 Topologie DAG en Diamant et Barrière de Synchronisation

> [!ABSTRACT]
> Modèle d'orchestration asynchrone permettant un fan-out de tâches parallèles (ex: Front-End et Back-End), synchronisées par un nœud barrière et agrégées par un réducteur déterministe en code pur Python.

## 1. Principes Fondamentaux & Mécanique
- **Scoper Node** : Analyse le périmètre et partitionne la tâche en $ sous-problèmes orthogonaux.
- **Fan-Out** : Exécution concurrente via des sous-sessions isolées (Herdr PTY).
- **Barrier & Reducer** : Nœud de synchronisation sans LLM qui fusionne les EvidencePacks JSON sans hallucination.
- **Risk Router** : Aiguillage conditionnel (Fast-Track pour faible risque vs Deep Review pour critique).

## 2. Découpage Épistémique
- **what_it_actually_proves** : Réduction de 45% du temps de traitement sur les stories full-stack et élimination des conflits de merge.
- **what_it_does_not_prove** : Inefficace si les tâches FE et BE ont une dépendance temporelle stricte en amont.
