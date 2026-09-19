# 🗺️ Cartographie Exhaustive des Fichiers par Phase & Plan de Test Intégral — Memory Loop (mLoop)

**Statut** : Document de Référence et Plan d'Assurance Qualité Déterministe  
**Normes de Référence** : [ADR-0375](file:///C:/Memory%20Loop/standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md), [ADR-0376](file:///C:/Memory%20Loop/standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md), [ADR-0378](file:///C:/Memory%20Loop/standards/adr-system/0378-phase-1-ingest-and-explore-contract-and-gate-1.md), [ADR-0369](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-standards.md), [ADR-0370](file:///C:/Memory%20Loop/standards/adr-system/0370-cli-pipeline-guide-normative-ssot.md), [PROJECT_LIFECYCLE_STAGES.md](file:///C:/Memory%20Loop/standards/protocols/PROJECT_LIFECYCLE_STAGES.md)  
**Date de Révision** : 18 septembre 2026 (v2.30.0 - Alignement Pragmatique du Cycle)  

---

## 1. Vue d'Ensemble & Architecture Réalignée du Cycle de Vie

### 🧭 Les Piliers Fondateurs du Flux Réel

Suite aux retours opérationnels, le flux de travail réel de **Memory Loop (mLoop)** clarifie trois principes fondamentaux :

1. **Le Préalable Technique Incontournable (`INIT` + `INGEST`)** :  
   Un projet ne peut ni être dimensionné (T-Shirt Size) ni analysé dans le vide. Deux actions préalables sont impératives :
   - **Échafaudage propre** : Création de la structure du projet (`python src/swarm.py init --project <nom>`).
   - **Ingestion de référence** : Dépôt des briefs, PDFs et maquettes dans `reference/` et conversion normalisée vers `docs/00-ingested/` (`python src/swarm.py ingest`).
2. **Le Juste Positionnement du T-Shirt Sizing** :  
   Le T-Shirt Sizing n'est pas une phase isolée en amont de tout. Il s'insère **immédiatement après l'ingestion documentaire et juste avant la rédaction du SOW**. Il extrait la complexité macro de la matière ingérée pour nourrir l'enveloppe budgétaire.
3. **L'Optionnalité du Cadrage Commercial (*Fast-Track Phase 2 - Analyse*)** :  
   Le T-Shirt Sizing et la rédaction de SOW sont **optionnels** (propres aux mandats en avant-projet). Si un projet dispose déjà d'un SOW signé et de spécifications client complètes, il s'initialise et démarre **directement en Phase 2 (PLAN / ANALYSE / GRILL-ME)** sans barrière artificielle.

```mermaid
flowchart TD
    subgraph SOCLE["0. SOCLE TECHNIQUE PRÉALABLE (Obligatoire)"]
        INIT["1. Scaffolding Projet (init)"] --> INGEST["2. Ingestion Matière Première (ingest)"]
    end

    INGEST --> DECISION{"Projet d'Avant-Projet<br>ou Mandat Déjà Cadré ?"}

    subgraph CADRAGE["CADRAGE COMMERCIAL (Optionnel - Avant-Projet)"]
        TSHIRT["T-Shirt Sizing Macro<br>(to-sow --size)"] -->|Gate 0 : Accord Enveloppe| SOW["SOW Contractuel<br>(docs/01-architecture/SOW.md)"]
    end

    DECISION -->|Nouveau Mandat à chiffrer| TSHIRT
    SOW -->|Gate 1 : Signature SOW| P2
    DECISION -->|SOW déjà signé & Specs prêtes (Fast-Track)| P2

    subgraph INGENIERIE["CYCLE D'INGÉNIERIE & DELIVERY"]
        P2["Phase 2 : PLAN / ANALYSE<br>(Grill-Me, Découpage INVEST & 4 Piliers)"]
        P3["Phase 3 : BUILD / DEV<br>(Code, Tests & Workers Herdr)"]
        P4["Phase 4 : VALIDATE / QA<br>(Sentinel, Fact-Check NLI & Evals)"]
        P5["Phase 5 : SHIP & SYNC<br>(Jira Cloud, Git & NotebookLM)"]
        
        P2 -->|Gate 2 : Definition of Ready| P3
        P3 -->|Gate 3 : Definition of Done| P4
        P4 -->|Gate 4 : Conformité Métier| P5
    end
```

---

## 2. Cartographie des Fichiers & Plan de Test par Étape

---

### 🧱 Socle Préalable : INITIALISATION & INGESTION (Prérequis Universel)

> **Objectif** : Mettre en place l'arborescence physique et convertir la matière brute en Source Unique de Vérité (SSOT) Markdown exploitable par les agents. Aucun chiffrage ni analyse fine ne peut exister sans ce socle.

#### A. Fichiers Impliqués

| Catégorie | Fichier / Répertoire dans `C:\Memory Loop\` | Rôle & Responsabilité Déterministe | Fréquence d'Utilisation & Déclencheur |
| :--- | :--- | :--- | :--- |
| **Moteur & Scaffolding** | [`src/commands/handlers/project.py`](file:///C:/Memory%20Loop/src/commands/handlers/project.py) | Commande `init` (création de l'arborescence, `README.md`, `AGENTS.md`, `opencode.json`, `.gitignore`). | **1x par projet** — Initialisation de l'environnement. |
| | [`src/pipelines/ingest.py`](file:///C:/Memory%20Loop/src/pipelines/ingest.py) | Pipeline principal d'ingestion et dispatching multimodal. | **À chaque lot de fichiers** — Conversion de `reference/` vers `docs/00-ingested/`. |
| | [`src/pipelines/ingest_agent.py`](file:///C:/Memory%20Loop/src/pipelines/ingest_agent.py) | Agent cognitif d'analyse documentaire et structuration initiale. | **À chaque session d'ingestion** — Traitement des briefs. |
| | [`src/converters/markpdfdown_converter.py`](file:///C:/Memory%20Loop/src/converters/markpdfdown_converter.py) | Convertisseur PDF/Office vers Markdown déterministe. | **À chaque document source** — Normalisation SSOT. |
| | [`src/converters/csv_engine.py`](file:///C:/Memory%20Loop/src/converters/csv_engine.py) | Normalisation encodage UTF-8 pur (nettoyage BOM/CP1252). | **À chaque CSV** — Validation de schéma tabulaire. |
| **Standards & Blueprints** | [`standards/protocols/PROJECT_CREATION_PROCEDURE.md`](file:///C:/Memory%20Loop/standards/protocols/PROJECT_CREATION_PROCEDURE.md) | Procédure opérationnelle de scaffolding agnostique. | **Référence permanente** — Suivi de l'arborescence type. |
| | [`standards/blueprints/project_readme_template.md`](file:///C:/Memory%20Loop/standards/blueprints/project_readme_template.md) | Gabarit standard du README projet. | **1x par projet** — Déployé lors du `init`. |
| | [`standards/blueprints/project_sprint_backlog_template.md`](file:///C:/Memory%20Loop/standards/blueprints/project_sprint_backlog_template.md) | Gabarit du backlog macroscopique. | **1x par projet** — Structure d'accueil des macro-briques. |
| **Artefacts Projet** | `Projects/<projet>/reference/` | Dépôt de matière première (exclu de Git, interdit de lecture directe). | **Au démarrage** — Dépôt des briefs et maquettes. |
| | `Projects/<projet>/docs/00-ingested/` | Matière normalisée SSOT prête pour le chiffrage ou l'analyse. | **Continue** — Base de travail de tous les agents. |

#### B. Plan de Test du Socle Préalable
* **Critère de Réussite Bloquant** : Le dossier `docs/00-ingested/` contient l'ensemble des documents sources convertis en UTF-8 sans altération sémantique, et l'arborescence standard est 100% conforme.
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_project_init_agnostic.py tests/test_ingest_source_manifest.py tests/test_csv_engine.py -v
  ```

---

### 🔵 Phase 2 : PLAN & ANALYSE (Macro-Planification, Chiffrage & Analyse Fine 1:1)

> **Objectif** : Cœur de l'ingénierie mLoop. Transformer la matière première ingérée en architecture validée, dimensionnement budgétaire (si avant-projet), et récits de backlog prêts pour le dev.  
> *Comprend la sous-étape A (Macro-cadrage & chiffrage optionnels) et la sous-étape B (Micro-analyse fine 1:1).*

#### A. Fichiers Impliqués

| Catégorie | Fichier / Répertoire dans `C:\Memory Loop\` | Rôle & Responsabilité Déterministe | Fréquence d'Utilisation & Déclencheur |
| :--- | :--- | :--- | :--- |
| **Moteur & Pipelines** | [`src/pipelines/grill_engine.py`](file:///C:/Memory%20Loop/src/pipelines/grill_engine.py) | Moteur d'entrevue interactive contradictoire *Grill-with-Docs* (Dualité Macro & Micro). | **Haute fréquence** — Cadrage transverse (`grill-project`) et analyse 1:1 (`grill --story`). |
| | [`src/pipelines/sow_engine.py`](file:///C:/Memory%20Loop/src/pipelines/sow_engine.py) | Compilation du SOW contractuel épuré (ADR-0375). | **Optionnel (1x par mandat)** — Cadrage contractuel et jalons. |
| | [`src/pipelines/ticket_pipeline.py`](file:///C:/Memory%20Loop/src/pipelines/ticket_pipeline.py) | Découpage en récits de cadrage Palier 1 (`story_draft_template.md` en `DRAFT`). | **1x par lot** — Découpage de l'architecture/spec en backlog. |
| | [`src/pipelines/focus.py`](file:///C:/Memory%20Loop/src/pipelines/focus.py) | Verrouillage de l'attention de session sur le récit actif. | **Systématique** — Au début de toute session d'analyse de story. |
| | [`src/pipelines/story_editor.py`](file:///C:/Memory%20Loop/src/pipelines/story_editor.py) | Éditeur AST-déterministe des sections H2 de récits (zéro régression). | **Haute fréquence** — À chaque retouche de critère ou scénario. |
| | [`src/pipelines/multi_draft.py`](file:///C:/Memory%20Loop/src/pipelines/multi_draft.py) | Challenge d'évaluation comparative multi-branches (ADR-0373). | **À la demande** — Arbitrage entre variantes de découpage. |
| | [`src/pipelines/canvas_generator.py`](file:///C:/Memory%20Loop/src/pipelines/canvas_generator.py) & [`drawdb_pipeline.py`](file:///C:/Memory%20Loop/src/pipelines/drawdb_pipeline.py) | Modélisation visuelle 2D Obsidian Canvas et schémas relationnels ERD. | **Régulière** — Synchronisation des flux d'écrans et données. |
| | [`src/core/lifecycle.py`](file:///C:/Memory%20Loop/src/core/lifecycle.py) | Machine à états FSM en 5 phases (`STAGE_2_PLAN_ANALYSE`). | **Systématique** — Contrôle de la Gate 2 (DoR 6/6). |
| | [`src/engine/invest_evaluator.py`](file:///C:/Memory%20Loop/src/engine/invest_evaluator.py) | Évaluateur algorithmique de conformité INVEST. | **À chaque story** — Contrôle de qualité de découpage. |
| **Handlers CLI** | [`src/commands/handlers/architecture.py`](file:///C:/Memory%20Loop/src/commands/handlers/architecture.py) | Commandes `grill`, `grill-project`, `to-tshirt`, `to-sow`, `to-tickets`, `to-spec`. | **Haute fréquence** — Commandes centrales de cadrage et analyse. |
| | [`src/commands/handlers/analysis.py`](file:///C:/Memory%20Loop/src/commands/handlers/analysis.py) | Commandes `drill`, `focus`, `update-story`. | **Haute fréquence** — Pilotage fin de la story. |
| | [`src/commands/handlers/graph_intelligence.py`](file:///C:/Memory%20Loop/src/commands/handlers/graph_intelligence.py) | Commandes `graph-query`, `graph-impact`, `graph-explain`. | **Haute fréquence** — Exploration sémantique par les agents. |
| **Standards & Blueprints** | [`standards/blueprints/story_draft_template.md`](file:///C:/Memory%20Loop/standards/blueprints/story_draft_template.md) | **Gabarit Palier 1** : Récits de cadrage (`status: DRAFT`, zones d'ombre pour Grill-Me). | **À chaque découpage** — Gabarit initial issu de T-Shirt/SOW/Spec. |
| | [`standards/blueprints/story_template.md`](file:///C:/Memory%20Loop/standards/blueprints/story_template.md) | **Gabarit Palier 2** : Gold Standard haute fidélité (4 Piliers Gherkin, UX D-A-F-E, contrats API). | **À chaque story analysée** — Gabarit final pour handoff dev. |
| | [`standards/blueprints/tshirt_size_template.md`](file:///C:/Memory%20Loop/standards/blueprints/tshirt_size_template.md) | Gabarit de dimensionnement macro (Grille Kevin Chamberland 1 000 $/j). | **Optionnel** — Avant-projet / Enveloppe budgétaire. |
| | [`standards/blueprints/sow_evaluation_template.md`](file:///C:/Memory%20Loop/standards/blueprints/sow_evaluation_template.md) | Gabarit contractuel officiel (RACI, jalons, conformité Loi 25). | **Optionnel** — Modèle pour `SOW_<PROJET>.md`. |
| | [`standards/protocols/STORY_AUTHORING_FRAMEWORK.md`](file:///C:/Memory%20Loop/standards/protocols/STORY_AUTHORING_FRAMEWORK.md) | Framework de rédaction bimodal et cycle de maturation en 2 paliers. | **Permanent** — Cadre de rédaction des stories. |
| | [`standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/STORY_LIFECYCLE_PROTOCOL.md) | Hiérarchie d'autorité des statuts (`DRAFT` ➔ `IN_ANALYZE` ➔ `READY_FOR_DEV`). | **Permanent** — Machine à états des récits. |
| | [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md) | Protocole de rigueur et audit 360° en 7 couches (ADR-0376). | **Permanent** — Gouvernance des modifications de mLoop. |
| **Artefacts Projet** | `Projects/<projet>/docs/01-architecture/TSHIRT_SIZE_<PROJET>.md` | Dimensionnement macro et grille budgétaire (Optionnel). | **1x par avant-projet** — Scellé à l'accord d'enveloppe. |
| | `Projects/<projet>/docs/01-architecture/SOW_<PROJET>.md` | Engagement contractuel et jalons (Optionnel). | **1x par mandat d'avant-projet** — Scellé à la signature. |
| | `Projects/<projet>/backlog/stories/<ID>.md` | User Stories au gabarit `DRAFT` puis `story_template.md`. | **Haute fréquence** — Livrable central de l'analyse. |
| | `Projects/<projet>/backlog/sprint_backlog.md` | Tableau de bord agile vivant dédié exclusivement au suivi de sprint. | **Continue** — Suivi d'avancement opérationnel. |
| | `Projects/<projet>/memory/evidence/<ID>_evidence.json` | EvidencePack compilé reliant chaque critère à une preuve dans `docs/`. | **Haute fréquence** — Preuve de vérité terrain. |

#### B. Plan de Test de la Phase 2 (DoR)
* **Critère Bloquant (Gate 2 - Definition of Ready)** :
  - 100% des stories prêtes au dev adoptent `story_template.md` avec leurs 4 Piliers Gherkin rédigés sans omission.
  - Les stories non encore analysées conservent `story_draft_template.md` avec `status: DRAFT` et `grill_me: PENDING`.
  - Zéro pseudo-code applicatif (respect strict de l'herméticité ADR-0319).
  - Validation 100% conforme par `struct-check --strict` et Sentinel.
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_grill_engine.py tests/test_blueprints.py tests/test_project_lifecycle.py tests/test_vibe_check_phase_gate.py -v
  ```
  - 100% des stories disposent de leurs 4 Piliers Gherkin rédigés sans omission.
  - Zéro pseudo-code applicatif (respect strict de l'herméticité ADR-0319).
  - Validation 100% conforme par `struct-check --strict` et Sentinel.
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_grill_engine.py tests/test_archify.py tests/test_canvas_generator.py tests/test_drawdb_bridge.py tests/test_dossier_init.py tests/test_invest_evaluator_and_layout.py tests/test_hypergraph_and_extractor.py tests/test_multi_draft.py -v
  ```

---

### 🟢 Phase 3 : BUILD / DEV (Développement & Workers Herdr)

> **Objectif** : Exécuter le développement applicatif physique et les tests unitaires via des développeurs ou des sous-agents out-of-process isolés (Herdr).

#### A. Fichiers Impliqués

| Catégorie | Fichier / Répertoire dans `C:\Memory Loop\` | Rôle & Responsabilité Déterministe | Fréquence d'Utilisation & Déclencheur |
| :--- | :--- | :--- | :--- |
| **Moteur & Pipelines** | [`src/pipelines/worker_pipeline.py`](file:///C:/Memory%20Loop/src/pipelines/worker_pipeline.py) | Gestionnaire de cycle de vie des workers Herdr isolés. | **À chaque tâche de worker** — Exécution out-of-process. |
| | [`src/pipelines/handoff.py`](file:///C:/Memory%20Loop/src/pipelines/handoff.py) | Packaging du contexte pour développeur humain ou agent aval (*Universal Dev Handoff*). | **1x par story prête** — Handoff sans friction. |
| | [`src/core/herdr_adapter.py`](file:///C:/Memory%20Loop/src/core/herdr_adapter.py) | Multiplexeur PTY Herdr et capture de traces de terminal. | **À chaque tâche lourde** — Isolation en Clean Slate. |
| | [`src/core/worker_signal.py`](file:///C:/Memory%20Loop/src/core/worker_signal.py) | Détection de blocages (stalls), timeouts et signaux inter-processus. | **Continue (Runtime)** — Surveillance de santé des workers. |
| | [`src/pipelines/evidence_pack.py`](file:///C:/Memory%20Loop/src/pipelines/evidence_pack.py) | Moissonnage des preuves d'exécution et tests unitaires. | **Haute fréquence** — Mise à jour des preuves réelles. |
| **Handlers CLI** | [`src/commands/handlers/worker.py`](file:///C:/Memory%20Loop/src/commands/handlers/worker.py) | Commandes `worker-spawn`, `worker-status`, `worker-harvest`, `worker-close`, `worker-reap`. | **Haute fréquence** — Pilotage opérationnel des sous-agents. |
| | [`src/commands/handlers/plannotator.py`](file:///C:/Memory%20Loop/src/commands/handlers/plannotator.py) | Commandes `review` et `annotate` (revue interactive visuelle de PR/diff). | **À chaque PR/Diff** — Revue de code par l'humain. |
| | [`src/commands/handlers/code_intelligence.py`](file:///C:/Memory%20Loop/src/commands/handlers/code_intelligence.py) | Commandes `code-explore`, `code-impact` (Blast Radius), `code-affected`. | **Régulière** — Analyse d'impact des modifications de code. |
| **Standards & Blueprints** | [`standards/blueprints/handoff_tripartite_template.md`](file:///C:/Memory%20Loop/standards/blueprints/handoff_tripartite_template.md) | Modèle de protocole d'alignement Tripartite (Archi, Dev, QA). | **1x par story** — Alignement avant codage. |
| | [`standards/adr-system/0346-herdr-dual-track-subagent-multiplexing.md`](file:///C:/Memory%20Loop/standards/adr-system/0346-herdr-dual-track-subagent-multiplexing.md) | Doctrine Dual-Track : Skills in-process vs Workers out-of-process. | **Permanent** — Isolation des tâches lourdes. |
| **Outils** | [`plannotator/`](file:///C:/Memory%20Loop/plannotator/) | Moteur applicatif autonome de revue de code visuelle. | **À chaque revue** — Interface interactive locale. |

#### B. Plan de Test de la Phase 3 (DoD)
* **Critère Bloquant (Gate 3 - Definition of Done)** :
  - 100% des tests unitaires et d'intégration applicatifs sont au vert.
  - Zéro processus orphelin Herdr en arrière-plan (purge validée par `worker-reap`).
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_herdr_adapter.py tests/test_specialized_workers.py tests/test_worker_harvest_partial.py tests/test_worker_spawn_lifecycle_gating.py tests/test_plannotator.py tests/test_evidence_pack.py -v
  ```

---

### 🟣 Phase 4 : VALIDATE / QA (Validation Sémantique & Fact-Check)

> **Objectif** : Contre-audit contradictoire Sentinel, certification de véracité factuelle par inférence NLI (zéro hallucination), détection des fuites tautologiques et exécution des Runnable Gates.

#### A. Fichiers Impliqués

| Catégorie | Fichier / Répertoire dans `C:\Memory Loop\` | Rôle & Responsabilité Déterministe | Fréquence d'Utilisation & Déclencheur |
| :--- | :--- | :--- | :--- |
| **Moteur & Pipelines** | [`src/pipelines/vibe_check.py`](file:///C:/Memory%20Loop/src/pipelines/vibe_check.py) | Guardrail pré-vol de session (17 contrôles déterministes stricts). | **Systématique** — Au boot de chaque session et pre-commit Git. |
| | [`src/pipelines/struct_checker.py`](file:///C:/Memory%20Loop/src/pipelines/struct_checker.py) | Gatekeeper structurel Read-Only : audit des violations C1 à C7. | **Haute fréquence** — Contrôle de template avant Sentinel. |
| | [`src/pipelines/rubber_duck.py`](file:///C:/Memory%20Loop/src/pipelines/rubber_duck.py) | Agent Sentinel : contre-audit sémantique contradictoire (Avocat du Diable). | **Haute fréquence** — Revue contradictoire de chaque récit. |
| | [`src/pipelines/wikifix.py`](file:///C:/Memory%20Loop/src/pipelines/wikifix.py) | Audit de cohérence globale des liens, modèles, références et wikilinks. | **Régulière** — À chaque synchronisation de projet. |
| | [`src/engine/fact_check/`](file:///C:/Memory%20Loop/src/engine/fact_check/) | Moteur d'inférence en langage naturel (NLI) pour certifier les faits énoncés. | **Haute fréquence** — Certification avant clôture de story. |
| | [`src/engine/fact_search/`](file:///C:/Memory%20Loop/src/engine/fact_search/) | Indexation SQLite FTS5 haute précision avec pondération trifusion. | **Continue** — Recherche documentaire haute précision. |
| | [`src/core/gates.py`](file:///C:/Memory%20Loop/src/core/gates.py) & [`completion_gate.py`](file:///C:/Memory%20Loop/src/pipelines/completion_gate.py) | Exécution des portails d'acceptation déterministes (*Runnable Gates*). | **Systématique** — À chaque passage de porte. |
| **Handlers CLI** | [`src/commands/handlers/fact_check.py`](file:///C:/Memory%20Loop/src/commands/handlers/fact_check.py) | Commande `fact-check` (émission des certificats de véracité factuelle NLI). | **Haute fréquence** — Contrôle de véracité par story. |
| | [`src/commands/handlers/analysis.py`](file:///C:/Memory%20Loop/src/commands/handlers/analysis.py) | Commandes `struct-check`, `rubber-duck`, `wikifix`, `check-leakage`. | **Haute fréquence** — Contrôles qualité au fil de l'eau. |
| | [`src/commands/handlers/project.py`](file:///C:/Memory%20Loop/src/commands/handlers/project.py) | Commande `gate-approve --gate 4`. | **1x par fin de sprint** — Validation formelle QA Lead. |
| **Standards & Blueprints** | [`standards/adr-system/0310-vibe-code-common-sense-guardrails.md`](file:///C:/Memory%20Loop/standards/adr-system/0310-vibe-code-common-sense-guardrails.md) | Spécification des 17 contrôles pré-vol de sécurité. | **Systématique** — Barrière de sécurité inviolable. |
| | [`standards/adr-system/0341-runnable-gates-acceptance-portals.md`](file:///C:/Memory%20Loop/standards/adr-system/0341-runnable-gates-acceptance-portals.md) | Standard des portails d'acceptation exécutables. | **Permanent** — Contrat des Runnable Gates. |
| | [`standards/adr-system/0354-specification-leakage-tautology-detection.md`](file:///C:/Memory%20Loop/standards/adr-system/0354-specification-leakage-tautology-detection.md) | Détection de fuites de spécification et critères tautologiques. | **À chaque audit** — Anti-tautologie. |
| **Artefacts Projet** | `Projects/<projet>/memory/wikifix_report.md` | Rapport détaillé d'audit sémantique et intégrité des liens. | **À chaque wikifix** — Bilan de santé projet. |
| | `Projects/<projet>/memory/evidence/<STORY_ID>_fact_dossier.md` | Dossier de preuves certifié par Fact-Check NLI. | **Haute fréquence** — Certificat NLI produit. |

#### B. Plan de Test de la Phase 4 (Recette Métier)
* **Critère Bloquant (Gate 4)** :
  - Certificat de véracité NLI positif émis pour chaque story (zéro hallucination).
  - Rapport WikiFix sans aucun lien mort ni incohérence.
  - Zéro violation bloquante signalée par Sentinel.
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_struct_checker.py tests/test_rubber_duck_api_routes.py tests/test_fact_check_engine.py tests/test_fact_search_engine.py tests/test_nli_polarity.py tests/test_verification_leakage_gate.py tests/test_gates_engine.py tests/test_vibe_check_lifecycle.py -v
  ```

---

### 🔴 Phase 5 : SHIP & SYNC (Synchronisation, Jira Cloud & Clôture)

> **Objectif** : Synchronisation tripartite sécurisée (Fail-Closed) vers Jira Cloud, publication Git versionnée, mise à jour du bundle Google NotebookLM officiel et scellage de cycle.

#### A. Fichiers Impliqués

| Catégorie | Fichier / Répertoire dans `C:\Memory Loop\` | Rôle & Responsabilité Déterministe | Fréquence d'Utilisation & Déclencheur |
| :--- | :--- | :--- | :--- |
| **Moteur & Pipelines** | [`src/pipelines/sync.py`](file:///C:/Memory%20Loop/src/pipelines/sync.py) | Synchronisation sémantique locale : mise à jour WikiFix + réindexation Hypergraphe. | **Régulière** — Fin de cycle ou de sprint. |
| | [`src/pipelines/jira/jira_sync.py`](file:///C:/Memory%20Loop/src/pipelines/jira/jira_sync.py) | Moteur de synchronisation bidirectionnelle Jira Cloud (Fail-Closed, dry-run par défaut). | **À chaque déploiement Jira** — Synchronisation contrôlée. |
| | [`src/pipelines/jira/jira_client.py`](file:///C:/Memory%20Loop/src/pipelines/jira/jira_client.py) | Client HTTP robuste Jira REST API v3 avec gestion des tokens et rate-limits. | **Sur requête Jira** — Couche de transport réseau sécurisée. |
| | [`src/pipelines/notebooklm_export.py`](file:///C:/Memory%20Loop/src/pipelines/notebooklm_export.py) | Exportateur du bundle documentaire SSOT vers le carnet Google NotebookLM officiel. | **Périodique** — À chaque jalon documentaire majeur. |
| | [`src/pipelines/cycle_runner.py`](file:///C:/Memory%20Loop/src/pipelines/cycle_runner.py) | Clôture de cycle et transition d'état globale. | **1x par clôture de sprint** — Scellage de cycle. |
| **Handlers CLI** | [`src/commands/handlers/project.py`](file:///C:/Memory%20Loop/src/commands/handlers/project.py) | Commandes `jira_sync`, `sync`, `cycle-status`. | **En fin de sprint** — Synchronisations officielles. |
| | [`src/commands/handlers/notebooklm.py`](file:///C:/Memory%20Loop/src/commands/handlers/notebooklm.py) | Commande `notebooklm` (authentification, export et mise à jour de carnets). | **À la demande** — Mise à jour de l'Oracle documentaire. |
| | [`src/commands/handlers/tooling.py`](file:///C:/Memory%20Loop/src/commands/handlers/tooling.py) | Commandes `install-hooks`. | **Ponctuelle** — Déploiement des protections Git. |
| **Standards & Blueprints** | [`standards/blueprints/git_pre_commit_hook.sh`](file:///C:/Memory%20Loop/standards/blueprints/git_pre_commit_hook.sh) | Script shell de protection Git pré-commit (vibe-check automatique). | **À chaque git commit** — Exécution automatique en arrière-plan. |
| | [`standards/adr-system/0360-google-notebooklm-rag-gemini.md`](file:///C:/Memory%20Loop/standards/adr-system/0360-google-notebooklm-rag-gemini.md) | Standard de RAG Gemini 2.5 sans hallucination via NotebookLM. | **Permanent** — Doctrine de consultation externe. |
| | [`standards/adr-system/0361-jira-cloud-safe-sync-fail-closed.md`](file:///C:/Memory%20Loop/standards/adr-system/0361-jira-cloud-safe-sync-fail-closed.md) | Protocole de synchronisation Fail-Closed, isolation par portée et dry-run obligatoire. | **Permanent** — Règle bloquante de sécurité d'écriture Jira. |
| **Outils** | [`tools/jira/`](file:///C:/Memory%20Loop/tools/jira/) | Boîte à outils et scripts de diagnostic de connexion Jira Cloud. | **En maintenance Jira** — Diagnostic des jetons et champs ADF. |
| | [`tools/notebooklm/login_notebooklm.mjs`](file:///C:/Memory%20Loop/tools/notebooklm/login_notebooklm.mjs) | Script Node/Playwright pour l'authentification interactive SSO Google NotebookLM. | **Périodique (expiration SSO)** — Renouvellement des cookies Google. |
| **Artefacts Projet** | Dépôt Git versionné | Commits propres avec hook de contrôle au vert. | **À chaque livraison** — Historique Git scellé. |
| | Tickets Jira Cloud synchronisés | Tickets mis à jour avec critères 4 Piliers et statut résolu/fermé. | **À chaque sync Jira** — Miroir distant officiel. |

#### B. Plan de Test de la Phase 5 (Clôture)
* **Critère Bloquant (Gate 5)** :
  - `jira_sync` exécuté sans violation de garde Fail-Closed.
  - Index FTS5 et hypergraphe sémantique synchronisés sans divergence.
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_jira_sync_safe.py tests/test_jira_md_cleaner.py tests/test_sync_resilience.py tests/test_in_review_lifecycle.py tests/test_memory_supersession.py -v
  ```

---

### ⚙️ Couche Transverse & Runtime (Invoquée à Travers Toutes les Phases)

#### A. Fichiers Impliqués

| Catégorie | Fichier / Répertoire dans `C:\Memory Loop\` | Rôle & Responsabilité Déterministe | Fréquence d'Utilisation & Déclencheur |
| :--- | :--- | :--- | :--- |
| **Séquence d'Amorçage (Boot Sequence)** | [`src/pipelines/session_resume.py`](file:///C:/Memory%20Loop/src/pipelines/session_resume.py) | Restauration anti-amnésie de l'historique et des décisions passées (Commande 1). | **Systématique (Boot)** — À tout premier tour de parole d'une session. |
| | [`src/pipelines/vibe_check.py`](file:///C:/Memory%20Loop/src/pipelines/vibe_check.py) | Contrôle pré-vol de sécurité obligatoire en 17 points (Commande 2). | **Systématique (Boot & Commit)** — Pré-vol session et hooks Git. |
| | [`src/pipelines/focus.py`](file:///C:/Memory%20Loop/src/pipelines/focus.py) | Verrouillage d'attention sur le récit cible en Phase ≥ 2 (Commande 3). | **Systématique (Boot)** — Dès qu'un récit actif est ciblé. |
| **Point d'Entrée & Registre** | [`src/swarm.py`](file:///C:/Memory%20Loop/src/swarm.py) | Méta-orchestrateur CLI principal (`python src/swarm.py <cmd>`). | **Systématique** — Invoqué pour 100% des commandes CLI. |
| | [`src/cli.py`](file:///C:/Memory%20Loop/src/cli.py) | Parseur d'arguments CLI standardisé. | **Systématique** — Parseur universel des drapeaux CLI. |
| | [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py) | Registre central normatif des 113 commandes CLI avec leurs métadonnées. | **Systématique** — Découverte et validation des arguments CLI. |
| | [`src/commands/router.py`](file:///C:/Memory%20Loop/src/commands/router.py) | Routeur dynamique et dispatch déterministe vers les handlers. | **Systématique** — Dispatch d'exécution vers le bon handler. |
| | [`src/state.py`](file:///C:/Memory%20Loop/src/state.py) | Gestionnaire de persistance d'état global du système. | **Continue (Runtime)** — Sauvegarde des instantanés de session. |
| **Supervision & Observabilité** | [`src/dashboard/`](file:///C:/Memory%20Loop/src/dashboard/) | Serveur Web FastAPI / SSE temps réel pour la supervision locale Zero-Docker. | **À la demande** — Lancement du dashboard web local. |
| | [`src/commands/handlers/dashboard.py`](file:///C:/Memory%20Loop/src/commands/handlers/dashboard.py) | Commande `dashboard`. | **À la demande** — Invocation CLI du dashboard. |
| | [`src/commands/handlers/tooling.py`](file:///C:/Memory%20Loop/src/commands/handlers/tooling.py) | Commandes `token-tracker`, `context-watch`. | **Régulière** — Audit de coûts et fenêtre de contexte. |
| | [`tools/budget/`](file:///C:/Memory%20Loop/tools/budget/) | Outil de suivi des coûts et crédits LiteLLM. | **Régulière** — Vérification du solde Nmédia Cloud. |
| **Mémoire, Hygiène & Consolidation** | [`src/pipelines/dream_consolidator.py`](file:///C:/Memory%20Loop/src/pipelines/dream_consolidator.py) | Algorithme Sleep-Wake de compression de mémoire nocturne. | **Périodique (Quotidien/Nuit)** — Consolidation mémorielle. |
| | [`src/pipelines/dreamer.py`](file:///C:/Memory%20Loop/src/pipelines/dreamer.py) | Moteur d'entraînement et de rêve mémoriel. | **Périodique** — Entraînement de représentations. |
| | [`src/pipelines/dream_rsi/`](file:///C:/Memory%20Loop/src/pipelines/dream_rsi/) | Méta-optimisation de politique par simulation hors-ligne. | **Périodique** — Optimisation de politique de décision. |
| | [`src/pipelines/memory_hygiene.py`](file:///C:/Memory%20Loop/src/pipelines/memory_hygiene.py) | Balayage de confiance de la mémoire de travail et élimination des hallucinations. | **À chaque compaction** — Nettoyage de contexte. |
| | [`src/pipelines/unlearn.py`](file:///C:/Memory%20Loop/src/pipelines/unlearn.py) | Désapprentissage ciblé d'un concept erroné ou obsolète. | **Sur correction** — Purge d'un fait obsolète du graphe. |
| | [`src/pipelines/teach_pipeline.py`](file:///C:/Memory%20Loop/src/pipelines/teach_pipeline.py) | Auto-apprentissage déterministe à partir des succès validés. | **Après succès** — Formalisation d'une nouvelle connaissance. |
| **Gouvernance des Compétences** | [`src/pipelines/skill_doctor.py`](file:///C:/Memory%20Loop/src/pipelines/skill_doctor.py) | Diagnostic de santé des compétences sous `.agents/skills/` (ADR-0348). | **Hebdomadaire / Audit** — Détection de Context Rot. |
| | [`src/pipelines/skill_auto_tuner.py`](file:///C:/Memory%20Loop/src/pipelines/skill_auto_tuner.py) | Réglage dynamique des hyperparamètres des compétences. | **À la demande** — Auto-calibrage des paramètres. |
| | [`src/core/skill_registry.py`](file:///C:/Memory%20Loop/src/core/skill_registry.py) | Registre de compétences avec support du protocole `skill://`. | **Systématique** — Résolution des invocations de skills. |
| | [`src/core/skill_impact_tracker.py`](file:///C:/Memory%20Loop/src/core/skill_impact_tracker.py) | Suivi de rentabilité et impact des compétences invoquées. | **Continue** — Suivi du ROI en jetons de chaque skill. |
| **Résilience & Cyber-Posture** | [`src/pipelines/agent_resilience.py`](file:///C:/Memory%20Loop/src/pipelines/agent_resilience.py) | Audit de la posture de cyber-résilience agentique (ADR-0371). | **Périodique** — Calcul du score de cyber-résilience. |
| | [`src/pipelines/blast_radius.py`](file:///C:/Memory%20Loop/src/pipelines/blast_radius.py) | Calcul du rayon d'impact conceptuel, architectural et fichier. | **À chaque modification** — Détection de dépendances impactées. |
| | [`src/core/hooks.py`](file:///C:/Memory%20Loop/src/core/hooks.py) | Gestionnaire de hooks de cycle de vie et pré-compaction (ADR-0364). | **Systématique** — Déclenché avant compaction LLM. |
| | [`src/agents/circuit_breaker.py`](file:///C:/Memory%20Loop/src/agents/circuit_breaker.py) | Coupe-circuit de sécurité empêchant les boucles infinies de requêtes. | **Continue (Runtime)** — Interception des cascades d'erreurs. |
| | [`src/agents/orchestrator.py`](file:///C:/Memory%20Loop/src/agents/orchestrator.py) | Orchestrateur central de swarm d'agents cognitifs. | **Continue (Runtime)** — Dispatch cognitif Système 1 / Système 2. |
| | [`src/pipelines/rho_optimizer.py`](file:///C:/Memory%20Loop/src/pipelines/rho_optimizer.py) | Optimisation RHO et génération de règles heuristiques persistées (`rho_rules.yaml`). | **Sur incident résolu** — Persistance d'une règle RHO. |

#### B. Plan de Test de la Couche Transverse
* **Critères Bloquants** :
  - Parité SSOT à 100% entre le code Python `src/commands/_registry.py` et le guide `CLI_PIPELINE_GUIDE.md`.
  - Bilan `SESSION_MEMORY_HEALTH.md` sous la barre stricte des 200 lignes et 25 Ko.
* **Commandes de Test** :
  ```bash
  uv run pytest tests/test_guide_parity.py tests/test_python_senior_standards.py tests/test_state.py tests/test_lifecycle_persistence.py tests/test_circuit_breaker.py tests/test_agent_resilience.py tests/test_token_ledger.py tests/test_skill_doctor.py tests/test_dashboard_v2.py -v
  ```

---

## 3. Matrice Récapitulative Globale d'Exécution des Tests

| Phase / Étape | Commande Pytest Ciblée | Nombre de Suites | Fréquence d'Exécution Idéale | Critère de Succès Bloquant |
| :---: | :--- | :---: | :--- | :--- |
| **Socle Init & Ingest** | `uv run pytest tests/test_project_init_agnostic.py tests/test_ingest_source_manifest.py tests/test_csv_engine.py` | 3 fichiers | À chaque création / ingestion de projet | Encodage UTF-8 pur et arborescence standardisée prête. |
| **Cadrage Commercial (Optionnel)** | `uv run pytest tests/test_sow_pipeline.py tests/test_vibe_check_sow_granularity.py` | 2 fichiers | Uniquement si mandat d'avant-projet | Zéro story détaillée avant la signature du SOW. |
| **Phase 2 : PLAN / ANALYSE** | `uv run pytest tests/test_grill_engine.py tests/test_archify.py tests/test_canvas_generator.py tests/test_drawdb_bridge.py tests/test_dossier_init.py tests/test_invest_evaluator_and_layout.py tests/test_hypergraph_and_extractor.py tests/test_multi_draft.py` | 16 fichiers | À chaque story rédigée / modifiée | Definition of Ready (DoR) validée, 4 Piliers Gherkin stricts, zéro pseudo-code. |
| **Phase 3 : BUILD / DEV** | `uv run pytest tests/test_herdr_adapter.py tests/test_specialized_workers.py tests/test_worker_harvest_partial.py tests/test_worker_spawn_lifecycle_gating.py tests/test_plannotator.py tests/test_evidence_pack.py` | 8 fichiers | À chaque exécution de worker Herdr | Isolation stricte des sessions Herdr et zéro modification directe de code client. |
| **Phase 4 : VALIDATE / QA** | `uv run pytest tests/test_struct_checker.py tests/test_rubber_duck_api_routes.py tests/test_fact_check_engine.py tests/test_fact_search_engine.py tests/test_nli_polarity.py tests/test_verification_leakage_gate.py tests/test_gates_engine.py tests/test_vibe_check_lifecycle.py` | 23 fichiers | À chaque recette / audit de story | Certificat de véracité NLI émis, zéro lien mort WikiFix, 17/17 vibe-check. |
| **Phase 5 : SHIP & SYNC** | `uv run pytest tests/test_jira_sync_safe.py tests/test_jira_md_cleaner.py tests/test_sync_resilience.py tests/test_in_review_lifecycle.py tests/test_memory_supersession.py` | 7 fichiers | À chaque synchronisation / release | Jira synchronisé en Fail-Closed, Git versionné et carnet NotebookLM à jour. |
| **Transverse & Runtime** | `uv run pytest tests/test_guide_parity.py tests/test_python_senior_standards.py tests/test_state.py tests/test_lifecycle_persistence.py tests/test_circuit_breaker.py tests/test_agent_resilience.py tests/test_token_ledger.py tests/test_skill_doctor.py tests/test_dashboard_v2.py` | 20+ fichiers | À chaque session / commit / CI | Parité SSOT 100%, standards Senior respectés, intégrité mémoire préservée. |
