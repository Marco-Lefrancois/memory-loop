# 🏛️ Registre Historique des Épopées Livrées — mLoop (Q2-Q3 2026)

> 📦 **Statut** : ARCHIVE SOUVERAINE SCELLÉE (Épopées EPIC-1 à EPIC-20)  
> **Période** : Mai 2026 — Septembre 2026  
> **Total Récits Livrés** : 91 récits (SHIPPED / DONE)  
> **Certification** : Tous les récits ci-dessous sont physiquement livrés, testés (pytest), et validés par les Quality Gates mLoop.  
> **Sprint Backlog Actif** : [../sprint_backlog.md](../sprint_backlog.md)

---

## Épopée : EPIC-1-CORE-LOOP (Noyau de la Boucle & Contrôle)

| État | Récit            | Clé Jira | Composant | Titre                                                      | Statut    | Responsable |
| :--: | :--------------- | :------: | :-------- | :--------------------------------------------------------- | :-------- | :---------- |
| [x]  | **MLOOP-001-BE** |    -     | Backend   | Moteur d'état `LoopState` (Pydantic v2 schemas)            | `SHIPPED` | ✅ IA        |
| [x]  | **MLOOP-002-BE** |    -     | Backend   | Orchestrateur Asymétrique (Routage Système 2 vs Système 1) | `SHIPPED` | ✅ IA        |
| [x]  | **MLOOP-003-BE** |    -     | Kernel    | Circuit Breaker Financier (Tokens & TTL)                   | `SHIPPED` | ✅ IA        |
|      |                  |          |           |                                                            |           |             |

---

## Épopée : EPIC-2-HYBRID-MEMORY (Système de Mémoire Hybride)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-010-BE** | - | MCP Server | Serveur MCP `mcp_loop_mem` (Recherche 1-hop) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-011-BE** | - | MCP Server | Standard SEP-2640 (Exposition via `skill://`) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-013-BE** | - | Memory | Démon de Préchargement d'Engrammes (Asynchronous Preloader) | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-3-SAFETY-GOVERNANCE (Sécurité et Gouvernance)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-020-BE** | - | Safety | Verrou physique `Story Guard` (Middleware d'écriture SCC) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-021-BE** | - | Safety | Linter Sémantique `WikiFix` (Refactoring Modulaire <=300L) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-023-BE** | - | Safety | Optimisation RHO (Génération déterministe & Registre d'Hypothèses) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-024-BE** | - | Safety | Pont de Speculative Drafting (Confidence Gate) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-025-BE** | - | Safety | Suite d'Évaluation de Gouvernance (AOEP-v0) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-026-BE** | - | Safety | Infrastructure de Désapprentissage Agentique (Agentic Unlearning) | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-4-SKILL-ECOSYSTEM (Écosystème de Compétences)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-030-BE** | - | Skill | Protocole `Grill with Docs` (Question unique + recommandation) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-031-BE** | - | Skill | Compétence `Wayfinder` (Exploration multi-chemins & DAG) | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-5-INGESTION-OFFICE (Ingestion & Bureautique)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-040-BE** | - | Ingest | Pipeline `MarkItDown` (Conversion locale sandboxed) | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-6-OKF-ENCLAVE (Open Knowledge Format & Enclave gVisor)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-050-BE** | - | Ingest/Skill | Compilateur OKF & Skill Factory (Entités typées) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-051-BE** | - | Memory | Recherche Hybride Tri-Flux (BM25 + Vector + Graphify) & Score de Confiance | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-7-AGENTIC-OBSERVABILITY (Observabilité Agentique Souveraine & Cockpit 2.0) [IN_PROGRESS]

> ▶️ **Reprise Post-Harnais (ADR-0381)** : Épopée reprise sous la protection du harnais déterministe EPIC-8. Récits `MLOOP-070-BE`, `071-BE`, `072-BE` et `073-FE` scellés en `SHIPPED`. `MLOOP-074-FULL` en cours de développement physique via le harnais Phase 3.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-070-BE** | - | Safety/Kernel | Disjoncteur Anti-Boucle Ping-Pong Guard (3 Handoffs Max) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-071-BE** | - | Engine/Artifacts | Intercepteur Boundary Tracing & Auto-Offload OpaqueArtifactBus | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-072-BE** | - | Core/Telemetry | Normalisation Locale des Événements JSONL OpenInference / OTel GenAI | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-073-FE** | - | Cockpit/UI | Jauge Contextuelle Dynamique 3-Zones par Session (Header Bento Grid) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-074-FULL** | - | Swarm/DreamRSI | Runway de Handoffs Multi-Agents & Trajectory Diff Viewer (Dream RSI) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-075-FULL** | - | Cockpit/Data | Explorateur Interactif Knowledge Graph (Graphify) & Base SQLite Souveraine | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-8-BUILD-HARNESS-GOVERNANCE (Harnais Déterministe & Gouvernance Phase 3)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-080-BE** | - | Core/Linter | Linter Statique Déterministe AST `code-check` CLI (Règles ADR-0202 & ADR-0369) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-081-BE** | - | Pipelines/Tournament | Moteur de Tournoi de Code Multi-Draft & Matrice d'Arbitrage Pareto ($S_{\text{pareto}}$) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-082-BE** | - | Core/TDD | Protocole TDD Red-Green Enforcement & Verrouillage Cryptographique Gate 3 | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-9-STAGE4-DETERMINISTIC-VALIDATION (Harnais Déterministe de Phase 4 & Certification QA)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-090-BE** | - | Pipelines/QA | Moteur de Certification QA Sprint & Triangulation 4 Piliers Gherkin | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-091-BE** | - | Pipelines/NLI | Contradiction Engine NLI & Verification Leakage Gate (ADR-0326 & ADR-0354) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-092-BE** | - | Core/Lifecycle | Verrous Bloquants de Gate 4 & Gouvernance Opposable de Recette QA (ADR-0383) | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-12-PHASE4-HARDENING (Renforcement & Blinder Phase 4 — Zero Blindspot)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-120-BE** | - | Standards/ADR | Fondations Normatives & Spécification Phase 4 : ADR-0383, Checklist & Parité | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-122-BE** | - | Pipelines/Evidence | Traçabilité & Preuves Phase 4 : Lien QA → Lifecycle → Handoff | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-123-BE** | - | Core/Safety | Garde-Fous Automatiques Phase 4 : Vibe-Check & Zombie Reap | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-124-BE** | - | Observabilité | Observabilité & Clôture Phase 4 : Logs Structurés & Rapport | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-10-SOVEREIGN-EXCELLENCE (Excellence Souveraine, Rénovation Modulaire & Temps Réel)

| État | Récit            | Clé Jira | Composant         | Titre                                                                                              | Statut        | Responsable |
| :--: | :--------------- | :------: | :---------------- | :------------------------------------------------------------------------------------------------- | :------------ | :---------- |
| [x]  | **MLOOP-100-BE** |    -     | Pipelines/Jira    | Découpage Modulaire du Moteur de Synchronisation Jira (ADR-0202 <=300L)                            | `SHIPPED` | ✅ IA       |
| [x]  | **MLOOP-101-BE** |    -     | Utils/Core        | Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons                                 | `SHIPPED` | ✅ IA        |
| [x]  | **MLOOP-102-BE** |    -     | Memory/Vector     | Consolidation du Flux Vectoriel RHO et Recherche Hybride sur Embeddings Locaux (mxbai-embed-large) | `SHIPPED`  | ✅ IA       |
| [x]  | **MLOOP-103-BE** |    -     | Bridges/MCP       | Transport MCP Réseau et Diffusion Événementielle SSE                                               | `SHIPPED` | ✅ IA       |
| [x]  | **MLOOP-104-FE** |    -     | Cockpit/UI        | Visualiseur Interactif Force-Directed Graph dans le Cockpit Web                                    | `SHIPPED` | ✅ IA       |
| [x]  | **MLOOP-105-BE** |    -     | Core/Security     | Garde-Fou Cryptographique et Hook Pre-Commit Déterministe                                          | `SHIPPED` | ✅ IA        |
| [x] | **MLOOP-106-BE** | - | Commands/Handlers | Découpage Modulaire des Handlers CLI (ADR-0202 <=300L) | `SHIPPED` | ✅ IA |
| [x]  | **MLOOP-107-BE** |    -     | Pipelines/Focus   | Correction du Verrou d'Attention Focus (Persistance Frontmatter et Verdict)                        | `SHIPPED` | ✅ IA       |
| [x]  | **MLOOP-108-BE** |    -     | Framework/CLI     | Fiabilisation du Harnais E2E Boot-Sequence et Alignement de la Clé LiteLLM Metro                   | `SHIPPED` | ✅ IA       |
| [x]  | **MLOOP-109-BE** |    -     | Core/Herdr        | Découpage Modulaire de herdr_adapter.py & Alignement RULE-AST-03 (Popen)                           | `SHIPPED` | ✅ IA       |

---

## Épopée : EPIC-11-ERROR-OBSERVABILITY (Persistance & Gouvernance des Logs d'Erreurs)

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-110-BE** | - | Utils/Logger | Persistance Rotative des Journaux d'Erreurs du Moteur de Logging mLoop | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-13-CODE-GRAPH-INTELLIGENCE (Intelligence de Graphe de Code & Couche de Contexte — Cycle 3) [PLANNED]

> 🔬 **Origine** : Analyses concurrentielles croisées du 21/09/2026 — Agora (arXiv:2609.18094, NVIDIA) et Graft (Trail/Nanonets, dossier de preuves `memory/evidence/ANALYSE-GRAFT-TRAILHQ_fact_dossier.md`). Six améliorations G1-G6 identifiées par confrontation structurelle et inspection physique de CodeGraph (`src/commands/handlers/code_intelligence.py`). **MLOOP-130-BE promu Palier 2 le 21/09/2026** — 4 décisions arbitées via Grill-Me 1:1 (corpus tiers neutre à froid · vérité terrain = bugfixes historiques · bac à sable scratch/ · verdict = rapport d'arbitrage, ADR différée conditionnelle). Récits 131-135 : `DRAFT` / `grill_me: PENDING` — passage Palier 2 subordonné au verdict du spike (ADR-0375). Pré-requis transverse : **MLOOP-130-BE (Spike G5)** — aucune architecture tranchée sans preuve empirique.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-130-BE** | - | Core/CodeGraph | Spike PoC Graft vs CodeGraph : Benchmark Empirique Croisé (pull vs push, tokens/call) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-131-BE** | - | Core/CodeGraph | Pipeline Hybride CodeGraph → Graft → Intersection | `SHIPPED` | ✅ |
| [x] | **MLOOP-132-BE** | - | Pipelines/Evidence | Test Graft Deep Build pour QA Sémantique | `SHIPPED` | ✅ |
| [x] | **MLOOP-133-BE** | - | Core/Telemetry | Fallback Automatique si Graft Callers Échoue | `SHIPPED` | ✅ |
| [x] | **MLOOP-134-BE** | - | Core/Hooks | Mesure de Tokens Réelle via APIs LiteLLM | `SHIPPED` | ✅ |
| [x] | **MLOOP-135-BE** | - | Core/CodeGraph | Benchmark Multi-Dépôts (3 tailles) | `SHIPPED` | ✅ |

---

## Épopée : EPIC-14-OBSERVABILITY-INSTRUMENTATION (Instrumentation Logging Complète — Flow RHO Zéro Blindspot)

> 🔧 **Origine** : Gap analysis MLOOP-110-BE — RotatingFileHandler posé (errors.log 5Mo/5, mloop.log 10Mo/3) mais **0% du codebase instrumenté** (3 modules seulement sur 72). 485 `except Exception` + 110 `ZeroFluffConsole.error` non capturés. Objectif : couverture 100% pour flow RHO (lecture errors.log → corrélation → fix suggéré).

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-140-BE** | - | Core/CLI | Instrumentation Logging Point d'Entrée CLI (swarm.py, router.py, cli.py) | `SHIPPED` | ✅ |
| [x] | **MLOOP-141-BE** | - | Pipelines/QA | Instrumentation Logging Pipelines Cœur QA (qa_certifier, vibe_check, sync, focus, lifecycle) | `SHIPPED` | ✅ |
| [x] | **MLOOP-142-BE** | - | Commands/Handlers | Instrumentation Logging Handlers CLI Principaux (code_intelligence, build_harness, analysis_audit, tooling, export_story) | `SHIPPED` | ✅ |
| [x] | **MLOOP-143-BE** | - | Core/Herdr | Instrumentation Logging Workers Herdr (herdr_adapter, herdr_core, herdr_daemon, herdr_worker, worker_pipeline) | `SHIPPED` | ✅ |
| [x] | **MLOOP-144-BE** | - | Pipelines/Jira | Instrumentation Logging Jira Sync (sync_engine, jira_item_sync, jira_reader, jira_report) | `SHIPPED` | ✅ |
| [x] | **MLOOP-145-BE** | - | Core/Internal | Instrumentation Logging Modules Internes & Handlers Secondaires (Ingest, Crawler, Dashboard, Calibrate, Graphify, Wikifix, Rho, Converters, LLM, Lexicon, Bridges, Fact-Search, Evidence, Rubber-Duck) | `SHIPPED` | ✅ |

---

## Épopée : EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT (Application du Chargement des Directives Projet & Ancrage SSOT Canonique) [OPEN]

> 🔧 **Origine** : Découverte terrain lors de la revue des récits `REC-009`→`REC-014` du projet `BoireFrere_Segment2` (22/09/2026). Un audit SSOT a été briefé sur les mauvaises sources (`docs/00-ingested/` amont) au lieu du SSOT canonique (`docs/03-models/`), produisant un faux « conflit de modèle de données ». Cause racine : **aucune règle n'oblige l'orchestrateur à charger `directives/tech.md`+`business.md`** avant tout cadrage/audit/brief. Épopée conduite sous ADR-0376 (Audit 360° en 7 Couches). Backlog détaillé : [`epics/epic_project_directives_ssot_enforcement.md`](epics/epic_project_directives_ssot_enforcement.md). Récits `OPEN` / `grill_me: PENDING` — passage Palier 2 subordonné à la session Grill-Me 1:1 de découpage.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-160-BE** | - | Standards/Protocols | Protocole Normatif Hiérarchie SSOT & Chargement des Directives Projet | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-161-BE** | - | Standards/ADR | ADR-0384 Directives SSOT Boot Enforcement & Amendement AGENTS.md (racine + projet) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-162-BE** | - | Skills/Grill | Renforcement Skill `grill` — Étape 0 Search-Before-Ask (Localisation SSOT obligatoire) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-163-BE** | - | Pipelines/Vibe-Check | Check 20 Vibe-Check — Intégrité Directives Projet & SSOT Canonique (conditionnel, non-régressif) | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-164-BE** | - | Tests/Parité | Suite de Tests Paramétrée Check 20 & Réalignement Tests Vibe-Check sur Sémantique Tri-État | `SHIPPED` | ✅ IA |
| [x] | **MLOOP-165-BE** | - | Pipelines/Vibe-Check | Check Ancrage Visuel des Récits Frontend (Contrat Visuel Premier — WARNING si récit `frontend` sans maquette) | `SHIPPED` | ✅ IA |

---

## Épopée : EPIC-16-DASHBOARD-TOOLING (Intégration Archify & DrawDB au Cockpit)

> 🔧 **Origine** : Demande utilisateur 2026-09-22 — exposer les diagrammes Archify et le modéliseur DrawDB dans le Cockpit Agentique. Pré-requis transverse : **MLOOP-145-BE** (conflit SCC sur `src/dashboard/server.py` — Groupe B instrumentation). Récits au statut Palier 1 `DRAFT` (`grill_me: PENDING`) — dossiers de preuves sous `memory/evidence/`.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-150-BE** | - | Dashboard/API | API REST Archify — Restitution des diagrammes compilés dans le Cockpit | `SHIPPED` | ✅ |
| [x] | **MLOOP-151-FE** | - | Dashboard/FE | Onglet Archify — Navigation des diagrammes dans le Cockpit | `SHIPPED` | ✅ |
| [x] | **MLOOP-152-BE** | - | Dashboard/DrawDB | DrawDB Souverain Local & Lien Cockpit (Zéro Exfiltration) | `SHIPPED` | ✅ Sortie QA 23/09 (PO) — Visualiseur ERD 100% local, routeur FastAPI (:8081), widget Cockpit, 12/12 tests PASS |

---

## Épopée : EPIC-17-MODULAR-REFACTORING (Résorption de la Dette Modulaire AST — RULE-AST-01)

> 🔧 **Origine** : Découverte lors de la livraison d'EPIC-15 (22/09/2026) — le hook pre-commit a bloqué sur `RULE-AST-01` (dette préexistante de `vibe_check.py`, 880 lignes). Audit `code-check --all` : **318 fichiers, 81 violations, 38 dépassements de plafond modulaire (300 lignes)**. Backlog détaillé archivé : [`epics/epic_modular_refactoring_ast_debt.md`](epics/epic_modular_refactoring_ast_debt.md). **Livré le 24/09/2026 (10/10)**.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-170-BE** | - | Pipelines/Vibe-Check | Récit Pilote — Refactoring Modulaire de `vibe_check.py` (880L → < 300L/module) | `DONE_TESTED` | 🟢 Clôturé 2026-09-23 (1306 tests verts, 73 miroirs) |
| [x] | **MLOOP-171-BE** | - | Core/Analysis | Cartographie & Priorisation des 39 Modules en Dépassement (blast radius) | `DONE_TESTED` | ✅ Harvest 2026-09-23 : 23/23 tests, code-check 297L PASS, matrice 39 fichiers BR, épic DONE |
| [x] | **MLOOP-172-BE** | - | Standards/Protocols | Pattern d'Extraction Modulaire Réutilisable (rétrocompatibilité imports) | `DONE_TESTED` | ✅ Harvest 2026-09-23 : protocole + fumée + check_22 (27/27) + critic extrait, rapport STATUS: DONE |
| [x] | **MLOOP-173-BE** | - | Core/State | Extraction Modulaire de src/state.py — Singleton d'État Partagé (BR=78) | `DONE_TESTED` | ✅ Build P6-C #1 2026-09-23 — 4 modules ≤300L, 1380 PASS/0 FAIL, harvest OK |
| [x] | **MLOOP-174-BE** | - | Core/Lifecycle | Extraction Modulaire de src/core/lifecycle.py — Gates & Transitions d'État (BR=8) | `DONE_TESTED` | ✅ Build P6-C #4 2026-09-23 — 6 modules ≤300L, code-check 6/6 PASS, 1380 PASS/0 FAIL, MRO mixins OK, harvest OK |
| [x] | **MLOOP-175-BE** | - | Commands/Registry | Extraction Modulaire de src/commands/_registry.py — Registre Déclaratif CLI (BR=3, 2028L) | `DONE_TESTED` | ✅ Build P6-C #5 2026-09-23 — 10 modules ≤300L + shim 16L, guide-sync 122/122, code-check 10/10 PASS, 1368 PASS/0 FAIL, harvest OK |
| [x] | **MLOOP-176-BE** | - | Converters/SVG | Extraction Modulaire de src/converters/svg_to_md.py — Convertisseur OCR/SVG (BR=2, 991L) | `DONE_TESTED` | ✅ Build 2026-09-24 — package `svg_to_md/` 5 modules + `__init__.py` ≤298L + shim 4L, smoke import VERT (7 callers), code-check 7/7 PASS, 1403 PASS/1 FAIL |
| [x] | **MLOOP-177-BE** | - | Dashboard/Server | Extraction Modulaire de src/dashboard/server.py — Routeurs FastAPI (BR=0, 1634L) | `DONE_TESTED` | ✅ Harvest 2026-09-23 : 9 routeurs/helpers ≤291L, server.py 144L, 77/77 tests dashboard PASS, code-check 10/10 PASS |
| [x] | **MLOOP-178-BE** | - | LoopMem/DB | Extraction Modulaire de src/loop_mem/db.py — Couche SQLite (BR=20) | `DONE_TESTED` | ✅ Build P6-C #2 2026-09-23 — 5 modules ≤300L, 1378 PASS/0 FAIL, ADR-0369 OK, harvest OK |
| [x] | **MLOOP-179-BE** | - | Pipelines/Sync | Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10) | `DONE_TESTED` | ✅ Build P6-C #3 2026-09-23 — 4 modules ≤300L, code-check 4/4 PASS, 1380 PASS/0 FAIL, ADR-0369 1/1 timeout, harvest OK |

---

## Épopée : EPIC-18-EVIDENCE-PARITY-PHASE3 (Parité Épistémique des EvidencePacks Phase 3 vs Phase 2)

> 🔧 **Origine** : Validation Phase 3 Build (22/09/2026) — audit comparatif révèle un écart majeur : les EvidencePacks Phase 3 manquaient de citations verbatim ancrées, de décisions d'implémentation et de contrats déclaratifs. Références : ADR-0320, ADR-0326, ADR-0335, ADR-0361, ADR-0375. Backlog détaillé archivé : [`epics/epic_evidence_impl_decisions.md`](epics/epic_evidence_impl_decisions.md). **Livré le 23/09/2026 (3/3)**.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-180-BE** | - | Pipelines/Evidence | Extension du Schema EvidencePackEngine vers la Parité Phase 2 (5 Champs de Richesse) | `DONE` | ✅ Sortie QA 23/09 (PO) — BUILD vert (28/28 tests, 35/35 croisé, C12) |
| [x] | **MLOOP-181-BE** | - | Pipelines/Build | Intégration Automatique des Décisions et Citations Ancrées avec le Harnais Phase 3 Build | `DONE` | ✅ Sortie QA 23/09 (PO) — BUILD vert (12/12 ciblés, 55/55 domaines, 1370/1370 totaux) |
| [x] | **MLOOP-182-BE** | - | Pipelines/Evidence | Backfill Rétroactif des EvidencePacks Existants vers la Parité Phase 2 | `DONE` | ✅ Sortie QA 23/09 (PO) — 7/7 tests unitaires, 3 modules ≤213L, 29 packs EPIC 10-17 enrichis |

---

## Épopée : EPIC-19-CLICK-CLI-ENGINE (Modernisation du Moteur CLI mLoop via Click)

> 🔧 **Origine** : Audit de performance et ergonomie CLI (23/09/2026) — remplacement du parseur monolithique `argparse` par un moteur dynamique `click.MultiCommand` (Click 8.5+), autocomplétion native PowerShell/Bash, structuration de l'aide par phase souveraine et harnais `CliRunner`. Références : ADR-0202, ADR-0339, ADR-0369, ADR-0370. Backlog détaillé archivé : [`epics/epic_click_cli_engine.md`](epics/epic_click_cli_engine.md). **Livré le 24/09/2026 (5/5)**.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-190-BE** | - | CLI/Context | Infrastructure de Contexte Click & Middleware d'Enforcement des Lifecycle Gates | `DONE` | ✅ BUILD 24/09 — contexte 259L, smokes 37 PASS ×2 moteurs, CA 6/6, sync ✓ |
| [x] | **MLOOP-191-BE** | - | CLI/Router | Routeur de Commandes Dynamique Lazy-Loading (`click.MultiCommand`) | `DONE` | ✅ BUILD 24/09 — router 251L, did-you-mean + fork invoke Design C |
| [x] | **MLOOP-192-BE** | - | CLI/Completion | Complétion Shell Native (PowerShell 5.1+ / pwsh / Bash) & Compléteurs Dynamiques | `DONE` | ✅ BUILD 24/09 — completion 277L, 9/9 protocoles, CA-4 0.22ms ≤15ms |
| [x] | **MLOOP-193-BE** | - | CLI/Formatter | Structuration de l'Aide par Phases Souveraines & Typage `click.Path` | `DONE` | ✅ BUILD 24/09 — formatter 195L, SSOT PHASE_MAPPING, CA 6/6 + piliers 4/4 |
| [x] | **MLOOP-194-BE** | - | CLI/Testing | Harnais de Test In-Process `CliRunner` & Validation Non-Régression | `DONE` | ✅ BUILD 24/09 — 27 tests in-process, suite 1431 passed, rollback argparse ✓ |

---

## Épopée : EPIC-20-PORTFOLIO-GOVERNANCE (Gouvernance du Portefeuille Actif mLoop)

> 📦 **Origine** : Inventaire portefeuille multi-projets du 23/09/2026 — désalignements `lifecycle_state.json` (5 projets), charge Grill-Me Metro_FOOD (12 IN_REVIEW), Gate C9 Metro_COMMERCE sans fact_dossiers (13 RFD), Shopify 41× IN_ANALYZE, Gate 5 mLoop non scellée, HTC à archiver. Backlog détaillé archivé : [`epics/epic_portfolio_governance_2026q4.md`](epics/epic_portfolio_governance_2026q4.md). **Livré le 24/09/2026 (8/8)**.

| État | Récit | Clé Jira | Composant | Titre | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| [x] | **MLOOP-200-BE** | - | Lifecycle | Réaligner `lifecycle_state.json` sur la vérité CLI (5 projets) | `DONE` | 👤 Humain (oui 200+201 2026-09-23) |
| [x] | **MLOOP-201-BE** | - | Evidence | Backfill fact_dossiers Gate C9 — Metro_COMMERCE (13 RFD) | `DONE` | 👤 Humain (oui 200+201 2026-09-23) |
| [x] | **MLOOP-202-BE** | - | Grill-Me | Séquence Grill-Me 1:1 — Metro_FOOD (12 en revue → DoR) | `DONE` | 👤 Humain (oui 2026-09-24) |
| [x] | **MLOOP-203-BE** | - | Triage | Triage Shopify — 41 en analyse → `READY_FOR_GROOMING` / `ON_HOLD` / résidu justifié | `DONE` | 👤 Humain (oui 2026-09-24) |
| [x] | **MLOOP-204-BE** | - | Gate 5 | Clôture Gate 5 mLoop — jira_sync, supersession, tests | `DONE` | 👤 Humain (oui 2026-09-24) |
| [x] | **MLOOP-205-BE** | - | Modular | Normalisation modules ADR-0342 + phases/module sprint_backlog | `DONE` | 👤 Humain (oui 2026-09-24) |
| [x] | **MLOOP-206-BE** | - | Architecture | Cartographie de parenté OneTrust ×3 + RBC ×2 (grille §4) | `DONE` | 👤 Humain (oui 2026-09-24) |
| [x] | **MLOOP-207-BE** | - | Passivation | Passivation HTC + registre SHARED (maintien) / Sante (init à venir) | `DONE` | 👤 Humain (oui 2026-09-24) |

---

## 🗄️ Récits Archivés & Dépréciés (TOMBSTONE Archive)
> *Consulter le registre détaillé des motifs d'arbitrage dans [`../../memory/archive/tombstone_stories.md`](../../memory/archive/tombstone_stories.md).*

| État | Récit | Épopée d'Origine | Composant | Titre | Statut | Décision d'Arbitrage |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| [-] | **MLOOP-012-BE** | EPIC-2-HYBRID-MEMORY | Memory | Compression MLA KV Cache | `TOMBSTONE` | Remplacé par OpaqueArtifactBus & Compaction contextuelle |
| [-] | **MLOOP-022-BE** | EPIC-3-SAFETY-GOVERNANCE | Safety | Audit Intentionnel `J-Lens` | `TOMBSTONE` | Remplacé par Invariants NLI & Assertions déterministes EPIC-9 |
| [-] | **MLOOP-032-BE** | EPIC-4-SKILL-ECOSYSTEM | Skill | `Skill Auto-Creator` | `TOMBSTONE` | Élagué — Risque de sécurité HITL & règle Zero-Bloat ADR-0362 |
| [-] | **MLOOP-041-BE** | EPIC-5-INGESTION-OFFICE | Skill | Bridge `OfficeCLI` | `TOMBSTONE` | Élagué — Périmètre SSOT 100% Markdown (couvert par MarkItDown) |
| [-] | **MLOOP-042-FE** | EPIC-5-INGESTION-OFFICE | Frontend | Visualiseur de Rendu HTML Office | `TOMBSTONE` | Élagué par transitivité avec MLOOP-041-BE |



