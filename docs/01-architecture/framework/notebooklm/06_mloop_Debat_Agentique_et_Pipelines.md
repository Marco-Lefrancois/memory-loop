# mLoop - 06. Débat Agentique & Pipelines Fonctionnels

Pour s'assurer que le backlog ne dérive pas vers du couplage technique (Scope Creep) et reste conforme aux exigences d'affaires, mLoop implémente un système de Débat Agentique et des pipelines d'action dédiés.

## 🧠 Le Moteur de Débat Agentique (Architecture d'Affaires)
L'analyse des règles complexes ou ambiguës est soumise à un stress-test via le moteur de débat à trois têtes (`src/bridges/agentic_debate.py`). Ce mécanisme structure la réflexion stratégique en opposant trois agents dotés d'expertises et de postures cognitives complémentaires :
1.  **Le Proposeur (DDD Architect)** : Formule une proposition d'architecture d'affaires (modèle conceptuel, flux de données, interfaces). Il a l'interdiction formelle d'écrire ou de suggérer du code d'implémentation.
2.  **Le Challenger (Red Team)** : Attaque la proposition en identifiant les failles logiques, les conditions aux limites (Edge Cases), les pannes et les contraintes de sécurité.
3.  **Le Juge (Synthesizer)** : Arbitre les débats et traduit la synthèse finale sous forme de scénarios de test Gherkin clairs, prêts à être injectés dans le Story Constraint Contract (SCC).

## 🔄 L'Automatisation via Batch Debate
Le script d'orchestration `src/bridges/batch_debate.py` permet de soumettre l'ensemble du backlog à cette évaluation de manière asynchrone :
*   **Ingestion** : Scanne de manière autonome les récits du dossier `backlog/stories/`.
*   **Identification** : Détermine la problématique métier ou le point de blocage architectural le plus critique de chaque story.
*   **Exécution** : Lance le débat à trois têtes sur ce point spécifique.
*   **Archivage** : Enregistre le transcript complet sous `memory/debate_transcript_<ID_story>.md`.
*   **Questions Ouvertes (OQ)** : Si des ambiguïtés d'affaires persistent et nécessitent une décision humaine, elles sont consignées formellement dans `docs/04-transverse/00-questions-ouvertes.md` sous la référence `OQ-XXX`.

## 🛠️ Les Pipelines du Kernel System 1
Le Backend mLoop propose une suite complète de pipelines d'ingénierie et d'orchestration :
*   **`graph-run` (Graph Engineering DAG)** : Lance l'exécution de la topologie multi-agents (Pattern Diamant, Risk Router, Evidence Reducer).
*   **`calibrate` (Ecosystem Calibration)** : Exécute l'auto-étalonnage déterministe en 8 points avec autoréparation (Auto-Repair).
*   **`cycle-status` (5-Phase Progress Diagnostic)** : Diagnostique le niveau de maturité et d'avancement du projet à travers les 5 phases du cycle.
*   **`plugin-validate` & `plugin-export`** : Valide et empaquète l'écosystème au standard Agent Plugins 1.0 (ADR-0309) pour distribution multi-IDE.
*   **`aoep` (Always-On Evaluation Protocol)** : Exécute la suite de tests de gouvernance d'état persistant.
*   **`jira_sync` (Backlog Sync)** : Assure la synchronisation bidirectionnelle du backlog fonctionnel local avec Jira Cloud (governance Story-Only).
*   **`research` & `crawl`** : Recherche autonome Scout/Crawl et ingestion web vers Markdown structuré (`memory/docs_cache/`).
*   **`dashboard` (Web Console)** : Console FastAPI/Uvicorn locale (port 8000) pour visualiser le graphe, les sessions et la santé du projet.
