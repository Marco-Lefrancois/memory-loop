---
id: MLOOP-389-BE
jira_key: ''
epic_key: EPIC-36-HERDR-WORKER-PERMISSIONS-AND-RUNTIME-GOVERNANCE
type: Feature
title: Gouvernance & Unification des Permissions des Workers Herdr (OpenCode & Cline)
tags:
- herdr
- permissions
- opencode
- cline
- worker-runtimes
- unattended
status: QA_CERTIFIED
layer: backend
invest_score: 6/6
macrostructure: workbench
validated_by: Marco
validated_at: '2026-09-25T18:35:00.000000+00:00'
ttl_cycles: 4
---
# Gouvernance & Unification des Permissions des Workers Herdr (OpenCode & Cline)

---

## Description
**En tant qu'** Orchestrateur mLoop ou développeur lançant des missions de cadrage ou de build via `worker-spawn`,  
**je veux** que les workers OpenCode et Cline démarrent avec des drapeaux d'auto-approbation valides et les personas adaptées,  
**afin d'** exécuter les missions de manière autonome sans invites d'approbation interactives bloquant les sous-volets terminaux PTY.

---

## Contexte & Périmètre

### Contexte Métier
Dans l'architecture mLoop, l'orchestrateur délègue les tâches de dev et d'audit à des sous-agents éphémères tournant dans des volets multiplexés Herdr v0.8.2+. L'audit a mis en évidence que les workers démarraient avec le drapeau obsolète `--yolo` (OpenCode 1.18.30) ou sans drapeau d'auto-approbation explicite (Cline 3.0.65), déclenchant les règles de détection de blocage de `herdr.exe` (`opencode_permission` et `tool_permission`) et provoquant la mort par timeout des workers unattended. Ce récit formalise la mise à niveau du registre des runtimes, la résolution d'`external_directory` et l'affectation de la persona `worker`.

### In-Scope
- Remplacement du flag `--yolo` par `--auto` et sélection systématique `--agent worker` pour OpenCode dans `src/core/worker_runtimes.py`.
- Injection explicite de `--auto-approve true` pour Cline 3.x garantissant l'absence d'invites d'outils en terminal PTY.
- Décloisonnement de la permission `external_directory: { "*": "allow" }` dans `opencode.json` et `standards/blueprints/project_opencode_template.json`.
- Mise à jour de `scripts/start-orchestrator.ps1` (`opencode --auto --agent orchestrator`).
- Remplacement des arguments `--yolo` codés en dur dans les 4 pipelines de délégation (`handoff_simulator`, `legacy_miner`, `shadow_estimator`, `visual_dissector`).
- Suite de tests de non-régression et couverture unitaire complète dans `tests/test_worker_permissions.py`.

### Out-of-Scope
- Migration par lot des fichiers `opencode.json` des projets existants sous `Projects/` (couvert par `MLOOP-390-BE`).
- Sonde d'audit dynamique Vibe-Check Check 31 (couvert par `MLOOP-391-BE`).
- Nouveaux runtimes tiers (Gemini, Claude Code, Cursor) (couvert par `MLOOP-392-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Résolution Déterministe des Flags d'Instanciation
* **Entrée Métier** : Kind du worker (`opencode` ou `cline`), modèle cible et arguments optionnels `extra_args`.
* **Règles d'admissibilité & Validation** : 
  - Tout worker OpenCode doit recevoir au minimum `["--auto", "--agent", "worker"]`.
  - Tout worker Cline doit recevoir au minimum `["--auto-approve", "true"]`.
  - En mode Plan (`task_type in ("plan", "grill", "analyse")`), Cline conserve son auto-approbation tout en recevant `--plan`.
* **Résultat Métier** : Les agents démarrent sans invite bloquante et passent directement à l'état `working`.
* **Cas de Rejet** : Tout échec d'instanciation de Cline déclenche le Circuit-Breaker vers OpenCode avec les drapeaux `--auto`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Registre Runtimes** : `WorkerRuntimeSpec.build_flags(model: Optional[str], extra_args: Optional[List[str]]) -> List[str]`
* **Instanciation Herdr** : `HerdrWorkerMixin.spawn_story_worker(project_name: str, story_id: str, kind: str, ...) -> Dict[str, Any]`

---

## Règles d'affaires

- **Auto-Approbation Obligatoire en Mode Unattended** : Un agent démarré dans un sous-panneau Herdr ne doit jamais requérir de saisie clavier pour autoriser un outil (`read`, `edit`, `bash`).
- **Persona Confinée** : Tout worker OpenCode s'exécute sous la persona `worker` (steps capés à 50, règles strictes d'arrêt) et non sous `orchestrator`.
- **Accès Transverse Décloisonné** : Les commandes transverses (`python src/swarm.py resume`) appelées depuis un sous-dossier de projet ne doivent subir aucun blocage d'`external_directory`.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Scénario Nominal (Instanciation d'un Worker OpenCode Auto-Approuvé)
* **GIVEN** Un orchestrateur mLoop déclenchant `herdr.spawn_story_worker` pour la story `US-01` avec `kind="opencode"`.
* **WHEN** Le registre `WORKER_RUNTIMES` construit les arguments CLI.
* **THEN** Les arguments contiennent strictement `"--auto"`, `"--agent"`, `"worker"`.
* **AND** Le worker OpenCode démarre dans le volet PTY sans afficher le prompt `Permission required`.

### Pilier 2 : Scénario d'Exception (Préservation d'Auto-Approbation Cline en Mode Plan)
* **GIVEN** Un worker Cline instancié pour une tâche d'analyse ou de planification (`task_type="plan"`).
* **WHEN** Le module `PlanActGuard.enforce_flags` applique les drapeaux de cycle de vie.
* **THEN** La ligne de commande finale contient à la fois `"--auto-approve"`, `"true"` et `"--plan"`.
* **AND** Cline exécute les outils d'inspection sans solliciter l'utilisateur.

### Pilier 3 : Scénario de Résilience (Accès External Directory sans Blocage)
* **GIVEN** Un worker OpenCode dont le répertoire de travail est `Projects/BoireFrere_Segment2`.
* **WHEN** Le prompt initial exécute `python src/swarm.py resume --project BoireFrere_Segment2`.
* **THEN** La permission `external_directory: { "*": "allow" }` autorise l'accès à `C:\Memory Loop\src\swarm.py`.
* **AND** Aucune exception ni freeze terminal n'est constaté.

### Pilier 4 : Scénario UX & Observabilité (Zéro Zombie Détecté par Herdr)
* **GIVEN** Des workers en cours d'exécution sous Herdr.
* **WHEN** La sonde `herdr.detect_stalled_agents()` analyse les sorties de terminal.
* **THEN** Aucun agent n'est classifié dans l'état `blocked` par les règles `opencode_permission` ou `tool_permission`.
* **AND** Les volets se clôturent normalement lors du moissonnage de preuves `worker-harvest`.

---

## Références

### 1. Décisions d'Architecture SSOT
- 🏛️ **ADR Fondateur** : [`standards/adr-system/0389-worker-permissions-zero-blindspot.md`](file:///C:/Memory%20Loop/standards/adr-system/0389-worker-permissions-zero-blindspot.md)
- 🏛️ **ADRs Amendés** : [`ADR-0029`](file:///C:/Memory%20Loop/standards/adr-system/0029-herdr-agent-runtime-integration.md), [`ADR-0205`](file:///C:/Memory%20Loop/standards/adr-system/0205-herdr-subagent-lifecycle-context-isolation.md), [`ADR-0346`](file:///C:/Memory%20Loop/standards/adr-system/0346-specialized-agent-delegation-gates.md)
- 📐 **Protocole d'Audit 360°** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)
