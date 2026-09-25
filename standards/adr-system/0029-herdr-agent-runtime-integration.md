# ADR-0029 : Intégration du Runtime Multi-Agents & Daemon Persistant Herdr (`herdrdev/herdr` v0.8.0) dans mLoop

- **Statut** : Approuvé (En Implémentation)
- **Date** : 2026-08-12
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Multiplexage PTY, Daemon Rust Persistant, Socket API Agentique, Unattended Mode
- **Amendement ADR-0389 (25 sept. 2026)** : Substitution de `opencode --yolo` par `opencode --auto --agent worker` et ajout de `cline --auto-approve true`.

---

## 1. Contexte & Découverte Technique

Le projet **Herdr** (`herdrdev/herdr` / `https://herdr.dev/`) v0.8.0 est un daemon Rust d'arrière-plan et runtime universel pour agents de code. Contrairement aux simples multiplexeurs de terminal, Herdr expose des primitives d'automatisation orientées agents (`Layout`, `Pane`, `Agent`) et supervise l'état du cycle de vie (`working`, `blocked`, `idle`, `done`, `unknown`).

### Primitives Cœur Herdr v0.8.0 :
1. **Layout Primitive (`workspace`, `tab`)** :
   - `herdr workspace create --cwd <path> --label <label> --no-focus` (retourne `.result.root_pane.pane_id`).
   - `herdr pane split <pane_id> --direction [right|down] --no-focus` (retourne `.result.pane.pane_id`).
2. **Pane Primitive (Contrôle PTY Brut)** :
   - `herdr pane run <pane_id> "<command>"`
   - `herdr pane wait-output <pane_id> --regex "<pattern>" --timeout <ms>`
   - `herdr pane capture -p <pane_id> --lines 100` / `herdr pane close -p <pane_id>`
3. **Agent Primitive (Contrôle d'Agents Détectés)** :
   - `herdr agent start <name> --kind <opencode|claude|codex|gemini> --pane <pane_id> -- <flags>`
   - `herdr agent prompt <name> "<prompt>" --wait --timeout <ms>`
   - `herdr agent wait <name> --until [idle|done|blocked|working]`
   - `herdr agent read <name> --source recent-unwrapped --lines 120` (Support Alternate-Screen PTY pour Claude Code / OpenCode).

---

## 2. Décisions d'Architecture

### 2.1 Axe 1 : Modèle Tripartite "Herdr Daemon (v0.8.0) <-> mLoop Kernel (v2.0.0) <-> Agents Autonomes"
- **Couche 0 - Daemon Rust & Socket Unix (`~/.herdr/herdr.sock`)** : Maintient les PTY ouverts et surveille les changements d'état (`blocked` $\rightarrow$ alerte HITL).
- **Couche 1 - Cerveau mLoop (System 2 & 1)** : Gère le cadrage Spec-Driven (5 phases), le découpage verticaux SCC, les verrous `story_guard.py` et les artefacts JSON EvidencePack (`memory/evidence/`).
- **Couche 2 - Sub-Agents Autonomes (Workers)** : Lancement en mode Unattended (`opencode --yolo`, `claude --dangerously-skip-permissions`) dans des sous-panneaux isolés.

### 2.2 Axe 2 : Intégration dans le Cycle 5 Phases Spec-Driven
- **Phase 1 SPEC** : Ingestion mono/multi-panneau (`ingest`).
- **Phase 2 PLAN** : L'orchestrateur maître (`p1`) analyse, produit le SCC (`US-XXX.md`), prépare les sous-tâches.
- **Phase 3 BUILD (Herdr Runtime)** : Master split Herdr (`p2`, `p3`), démarre les workers, envoie les prompts avec `agent prompt --wait` ou `agent wait --until idle`. `story_guard.py` garantit l'isolation physique.
- **Phase 4 VALIDATE (mLoop Gatekeeping)** : Master lit la sortie via `agent read --source recent-unwrapped`, lance la QA dans `p4` (`pytest` + `wikifix`), valide les 4 Piliers Gherkin, génère l'EvidencePack JSON.
- **Phase 5 SHIP / MEMORY** : Met à jour Graphify (`sync`), synchronise vers Jira Cloud (`jira_sync` Story-Only), auto-étalonne (`calibrate` 8/8 PASS) et ferme les panneaux (`pane close`).

---

## 3. Statut d'Alignement
- **Fichier SSOT** : `docs/01-architecture/ADR-0029_herdr_agent_runtime_integration.md`
- **Skill Associé** : `herdr-orchestration` (`.agents/skills/herdr-orchestration/SKILL.md`)
- **Adaptateur Core** : `src/core/herdr_adapter.py` & Pont MCP `src/bridges/mcp_herdr.py`
