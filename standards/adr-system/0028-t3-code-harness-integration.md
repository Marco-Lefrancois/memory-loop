# ADR-0028 : Intégration du Control Surface T3 Code (`pingdotgg/t3code`) avec l'Écosystème mLoop

- **Statut** : Proposé (Standby / En attente de validation)
- **Date** : 2026-08-07
- **Auteurs** : Équipe mLoop Swarm & AI Assistant
- **Périmètre** : Framework Backend mLoop, Surface de Contrôle Visuelle, Interfaces Multi-plateformes (Desktop/Mobile)

---

## 1. Contexte

Le projet **T3 Code** (`pingdotgg/t3code`) développé par Ping.gg offre une interface de contrôle unifiée (*agent harness control surface*) multi-plateforme (Desktop Electron, Web, iOS, Android). T3 Code permet de piloter visuellement et à distance des agents CLI (OpenCode, Claude Code, Codex, Cursor, Grok Build) en communiquant avec leur serveur local Node.js / WebSocket via un protocole standardisé sur `stdio` / RPC.

mLoop opère en tant que **Cerveau d'État & Orchestrateur** (Backend Python). Afin d'offrir une expérience de supervision mobile et desktop sans réinventer de frontends mobiles natifs, mLoop intègre T3 Code comme couche de présentation visuelle tout en conservant la gouvernance stricte de la mémoire, du graphe de connaissances et des guardrails.

---

## 2. Décisions d'Architecture

### 2.1 Axe 1 : Modèle Découplé "Cerveau mLoop <-> Surface T3 Code"
- **Surface Visuelle (T3 Code)** : T3 Code prend en charge l'affichage réactif, le mode supervisé (*Supervised Approval*), la gestion de git worktrees et les notifications mobiles (iOS/Android).
- **Cerveau d'État (mLoop)** : mLoop conserve la propriété exclusive du graphe de connaissances (`graphify`), du RAG d'évidence (`memory/evidence/`), de la mémoire FTS5 et des guardrails pré-vol (`vibe-check`).

### 2.2 Axe 2 : Intégration par le Standard OpenCode (`opencode.json`)
- T3 Code supportant nativement OpenCode CLI, mLoop s'interface avec T3 Code via l'écosystème `opencode.json` et les ponts MCP (`src/bridges/mcp_*.py`).
- Les commandes et guardrails `python src/swarm.py` s'exécutent en arrière-plan et rapportent leur état synchrone dans les sessions d'agents T3 Code.

### 2.3 Axe 3 : Pont de Télémesure & Restauration (`swarm.py t3-bridge`)
- Ajout de capacités de sérialisation JSON-RPC / WebSocket pour diffuser l'état du backlog (`sprint_backlog.md`), les EvidencePacks et le statut du Vibe-Check vers les clients distants de T3 Code.

---

## 3. Conséquences & Impacts sur les 8 Piliers mLoop

- **Moteur Swarm & CLI** : Conservation de `src/swarm.py` comme point d'entrée universel.
- **Ponts MCP** : Extension des capacités de pontage MCP pour relayer la télémétrie des sessions mLoop vers T3 Code.
- **Directives & Guardrails** : Le mode supervisé de T3 Code renforce la règle *Ask first / Porte de confirmation* de mLoop.
- **Ergonomie Mobile & Déportée** : Possibilité de piloter et superviser le Cerveau mLoop en mobilité depuis l'application iOS / Android T3 Code.

---

## 4. Statut d'Alignement
- **Fichier SSOT** : `docs/01-architecture/ADR-0028_t3_code_harness_integration.md`
- **Skill Associé** : `research-and-develop` (`.agents/skills/research-and-develop/SKILL.md`)
