# mLoop - 04. Auto-Amélioration RHO & Moteur de Calibrage

mLoop est un système **auto-apprenant** et **auto-étalonné**. Il utilise la méthode RHO (Retrospective Harness Optimization) et le moteur `Calibrate Engine` pour s'immuniser contre ses propres erreurs et prévenir le drift système.

## Le concept de Self-Validation (Chaos Testing)
Au lieu de corriger de façon temporaire un anti-pattern, l'agent IDE (Système 2) utilise la "Self-Validation" :
1. **Détection** : L'agent rencontre une erreur récurrente de compilation, un bug sémantique, ou identifie qu'il a produit un livrable contraire aux règles d'affaires.
2. **Cristallisation** : L'agent Sentinel ou l'orchestrateur invoque la commande d'optimisation du moteur : `python src/swarm.py optimize --keyword "<mot-clé ou erreur>" --msg "<directive de correction>" --scope <project|global>`.

## Double Portée (Global vs Local)
Les règles générées par RHO sont stockées sous format YAML selon leur portée :
*   **Scope Global (`standards/rho_rules.yaml`)** : Pour les interdictions architecturales, les règles de sécurité ou de conformité sémantique applicables à l'ensemble de l'écosystème Memory Loop.
*   **Scope Projet (`Projects/<nom_projet>/memory/rho_rules.yaml`)** : Pour les contraintes d'affaires ou règles de nommage spécifiques à un projet particulier.

## Application active par WikiFix & Moteur Calibrate
* **Wikifix** : Lors de chaque phase d'audit (ou exécution de `python src/swarm.py wikifix` / `sync`), le moteur charge dynamiquement ces règles RHO. Si une occurrence du mot-clé est repérée, `wikifix` lève une violation bloquante.
* **Calibrate Engine (`python src/swarm.py calibrate`)** : Auto-étalonnage continu vérifiant 8 points de contrôle critiques (CLI, raccourcis OpenCode, ponts MCP, index des skills, directives AGENTS/GEMINI, blueprints, SQLite/Graphify, registres SHA256 et guardrails audit-loop). En cas d'écart, le moteur exécute une autoréparation automatique (*Auto-Repair*).
