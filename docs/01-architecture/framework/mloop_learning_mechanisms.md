# Les Mécanismes d'Apprentissage & Auto-Calibrage de mLoop (v2.0.0)

Ce document explicite comment le framework mLoop apprend, s'auto-étalonne et garantit le "zéro-drift" de ses agents.

L'apprentissage dans mLoop n'est pas basé sur la mémoire contextuelle classique d'un LLM, mais sur une structuration rigoureuse de la connaissance et de l'expérience, divisée en quatre dimensions : Proactive, Réactive, Prescriptive et d'Auto-Étalonnage.

## 1. Apprentissage Proactif : Cartographie & Graphify (Phase 1 SPEC)
Avant d'entamer la planification, mLoop "apprend" son environnement de travail :
- **Graphify (SSOT & AST)** : Le framework scanne le code source et la documentation pour construire le graphe sémantique persistant L3 In-Memory.
- **God Nodes & Dependances** : Il identifie les nœuds centraux et permet l'exploration sémantique ciblée via `graphify query`, `graphify explain` et `graphify path`.

## 2. Apprentissage Réactif : Apprendre par l'Erreur (RHO & EvidencePacks)
C'est le mécanisme de **Retrospective Harness Optimization (RHO)** :
- Lorsqu'une violation sémantique ou une erreur de conformité est détectée, la commande `python src/swarm.py optimize` est invoquée.
- L'erreur est instantanément "cristallisée" dans `rho_rules.yaml` (projet local ou global).
- Le Linter Sémantique (**WikiFix**) et l'**EvidencePackEngine** (`memory/evidence/`) lisent déterministement ces règles pour bloquer la récidive et consigner la preuve d'audit.

## 3. Apprentissage Prescriptif : Standardisation (Blueprints & AP 1.0)
- **Directives Métier et Technique (`business.md`, `tech.md`, `AGENTS.md`)** : Lexique strict (Ubiquitous Language) et Negative Prompting.
- **Agent Plugins 1.0 (ADR-0309)** : Empaquetage standardisé (`.agents/plugin.json`, `.agents/mcp.json`, 21+ skills) exportable vers multi-IDE (`plugin-export`).
- **ADR (Architecture Decision Records)** : Les décisions d'architecture validées sont gravées dans `docs/01-architecture/adrs/`.

## 4. Moteur d'Auto-Calibrage (`mLoop Calibrate Engine`)
Le moteur `Calibrate Engine` garantit un alignement continu sans dérive :
- **Commande CLI** : `python src/swarm.py calibrate --project <nom_projet>`.
- **Auto-Repair 8/8 PASS** : Teste et répare automatiquement les 8 composants (CLI, OpenCode shortcuts, ponts MCP, index des skills, directives, blueprints, SQLite/Graphify et registres SHA256).

## 5. Continuité et Session Recall : Le Handoff
Pour l'isolation contre la "Pourriture du contexte" (Context Rot), l'agent exécute le skill `handoff` à la fin d'une itération pour comporter son état réactif dans `memory/sessions/handoff.md`, réinitialisant la mémoire vive tout en préservant les points de contrôle.

---
**En conclusion** : 
mLoop **cartographie** le projet (Graphify), **restreint** ses erreurs (RHO), **étalonne** son écosystème (Calibrate 8/8), **standardise** ses succès (Plugins AP 1.0 & Blueprints) et **compresse** son contexte via le `handoff`.
