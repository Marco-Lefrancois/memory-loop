# mLoop - 02. Architecture à Deux Couches (Cerveau & Moteur)

L'architecture de mLoop sépare strictly l'intelligence cognitive (Système 2) de la gouvernance et de la validation déterministe (Système 1).

## Couche 1 : L'IDE Agentique (Le Cerveau - Exécution Syst. 2)
Le Cerveau réside directement dans l'IDE du développeur. Il est modélisé sous la forme d'un swarm d'agents autonomes configurés via le frontmatter YAML dans `.agents/agents/` ou les compétences portables dans `.agents/skills/` :
*   **orchestrator** : Assure la supervision générale, pilote les sessions, gère l'état actif dans le nœud `ML_ACTIVE_STATE` du graphe de connaissances, et coordonne les 5 phases du workflow.
*   **plan** : Chargé de la modélisation stratégique, du DDD, du protocole d'entrevue interactive "Grill with Docs", de la mise à jour de `CONTEXT.md` et de la génération du PRD et du Story Constraint Contract (SCC) dans le backlog.
*   **sentinel / validate** : Barrière de qualité intransigeante. Audite la conformité fonctionnelle et structurelle, valide les 4 piliers Gherkin, exécute `wikifix`, la suite `aoep` et calcule le score INVEST final.
*   **build** : Skill d'auto-développement physique réservé exclusivement à l'évolution interne du framework mLoop (`C:\Memory Loop\src`). Pour les projets clients, le rôle Build est délégué au développeur humain.

Leur comportement est orienté par un sous-système de 21+ compétences portables (dossier `.agents/skills/` : `analyze`, `plan`, `validate`, `triage`, `sentinel`, `rubber-duck`, `graph-engineering`, `calibrate`, `blindspot-scan`, `tdd`, `wait-what`, etc.).

## Couche 2 : Le Backend mLoop (Le Moteur - Gouvernance Syst. 1)
Le code Python natif de Memory Loop (`src/swarm.py` et les pipelines dans `src/pipelines/`) agit comme un système d'exploitation et de validation déterministe. Les opérations critiques transitent par ce moteur via l'interface CLI :
*   `python src/swarm.py resume --project <p>` : Restauration de session anti-amnésie.
*   `python src/swarm.py sync --project <p>` : Synchronisation absolue du graphe (Graphify) avec le disque.
*   `python src/swarm.py wikifix` : Linter sémantique actif et mécanique (Auto-Healing, contrôle d'encapsulation).
*   `python src/swarm.py calibrate --project <p>` : Auto-étalonnage continu des 8 composants de l'écosystème mLoop.
*   `python src/swarm.py graph-run --project <p>` : Exécution de la topologie Graph Engineering (DAG Multi-Agents).
*   `python src/swarm.py aoep` : Suite d'évaluation d'état persistant (Always-On Evaluation Protocol).
*   `python src/swarm.py plugin-validate` & `plugin-export` : Validation et exportation du package Agent Plugins 1.0 (ADR-0309).
*   `python src/swarm.py cycle-status --project <p>` : Diagnostic de progression du projet sur les 5 phases.
*   `python src/swarm.py jira_sync --project <p>` : Synchronisation bidirectionnelle du backlog local vers Jira (gouvernance Story-Only).
*   `python src/swarm.py optimize --keyword "<kw>" --msg "<msg>"` : Génération d'une contrainte d'affaires RHO.
*   `python src/swarm.py ingest` / `research` / `crawl` : Pipelines d'acquisition et d'ingestion documentaire.
*   `python src/bridges/story_guard.py` : Garde-fou actif protégeant le SCC contre les modifications hors-périmètre.
