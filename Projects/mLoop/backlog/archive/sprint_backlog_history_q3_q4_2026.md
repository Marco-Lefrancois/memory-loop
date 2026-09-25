# 🏛️ Registre Historique des Épopées Livrées — mLoop (Q3-Q4 2026)

> 📦 **Statut** : ARCHIVE SOUVERAINE SCELLÉE (Épopées scellées Post-Git)
> **Certification** : Tous les récits sont physiquement livrés, testés (pytest 100% PASS), et scellés.
> **Sprint Backlog Actif** : [../sprint_backlog.md](../sprint_backlog.md)

---

## Épopée : EPIC-21-MCP-MODERN-SUITE (Standards MCP 2026-07-28 & Extensions) [OPEN]

> 🌐 **Origine** : Audit d'évolution protocolaire MCP du 24/09/2026 — intégration des spécifications modernes 2026-07-28 : extension `Tasks` (découplage asynchrone et suppression des timeouts), extension `MCP Apps` (`ui://` pour projection in-IDE d'Archify et DrawDB), extension `Elicitation` (Form Mode pour Grill-Me interactif en clean-slate), et `Skills over MCP` (allègement AGENTS.md). Références : ADR-0202, ADR-0308, ADR-0374, ADR-0376, ADR-0387. Backlog détaillé : [`epics/epic_mcp_modern_suite_2026q4.md`](epics/epic_mcp_modern_suite_2026q4.md). Récits 210/211 : Palier 2 `READY_FOR_DEV` (validé humain 2026-09-24, grill ADR-005/006) ; récits 212-215 : Palier 2 `READY_FOR_DEV` (validé humain 2026-09-24, session Grill EPIC-21 — grill ADR-007 à ADR-010, conversion Palier 2, Rubber Duck PASS ×4 Trust 91.6/0 bloquant ; **épopée 6/6 `READY_FOR_DEV`**).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-210-BE** | - | Bridges/Core | Socle Protocolaire MCP 2026-07-28 : Négociation de Version & Header Routing | ✅ `DONE` | `SHIPPED` | ✅ Build achevé (2026-09-24) · 1437 tests verts |
| [ ] | **MLOOP-211-BE** | - | Bridges/Herdr | Extension Tasks (`io.modelcontextprotocol/tasks`) : Handles Asynchrones pour Herdr | ✅ `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · cert `N1-TACHES-ASYNC` PASS (3/3) · 1697 tests verts |
| [x] | **MLOOP-212-FE** | - | Bridges/UI | Extension MCP Apps (`io.modelcontextprotocol/ui`) : Exposition `ui://` Archify & DrawDB | ✅ `DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-24) |
| [ ] | **MLOOP-213-BE** | - | Bridges/Grill | Extension Elicitation : Formulaire Interactif Form Mode pour Grill-with-Docs | ✅ `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-24) · cert `N1-ELICITATION-FORM` PASS · 1611 tests verts |
| [ ] | **MLOOP-214-BE** | - | Bridges/Skills | Standard Skills over MCP (`io.modelcontextprotocol/skills`) : Exposition Dynamique des Compétences mLoop | ✅ `DONE` | 🟣 `DONE_TESTED` | 👤 Humain (validé 2026-09-24, Grill EPIC-21) |
| [ ] | **MLOOP-215-FULL** | - | QA/Certification | Harnais de Certification & Conformité E2E MCP 2026-07-28 & Non-Régression Multi-IDE | ✅ `DONE` | 🟣 `DONE_TESTED` | 👤 Humain (validé 2026-09-24, Grill EPIC-21) |


---

## Épopée : EPIC-22-TOOLING-ECOSYSTEM-HARNESS (Intégration Opérationnelle de l'Écosystème Tooling mLoop) [DONE]

> 🛠️ **Origine** : Rationalisation des outils de développement mLoop (Q4 2026) : création du domaine `06-tooling-ecosystem/` (KN-050, KN-051, KN-052), sanctuarisation de Plannotator sous `%LOCALAPPDATA%`, et déploiement d'un harnais d'orchestration unifié sans dossiers orphelins à la racine. Cadrage Macro-Grill VALIDÉ le 24/09/2026 via ADR-014. Feu vert humain PO (2026-09-24). **Livré et certifié le 24/09/2026 (24/24 tests verts, AST ≤ 271L, Vibe-Check OK)**. Références : KN-050, KN-051, KN-052, `PHASE_FILES_AND_TEST_PLAN.md`, ADR-0202, ADR-0370, ADR-0376, ADR-014. Backlog détaillé : [`epics/epic_tooling_ecosystem_harness.md`](epics/epic_tooling_ecosystem_harness.md).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-220-BE** | - | CLI/OpenCode | Bridge d'Exécution & Commande CLI OpenCode (Intégration Declarative opencode.json) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 24 tests verts |
| [x] | **MLOOP-221-BE** | - | Pipelines/Plannotator | Harnais Automatisé Plannotator (Génération, Validation Visuelle HITL & Archivage Canonique) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 24 tests verts |
| [x] | **MLOOP-222-BE** | - | Pipelines/Wayfinder | Pipeline Décisionnel Wayfinder (Cartographie de Décisions & Sous-Agents Asynchrones AFK) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 24 tests verts |
| [x] | **MLOOP-223-FE** | - | Dashboard/Tooling | Module Dashboard pour l'Écosystème Tooling & Visualisation des Runtimes Développeur | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 24 tests verts |
| [x] | **MLOOP-224-FULL**| - | QA/Certification | Harnais de Certification E2E du Cycle Tooling (Phase -> Plan Visuel -> Build -> Vibe-Check) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 24 tests verts |


---

## Épopée : EPIC-23-DATA-HYGIENE-AND-RETENTION (Gouvernance du Stockage Persistant & Rétention) [DONE]

> 🧹 **Origine** : Audit volumétrique de `memory/` (24/09/2026) : 565 Mo cumulés (base SQLite 429 Mo, cache crawler 118 Mo, logs cumulatifs sans rotation). Déploiement d'un moteur de rétention, défragmentation et log rotation continue inspiré d'Ebbinghaus (ADR-0003). Cadrage Macro-Grill VALIDÉ le 24/09/2026 via ADR-015. Feu vert humain PO (2026-09-24). **Livré et certifié le 24/09/2026 (5/5 récits DONE_TESTED, 38/38 tests verts, AST ≤ 241L, Vibe-Check 24P/1W/0F)**. Références : ADR-0003, ADR-0312, ADR-0364, ADR-0369, ADR-0370, ADR-0376, ADR-015. Backlog détaillé : [`epics/epic_data_hygiene_and_retention.md`](epics/epic_data_hygiene_and_retention.md).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-230-BE** | - | Storage/SQLite | Moteur de Maintenance & Défragmentation SQLite (`mloop memory vacuum / health`) | `✅ DONE` | `SHIPPED` | ✅ Implémenté & 6/6 tests verts (2026-09-24) |
| [x] | **MLOOP-231-BE** | - | Logging/Rotation | Middleware de Rotation & Archivage Rotatif des Journaux (`events.jsonl`, `traces.json`) | `✅ DONE` | `SHIPPED` | ✅ Implémenté & 8/8 tests verts (2026-09-24) |
| [x] | **MLOOP-232-BE** | - | Crawler/Cache | Gestionnaire de Cycle de Vie & TTL du Cache Crawler (`mloop crawler prune`) | `✅ DONE` | `SHIPPED` | ✅ Implémenté & 7/7 tests verts (2026-09-24) |
| [x] | **MLOOP-233-BE** | - | Session/Scratch | Nettoyage Automatique & Rétention des Artefacts de Session (`memory/scratch/`, checkpoints) | `✅ DONE` | `SHIPPED` | ✅ Implémenté & 9/9 tests verts (2026-09-24) |
| [x] | **MLOOP-234-FULL**| - | QA/VibeCheck | Harnais de Surveillance E2E de la Santé du Stockage & Intégration Vibe-Check | `✅ DONE` | `SHIPPED` | ✅ Implémenté & 3/3 tests verts (2026-09-24) |


---

## Épopée : EPIC-24-SKILLS-EVAL-HARNESS (Harnais Industriel d'Évaluation des Compétences Agentiques) [DONE]

> 🎯 **Origine** : Standardisation sur Google Agents CLI Eval & besoin stratégique d'évaluer objectivement l'intégralité des 39 compétences (.agents/skills/*) et skills Antigravity pour éliminer le Context Rot, la suractivation (trigger pollution) et les dérives comportementales. Références : ADR-0202, ADR-0308, ADR-0348, ADR-0375, ADR-0376, **ADR-0389**. Backlog détaillé : [`epics/epic_skills_eval_harness.md`](epics/epic_skills_eval_harness.md). **Session Grill EPIC-24 VALIDÉE le 24/09/2026 (PO Marco) — 5/5 récits `DONE_TESTED` (27/27 tests verts)** · Système 1 statique · Seuil 80 pts · HITL obligatoire · Check 23 Vibe-Check · Dashboard `/skills-health` HTML statique · CI uniquement.

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-240-BE** | - | Pipelines/SkillsEval | Moteur d'Évaluation Déterministe & Rubrique Sémantique 100 pts pour Compétences | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-24) |
| [x] | **MLOOP-241-BE** | - | Memory/EvalDatasets | Référentiel Golden Datasets d'Évaluation pour les 39 Skills (`memory/evals/skills/`) | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-24) |
| [x] | **MLOOP-242-BE** | - | Pipelines/AutoTuner | Boucle d'Amélioration Fermée (Eval Flywheel) : Couplage Auto-Tuner, Harvester & Anti-Amnésie | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-24) |
| [x] | **MLOOP-243-FE** | - | Dashboard/Skills | Matrice Visuelle & Radar de Santé des Compétences dans le Dashboard mLoop | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-24) |
| [x] | **MLOOP-244-FULL**| - | CLI/VibeCheck | Commande CLI `mloop skill-eval --all` & Contrôle de Vol Pré-Vol Vibe-Check (Check 23) | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-24) |


---

## Épopée : EPIC-25-OPENCODE-ECOSYSTEM-HARNESS (Intégration Avancée & Exploitation des Innovations OpenCode.ai) [DONE]

> 🔭 **Origine** : Veille technologique OpenCode (v1.18.x) — protocole ACP (Agent Client Protocol), architecture serveur/client headless (`opencode serve`), session forking déterministe (`--fork`), sous-agents déclaratifs sous `.opencode/agents/` et outils TypeScript natifs. Références : ADR-0202, ADR-0308, ADR-0375, ADR-0376, ADR-0377. Backlog détaillé : [`epics/epic_opencode_ecosystem_harness.md`](epics/epic_opencode_ecosystem_harness.md). **Session Grill VALIDÉE & 5/5 récits `DONE_TESTED` (27/27 tests verts)** · Parité personas `craftsman`/`subagents` · Outils TS fact_search/vibe_check · Session Forking · Client ACP JSON-RPC · CLI `mloop opencode sync [--dry-run]`.

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-250-BE** | - | Bridges/OpenCode | Parité Miroir Automatique des Personas (`.agents/agents/` → `.opencode/agents/`) | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-25) |
| [x] | **MLOOP-251-BE** | - | Tools/OpenCode | Bridge d'Outils Natifs TypeScript mLoop pour OpenCode (`.opencode/tools/`) | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-25) |
| [x] | **MLOOP-252-BE** | - | Bridges/OpenCode | Intégration du Session Forking dans les Rituels Grill-Me & Doubt-Driven | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-25) |
| [x] | **MLOOP-253-BE** | - | Protocols/ACP | Adaptateur Protocolaire Expérimental OpenCode ACP (JSON-RPC) | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-25) |
| [x] | **MLOOP-254-FULL**| - | CLI/OpenCode | Commandes CLI mLoop d'Orchestration & Validation E2E OpenCode | `✅ DONE` | `SHIPPED` | ✅ Livré & Certifié Gate 4 (2026-09-25) |


---

## Épopée : EPIC-28-ADR-CLEAN-ARCHITECTURE (Assainissement du Générateur d'ADR & Raccordement Dynamique des Blueprints) [DONE]

> 🏛️ **Origine** : Audit d'ingénierie post-veille du 24/09/2026 — `src/pipelines/grill_engine.py` utilise une constante Python en dur (`ADR_TEMPLATE`), ignore le blueprint officiel `standards/blueprints/project_adr_template.md` créé le 16/09/2026, utilise une incrémentation d'ID naïve (`len(existing) + 1`) génératrice de collisions et dépasse le plafond modulaire (440 lignes > 300L, `RULE-AST-01`). Raccordement dynamique, calcul robuste `max(ids) + 1` et modularisation en sous-package `src/pipelines/grill/`. Cadrage Macro-Grill VALIDÉ le 24/09/2026 via ADR-012. **Livré et certifié le 24/09/2026 (4/4 tests verts, AST ≤ 251L)**. Références : ADR-0202, ADR-0320, ADR-0375, ADR-0376, ADR-012. Backlog détaillé : [`epics/epic_adr_clean_architecture.md`](epics/epic_adr_clean_architecture.md).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-280-BE** | - | Pipelines/Grill | Résolution Dynamique du Gabarit `project_adr_template.md` | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — Cascade 3 niveaux |
| [x] | **MLOOP-281-BE** | - | Pipelines/Grill | Calculateur d'ID ADR Robuste par Regex Anti-Collision | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — max(ids)+1 anti-collision |
| [x] | **MLOOP-282-BE** | - | Pipelines/Grill | Scission Modulaire de `grill_engine.py` (Plafond Strict ADR-0202 ≤ 300L) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — Package `grill/` ≤251L + shim |
| [x] | **MLOOP-283-FULL**| - | QA/Certification | Harnais de Tests de Non-Régression & Certification Vibe-Check | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 19/19 tests verts, vibe-check OK |





---

## Épopée : EPIC-29-GRILL-V2-FRONTIER-SKILLS (Modernisation du Grilling mLoop v2 : Rounds, Ungrillables & Context Health) [DONE]

> 🥩 **Origine** : Veille technologique et benchmarking de l'état de l'art (Matt Pocock / AI Hero, Septembre 2026) — formalisation de l'ADR-0389 : hybridation du format d'interrogation (Frontier Rounds de 2 à 4 questions orthogonales en Macro vs 1:1 atomique en Micro), protocole Handoff pour les questions ungrillables (IHM/UX) vers des prototypes jetables (`scratch/prototypes/`), surveillance de la "Dumb Zone" (> 120k tokens) et interdiction absolue de purge de contexte post-grill. Références : ADR-0320, ADR-0375, ADR-0376, ADR-0389, ADR-013. Cadrage Macro-Grill VALIDÉ le 24/09/2026 (ADR-013). Feu vert PO Marco (2026-09-24). **Livré et certifié le 24/09/2026 (26/26 tests verts, AST ≤ 276L, Vibe-Check OK)**. Backlog détaillé : [`epics/epic_grill_v2_frontier_rounds_ungrillable_context.md`](epics/epic_grill_v2_frontier_rounds_ungrillable_context.md).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-290-BE** | - | CLI/Swarm | Câblage CLI Swarm (Options `--mode round/atomic` & Alertes Health) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — Options `--mode` et health check CLI |
| [x] | **MLOOP-291-FE** | - | Frontend/UI | Protocole Handoff & Staging des Prototypes Jetables (`scratch/prototypes/`) | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — Sandbox Handoff HTML5/SVG |
| [x] | **MLOOP-292-DOC**| - | Blueprints/Gates | Alignement des Blueprints Gates (G6/G7) & Protocole de Cadrage Phase 2 | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — Blueprint Gates G6/G7 & protocole v2 |
| [x] | **MLOOP-293-FULL**| - | QA/Certification | Validation E2E sur Cas Réel (Metro FOOD) & Certification Vibe-Check | `✅ DONE` | `SHIPPED` | ✅ Sortie QA (PO) — 26/26 tests verts & vibe-check OK |


---

## Épopée : EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION (Refactorisation de la Machine à États des Récits, Éradication du Hardcoding & Alignement 5 Phases) [DONE]

> ⚙️ **Origine** : Audit contradictoire du 25/09/2026 — élimination de la contradiction `IN_DEV ➔ DONE_TESTED` avant la QA, éradication du hardcoding dans `src/pipelines/state_machine.py` (verticaux clients `FOOD/COMMERCE/SANTE`, TTL dupliqué, arborescence en dur), formalisation de la règle d'or d'immuabilité des récits `DONE` (anomalies ultérieures = nouveau `BUG`/`HOTFIX`) et auto-clôture Gate 5 sans confirmation humaine si tout est vert (`requires_human: False`). Références : ADR-0202, ADR-0375, ADR-0376, ADR-0386, ADR-0391. Backlog détaillé : [`epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md`](epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md). **Session Macro-Grill VALIDÉE le 25/09/2026 (PO Marco)** — 5/5 récits Palier 2 `READY_FOR_DEV` (Rubber Duck PASS ×5, Trust 95-100%, 0 bloquant ; **épopée 5/5 `READY_FOR_DEV`**).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-310-BE** | - | Core/State | Unification du Modèle d'États `StoryStatus` & Rétrocompatibilité Tolérante | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 48/48 tests verts |
| [x] | **MLOOP-311-BE** | - | Pipelines/FSM | Assainissement Anti-Hardcoding de `state_machine.py` (Verticaux, TTL & Arborescence) | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 62/62 tests verts |
| [x] | **MLOOP-312-BE** | - | Pipelines/Lifecycle | Graphe de Transitions Déterministe & Auto-Clôture Gate 5 sans Validation Humaine | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 65/65 tests verts |
| [x] | **MLOOP-313-BE** | - | Pipelines/Sync | Harmonisation Multi-Couches des Consommateurs (`_sync_backlog`, `wikifix`, `scratch_prune`, `Dashboard`) | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 15/15 tests verts |
| [x] | **MLOOP-314-FULL**| - | Standards/QA | Formalisation Normative ADR-0391, Mise à Jour SSOT & Harnais de Certification E2E | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1669/1669 tests verts |

---

## Épopée : EPIC-27-LIFECYCLE-STATE-LOCK (Gouvernance de Concurrence de la Machine à États des Récits) [OPEN]

> 🔐 **Origine** : **Incident réel du 24/09/2026 (session Grill EPIC-21)** — réécriture non autorisée de `sprint_backlog.md` à **13:49:04** basculant `MLOOP-212/213/214/215` en `READY_FOR_DEV` sans aucune session humaine, restaurée à **13:50:18** puis **re-jeuée à 13:54:28** ; mention « struct-check ×4 » sans aucun artefact `struct_check_*` sur disque ; `validate_content_integrity` ne hashant que le corps (`parts[2]`) — un changement de `status:` en frontmatter passe inaperçu, alors même que `STORY_LIFECYCLE_PROTOCOL.md` §4 qualifie l'auto-promotion de « faute grave » **sans aucun garde-fou machine**. Conflit structurel en environnement multi-agents concurrents (workers EPIC-19, autres orchestrators) ; résolution humaine Option A (rétrogradation puis promotion un par un, feu vert traçable). Références : ADR-0375, ADR-0376, ADR-0345 (Zero Zombie — analogie de gouvernance), `STORY_LIFECYCLE_PROTOCOL.md`. Backlog détaillé : [`epics/epic_lifecycle_state_lock.md`](epics/epic_lifecycle_state_lock.md). Récit Palier 2 `READY_FOR_DEV` / `grill_me: DONE` (Rubber Duck `🟢 CONFORME`, feu vert humain 2026-09-24).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **MLOOP-270-BE** | - | Core/Lifecycle | Verrou Anti-Promotion & Journal des Transitions de Statut des Récits | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1777 tests verts · story-backfill exécuté (16 récits) |

---

---

## Épopée : EPIC-26-CLINE-ECOSYSTEM-HARNESS (Intégration Avancée & Exploitation des Innovations Cline : Agent Teams, Memory Bank & Plan/Act) [OPEN]

> 🤖 **Origine** : Veille technologique Cline ([cline.bot](https://cline.bot) / [docs.cline.bot](https://docs.cline.bot)) — coordination d'équipes autonomes via **Agent Teams** (`cline --team-name`) et tableau de tâches partagé, standard de persistance contextuelle **Memory Bank** (`memory-bank/`), séparation étanche **Plan & Act** (`--plan`), et gouvernance par `.clinerules`. Références : ADR-0202, ADR-0346, ADR-0375, ADR-0376, ADR-0377. Backlog détaillé : [`epics/epic_cline_ecosystem_harness.md`](epics/epic_cline_ecosystem_harness.md). Récits Palier 1 `DRAFT` / `grill_me: PENDING`.

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-260-BE** | - | Bridges/Cline | Bridge de Mémoire Bidirectionnel mLoop <-> Cline Memory Bank (`memory-bank/`) | `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-261-BE** | - | Rules/Cline | Génération Automatique de la Parité `.clinerules` depuis `CONSTRAINTS.md` & `AGENTS.md` | `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-262-BE** | - | Workflow/Cline | Intégration du Mode Plan/Act de Cline (`--plan`) avec les Gates de Cycle de Vie mLoop | `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-263-BE** | - | Swarm/Cline | Adaptateur Worker Cline Agent Teams (`--team-name`) pour Swarm Multitâches | `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-264-FULL**| - | CLI/Cline | Commandes CLI `mloop cline-sync` & Harnais de Validation Pré-Vol Vibe-Check | `DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |

---

---

## Épopée : EPIC-30-MULTIMODAL-ARTIFACT-HARNESS (Harnais de Fidélité Visuelle & Intégrité des Artefacts Topologiques) [OPEN]

> 🎨 **Origine** : Étude scientifique de référence **ReFigBench** (*arXiv:2609.18844*, 16/09/2026) — formalisation des garde-fous d'intégrité pour agents multimodaux : barrière déterministe $g(P) \in \{0, 1\}$ anti-collage raster (>80%), prévention de l'effondrement des connecteurs (*Connector Collapse* à 100%) dans Archify (graphe fermé strict), filtre d'ingestion des schémas d'architecture via les légendes (*ORBIT Caption Harvesting*), découplage de la note topologique/sémantique (30% éliminatoire) du rendu cosmétique, et sonde Check 27 dans Vibe-Check. Références : ADR-016, ADR-0392, ADR-0202, ADR-0375, ADR-0376, ADR-0377, ADR-0389. Backlog détaillé : [`epics/epic_multimodal_artifact_harness.md`](epics/epic_multimodal_artifact_harness.md). **Session Macro-Grill VALIDÉE le 25/09/2026 (PO Marco)** — 5 récits en transition Palier 2.

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-300-BE** | - | Gate/Artifacts | Porte Déterministe d'Artefacts & Anti-Raster Paste (`DeterministicArtifactGate`) | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-301-BE** | - | Tools/Archify | Validation Topologique Anti-Effondrement des Connecteurs Archify | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-302-BE** | - | Pipelines/Ingest | Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-303-BE** | - | Pipelines/Audit | Grille d'Audit Architectural Découplée (Structure Sémantique vs Rendu) | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x] | **MLOOP-304-FULL**| - | CLI/VibeCheck | Contrats de Dev Handoff Multi-Harnais & Commande CLI `mloop artifact-check` | `✅ DONE` | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |

---

---

## Épopée : EPIC-32-GRILL-MODALITY-DECOUPLING-AND-STORY-SPAWN-GATING (Découplage Déterministe Modalité de Grill vs Périmètre, Verrou Anti-Cascade & Gating d'Écriture) [OPEN]

> 🥩 **Origine** : **Incident réel du 25/09/2026 (conversation `e375a796`)** — dérive cognitive où l'agent a confondu la demande de format de questions (*« passe en mode macro »*) avec un ordre d'exécution et de promotion industrielle en cascade de 5 récits Palier 2, court-circuitant l'autorité exclusive de Gate 2 (`READY_FOR_DEV`) et risquant la "Dumb Zone" contextuelle (>120k tokens). Découplage strict de la matrice Format (`ATOMIC` vs `ROUND`) $\times$ Scope (`STORY` vs `EPIC`), règle d'arrêt formel post-round et sonde Check 28 dans Vibe-Check. Références : ADR-017, ADR-0393, ADR-0320, ADR-0375, ADR-0376, ADR-0389, ADR-0391, `STORY_LIFECYCLE_PROTOCOL.md`. Backlog détaillé : [`epics/epic_grill_modality_decoupling_anti_cascade.md`](epics/epic_grill_modality_decoupling_anti_cascade.md). **Session Macro-Grill VALIDÉE le 25/09/2026 (PO Marco)** — 5 récits Palier 1 (`DRAFT` / `grill_me: PENDING`).

| État | Récit              | Clé Jira | Composant           | Titre                                                                                                          | Grill-me  | Statut             | Responsable                                |
| :--: | :----------------- | :------: | :------------------ | :------------------------------------------------------------------------------------------------------------- | :-------: | :----------------- | :----------------------------------------- |
| [x]  | **MLOOP-320-BE**   |    -     | Standards/Protocols | Formalisation Normative & Triangulation des Standards (ADR-0393, STORY_LIFECYCLE_PROTOCOL & AGENTS.md)         | `✅ DONE`  | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x]  | **MLOOP-321-BE**   |    -     | Skills/Grill        | Refonte du Skill Grill & Table Anti-Rationalisation (Découplage Atomic/Round vs Story/Epic & Arrêt Post-Round) | `✅ DONE`  | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x]  | **MLOOP-322-BE**   |    -     | Core/FSM            | Garde Mécanique FSM & Verrou Anti-Promotion Directe en `READY_FOR_DEV` dans GrillEngine                        | `✅ DONE`  | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x]  | **MLOOP-323-BE**   |    -     | CLI/VibeCheck       | Contrôle de Gating CLI & Sonde de Détection de Cascade (Check 28 Vibe-Check)                                   | `✅ DONE`  | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |
| [x]  | **MLOOP-324-FULL** |    -     | Tests/Integration   | Harnais de Non-Régression & Suite de Tests Automatisés (Pytest FSM + Grill Engine)                             | `✅ DONE`  | 🟣 `DONE_TESTED` | ✅ Build achevé (2026-09-25) · 1827 tests verts |

---

---

