# ADR-0313 : Intégration des Innovations d'Architecture jcode (Mémoire Passive, Swarm Code-Shift & Self-Dev)

- **Statut** : Accepté
- **Date** : 2026-08-03
- **Auteurs** : Équipe mLoop Swarm & AI Assistant
- **Périmètre** : Framework Backend mLoop, Mémoire MCP `mcp_loop_mem.py`, Orchestration DAG Multi-Agents, CLI `self-dev`

---

## 1. Contexte

Le harness **jcode** (`https://github.com/1jehuang/jcode`), écrit en Rust, introduit des avancées significatives en termes de performance, de sobriété mémoire et d'intelligence agentique :
1. **Mémoire Passive par Cosine Similarity (Auto-Recall)** : Injection sémantique automatique d'engrammes liés sans forcer le LLM à appeler des outils de mémoire explicites.
2. **Detection de Collision Swarm (Code-Shift)** : Notification instantanée d'un agent si un autre agent modifie du code qu'il est en train de consulter dans le même repository.
3. **Moteur de Rendu Mermaid ultra-rapide** : Pré-calcul et minification des diagrammes visuels.
4. **Harness Self-Dev** : Boucle fermée permettant à l'agent de refactoriser sa propre codebase, exécuter ses tests, vérifier son alignement et recharger son binaire.

La présente décision d'architecture intègre ces 4 piliers au cœur de mLoop.

---

## 2. Décisions d'Architecture

### 2.1 Axe 1 : Mémoire Sémantique Passive & Auto-Recall par Dérive Contextuelle
- **Mécanisme** : Lors de l'appel à `loop_mem_preload_context` ou `loop_mem_search` dans `src/bridges/mcp_loop_mem.py`, mLoop pré-calcule les 5 engrammes sémantiques les plus proches de la Story courante.
- **Résultat** : Injection passive dans le prompt système agentique pour éviter les oublis ou les requêtes FTS5 explicites répétitives.

### 2.2 Axe 2 : Bus Anti-Collision & Code-Shift Detection dans le Swarm
- **Mécanisme** : Dans `src/pipelines/graph_runner.py`, création de l'événement `file_shift_event`.
- **Résultat** : Lorsque deux nœuds parallèles d'un DAG modifient le même artefact ou la même règle `RM-XXX`, l'Évaluateur (`EvaluatorNode`) reçoit une alerte synchrone pour éviter les hallucinations et conflits de fusion.

### 2.3 Axe 3 : Moteur de Rendu & Visual Gates Mermaid Minifiées
- **Mécanisme** : Utilisation du pipeline d'optimisation vectoriel `svg-optimize` et pré-rendu minifié des diagrammes Mermaid (Wayfinder, Gherkin Visual Gates) pour le Dashboard Web mLoop.

### 2.4 Axe 4 : Pipeline d'Auto-Développement mLoop (`python src/swarm.py self-dev`)
- **Mécanisme** : Création du pipeline `src/pipelines/self_dev_pipeline.py` et de la sous-commande CLI `python src/swarm.py self-dev --project mLoop`.
- **Fonctionnement** : mLoop exécute un cycle d'auto-audit (analyse d'anomalies, refactoring sous exception de développement mLoop, contrôle par `wikifix`, et validation par `calibrate`).

---

## 3. Conséquences

### Positives :
- **Diminution du coût en jetons** et suppression des requêtes de mémoire redondantes grâce à l'Auto-Recall.
- **Résolution synchrone des conflits** lors de l'exécution parallèle de DAGs multi-agents.
- **Capacité d'auto-amélioration continue et déterministe** du framework mLoop par lui-même.

### Statut d'Alignement :
- Analyse R&D approuvée par le PO.
- ADR consigné sous `docs/01-architecture/ADR-0308_jcode_memory_swarm_and_selfdev_innovations.md`.
