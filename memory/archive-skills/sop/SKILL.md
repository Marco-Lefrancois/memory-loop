---
name: sop
description: "SOP: Référence standard des opérations mLoop (Lecture par l'humain)."
disable-model-invocation: true
---

# 📖 sop (The Bible)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Ce skill est la Source Unique de Vérité (SSOT) pour le fonctionnement du moteur autonome. Il définit les protocoles de communication, d'analyse et de validation fonctionnelle.

## 🏗️ Architecture (Kernel-Pipeline)
1. **Kernel (`src/swarm.py`)** : Orchestrateur agnostique piloté par les Workflows (Pipelines).
2. **IDE & Skills (`.agents/skills/`)** : Le "Cerveau". Postures cognitives de l'agent.
3. **MCP Bridges (`src/bridges/`)** : Ponts natifs (Mémoire, Crawler) isolant l'état du système.
4. **Hooks (`.agents/hooks/`)** : Sentinelles (Pre-flight/Post-flight).

## 🔄 Cycle A-P-QA
- **[A] Analyze** : Ingestion via Graphify et moissonnage (Pont MCP Crawler).
- **[P] Plan** : Grilling DDD, création de SCC et rédaction d'ADR (MADR format).
- **[QA] Functional Audit** : Audit de conformité (WikiFix), validation du score INVEST et déclenchement de l'auto-amélioration (RHO).

## 🛡️ La Frontière Ultime : SCC & Story Guard
Toute story doit être "cristallisée" (SCC) avec :
- Une **Triade de scénarios** (Anonyme / Membre / Guest).
- Une gestion des erreurs standard (4xx / 5xx).
- **Zero-Drift Execution** : L'IDE doit invoquer `python src/bridges/story_guard.py --check_file` avant de modifier un fichier.

## 🧬 Auto-Amélioration & Synchronisation (RHO)
- **Chaos Testing (RHO)** : Toute erreur récurrente doit être transformée en règle de garde-fou dynamique via `python src/swarm.py optimize`.
- **Ground Truth Sync** : Après toute édition physique, l'agent a l'obligation formelle de déclencher `python src/swarm.py sync` pour mettre à jour la mémoire Graphify.

## 📚 Références Locales
- `references/aspec_core_standard.md` : Principes de l'Agentic Coworker.
