# ADR-0345 : Intégration Approfondie de Herdr Runtime v0.8.2, Matrice Zero-Blindspot & Architecture Plugin Officiel mLoop

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-02
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Multiplexage PTY Herdr v0.8.2, Plugin Officiel, Primitives Layout/Metadata/Notifications, Zero-Blindspot Governance

---

## 1. Contexte & Rationale (Crawl R&D Herdr v0.8.2)

Suite à la session R&D menée sur la documentation officielle ([herdr.dev/docs](https://herdr.dev/docs/)), le catalogue de plugins ([herdr.dev/plugins](https://herdr.dev/plugins/)) et le dépôt GitHub ([github.com/herdrdev/herdr](https://github.com/herdrdev/herdr)), l'écosystème **Herdr v0.8.2** a atteint un degré de maturité critique pour l'exécution d'essaims d'agents de code autonomes (900+ plugins, streaming d'événements, notifications, détection déclarative TOML d'états, alternate-screen unwrapping).

Cette ADR standardise l'évolution de l'intégration Herdr au sein de mLoop afin de garantir une **hygiène d'exécution irréprochable (Zero Zombie Policy)**, une **résilience multi-OS totale (Zero-Blindspot)** et la création du **plugin officiel `mloop-herdr-plugin`**.

---

## 2. Décisions d'Architecture

### 2.1 Extension des Primitives de Contrôle Herdr (v0.8.2)
L'adaptateur central (`src/core/herdr_adapter.py`) et le pont MCP (`src/bridges/mcp_herdr.py`) sont enrichis des primitives suivantes :
1. **Layout Déclaratif BSP (`layout.export` / `layout.apply`)** : Permet à mLoop de sauvegarder ou instancier des topologies de travail complexes en un seul appel atomique.
2. **Métadonnées et Badges de Volets (`pane.report_metadata`)** : Injection de jetons dynamiques (`$summary`, `$status`) visibles dans la barre latérale Herdr sans altérer l'état sémantique du cycle de vie.
3. **Notifications Toasts Légères (`notification.show`)** : Alertes visuelles et sonores non-bloquantes (Deadlocks, Circuit Breaker, Fin de Story).
4. **Introspection du Moteur d'États (`agent.explain`)** : Diagnostic déterministe des règles TOML pour les états `working`, `blocked`, `idle`, `done`.

### 2.2 Matrice de Résilience & Couverture des 4 Vecteurs d'Angles Morts (ADR-0306)
- **Vecteur 1 (Runtimes & OS)** : Fonction `ensure_windows_agent_binaries()` pérennisée pour neutraliser les shims npm (`.ps1`, `.cmd`) sous Windows et forcer l'usage du binaire compilé `opencode.exe`.
- **Vecteur 2 (Lifecycles & Zombie Leaks)** : Protocole de purge automatique `audit_and_reap_zombies()` éliminant tout worker `IDLE` sans mission lors de la fermeture de session.
- **Vecteur 3 (Race Conditions & Séquencement)** :
  - Respect du délai d'amorçage `interactive_ready` (~3s) avant soumission de prompt.
  - Lecture alternate-screen conditionnelle : bascule transparente sur `visible` si l'agent est encore en cours d'exécution (`working`), évitant l'erreur `agent_not_idle`.
- **Vecteur 4 (Headless & CI/CD)** : Injection systématique de `--no-focus`, `--yes` et `HERDR_DISABLE_SOUND=1` pour les environnements de test et CI.

### 2.3 Architecture du Plugin Officiel `mloop-herdr-plugin`
Création du package déclaratif sous `plugins/mloop-herdr-plugin/` conforme au standard `herdr-plugin.toml` :
- **`[[panes]]`** :
  - `backlog` : Vue fractionnée (Split) du `sprint_backlog.md` et des critères INVEST.
  - `evidence` : Volet superposition (Overlay) des EvidencePacks JSON.
  - `dag` : Moniteur d'événements du DAG (`memory/herdr_events.jsonl`).
- **`[[actions]]`** :
  - `status` : Synthèse globale du projet mLoop.
  - `reap_zombies` : Purge immédiate des volets orphelins.
  - `sync` : Synchronisation du graphe sémantique Graphify.

---

## 3. Conséquences & Bénéfices

- **Isolation Cognitive Parfaite** : Les workers exécutent leurs missions dans des sessions vierges (Clean Slate Protocol) sans saturer le contexte de l'orchestrateur.
- **Zéro Dérive d'Exécution** : Élimination des processus résiduels en mémoire et traçabilité 100% autonome dans les EvidencePacks.
- **Observabilité TUI Supérieure** : Suivi visuel unifié des agents, du backlog et des événements DAG depuis l'interface Herdr.

---

## 4. Statut d'Alignement & Fichiers Cibles
- **SSOT Code** : `src/core/herdr_adapter.py`, `src/bridges/mcp_herdr.py`, `src/pipelines/graph_router.py`, `src/pipelines/worker_pipeline.py`
- **Plugin Manifest** : `plugins/mloop-herdr-plugin/herdr-plugin.toml` & `plugins/mloop-herdr-plugin/tui_panes.py`
- **Skill Associé** : `.agents/skills/herdr-orchestration/SKILL.md`
