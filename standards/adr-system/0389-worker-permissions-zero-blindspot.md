# ADR-0389 : Gouvernance & Unification des Permissions des Workers Herdr (OpenCode & Cline)

* **Statut** : ACCEPTÉ
* **Date** : 25 septembre 2026
* **Décideurs** : Architecte en Chef, Core Team mLoop
* **Contexte** : Remplacement des flags obsolètes `--yolo`, auto-approbation déterministe unattended, gestion d'external_directory et personas dédiées pour les sous-agents OpenCode et Cline.
* **Référence d'audit** : ADR-0376 (Rigueur 360° Zéro Blindspot), ADR-0346 (Délégation Dual-Track), ADR-0311 (Optimisation OpenCode).

---

## 1. Contexte & Problématique

L'orchestration des User Stories via Herdr instancie des sous-agents éphémères dans des volets PTY isolés (`spawn_story_worker`).
L'audit technique a mis en évidence plusieurs failles de permissions causant le blocage systématique des workers et de l'orchestrateur (règles `opencode_permission` et `tool_permission` de `herdr.exe` passant l'agent en état `blocked`) :

1. **Flag OpenCode obsolète** : OpenCode 1.18.30 n'implémente pas `--yolo`. Le drapeau officiel d'auto-approbation sans invite est `--auto`.
2. **Absence de Persona Worker** : OpenCode démarrait sans `--agent worker`, retombant sur `orchestrator` qui applique `edit: ask`, gelant toute tentative d'écriture de livrable ou de code.
3. **Périmètre `external_directory` bloquant** : L'accès depuis `Projects/<projet>` aux scripts racines (`src/swarm.py`) déclenchait la permission `external_directory: ask`.
4. **Auto-approbation implicite Cline** : Cline 3.x dans un PTY interactif sans prompt CLI pouvait inviter à confirmer l'exécution des commandes sans le drapeau explicite `--auto-approve true`.
5. **Orchestrateur** : `start-orchestrator.ps1` utilisait lui-même `opencode --yolo`.

---

## 2. Décisions d'Architecture

### 2.1. Registre SSOT des Runtimes (`worker_runtimes.py`)
- **OpenCode** : `one_shot_flags=["--auto", "--agent", "worker"]`.
  - `--auto` garantit l'absence d'invites d'outils interactifs.
  - `--agent worker` charge la persona isolée avec `edit: allow` et `bash: allow`.
- **Cline** : `one_shot_flags=["--auto-approve", "true"]`.
  - Garantit l'exécution déterministe des outils en session PTY interactif.

### 2.2. Permissions Globales et Blueprints de Projets
- Injection de `external_directory: { "*": "allow" }` dans `opencode.json` racine et dans le gabarit `standards/blueprints/project_opencode_template.json`.
- Injection systématique du bloc `permission` complet lors de l'initialisation ou synchronisation de projet via `src/commands/handlers/opencode.py`.

### 2.3. Amorçage Orchestrateur
- `scripts/start-orchestrator.ps1` démarre avec `opencode --auto --agent orchestrator`.

### 2.4. Pipelines de Délégation Spécialisée
- Suppression des flags `["--yolo"]` codés en dur dans `handoff_simulator.py`, `legacy_miner.py`, `shadow_estimator.py`, `visual_dissector.py` au profit de l'appel au registre `get_worker_runtime("opencode").build_flags(...)`.

---

## 3. Conséquences & Bénéfices

- **Zéro blocage unattended** : Les workers OpenCode et Cline exécutent leurs missions sans interruption ni attente d'entrée clavier humaine dans les sous-panneaux Herdr.
- **Conformité stricte Herdr** : Élimination des états `blocked` détectés par les règles binaires de `herdr.exe`.
- **Isolation garantie** : Les workers opèrent avec leur persona `worker` dédiée (steps capés, règles Clean Slate) sans polluer la posture de l'orchestrateur.
- **Rétrocompatibilité** : Préservation des surcharges via `extra_args` et conservation de la sélection dynamique de modèle.
