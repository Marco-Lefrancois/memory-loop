# Sprint Backlog - mLoop

## Règle de responsabilité
> 💡 **Règle de responsabilité** (alignée sur STORY_LIFECYCLE_PROTOCOL.md & ADR-0391) : 
> - `DRAFT` / `OPEN` ➡️ **⚪ Phase 1 : Ingestion & Cadrage** (Ébauche initiale)
> - `IN_ANALYZE` ➡️ **🤖 Phase 2 : Plan & Analyse** (Entrevue Grill-Me 1:1, mono-récit strict)
> - `READY_FOR_GROOMING` ➡️ **🟡 Phase 2 : Prêt pour Revue** (DoR 6/6 certifié par l'IA)
> - `READY_FOR_DEV` ➡️ **👤 Phase 2 : Arbitrage Humain** (Seul l'humain valide le passage en dev)
> - `IN_DEV` ➡️ **🔧 Phase 3 : Build & Dev** (Implémentation physique active)
> - `READY_FOR_QA` ➡️ **🧪 Phase 4 : Prêt pour Validation** (Tests unitaires verts, prêt pour qualification sprint)
> - `QA_CERTIFIED` ➡️ **🟢 Phase 4 : Qualifié QA** (Certification `validate-sprint` et linters 100% PASS)
> - `READY_TO_SHIP` ➡️ **📦 Phase 5 : Prêt pour Clôture** (Bilan pré-vol vierge, prêt pour auto-livraison Gate 5)
> - `DONE` / `SHIPPED` ➡️ **🟣 Phase 5 : Livré & Scellé** (Clôture autonome 0 FAIL, immuabilité absolue)
> *(Rétrocompatibilité : `DONE_TESTED` sanctuarisé comme passerelle historique)*

---

> 📦 **Archives des Sprints Antérieurs** :
> - **EPIC-1 à EPIC-20** (91 récits) : [archive/sprint_backlog_history_q2_q3_2026.md](archive/sprint_backlog_history_q2_q3_2026.md)
> - **Épopées Clôturées Q3-Q4 2026** : [archive/sprint_backlog_history_q3_q4_2026.md](archive/sprint_backlog_history_q3_q4_2026.md)

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

## Épopée : EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE (Traçabilité Bidirectionnelle Code ↔ Exigences, Preuves de Programmation AST & EvidencePack 2.0) [OPEN]

> 🧬 **Origine** : Cadrage formel du 25/09/2026 — liaison déterministe entre chaque bloc de code physique (symboles AST qualifiés) et la règle d'affaires (`RM-XXX`) ou critère Gherkin qui justifie son existence. Élimination complète du "code fantôme" (*Ghost Code*) et de la sur-ingénierie non auditée, tout en préservant la pureté no-code des User Stories Markdown (confinement dans le plan d'implémentation et l'EvidencePack JSON). Références : ADR-0394, ADR-0320, ADR-0326, ADR-0369, ADR-0375, ADR-0376, `ECOSYSTEM_RIGOR_PROTOCOL.md`. Backlog détaillé : [`epics/epic_requirement_to_code_traceability.md`](epics/epic_requirement_to_code_traceability.md). Récits Palier 1 (`status: DRAFT` / `grill_me: PENDING`).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-330-BE** | - | Standards/Blueprints | Normalisation des Gabarits de Traçabilité Code ↔ Exigences & Schéma EvidencePack 2.0 | `✅ DONE` | 🟡 `READY_FOR_QA` | 👤 Pair AI / PO Marco |
| [x] | **MLOOP-331-BE** | - | Core/AST | Moteur d'Extraction AST & Résolution Déterministe des Symboles de Code | `✅ DONE` | 🟡 `READY_FOR_QA` | 👤 Pair AI / PO Marco |
| [ ] | **MLOOP-332-BE** | - | Pipelines/EvidencePack | Pipeline d'Harmonisation Synchrone EvidencePack 2.0 & Archivage des Preuves | `✅ DONE` | 🟢 `READY_FOR_DEV` | 👤 PO Marco (Gate 2 validée le 25/09/2026) |
| [ ] | **MLOOP-333-BE** | - | QA/VibeCheck | Sonde Vibe-Check Check 29 (Intégrité Traçabilité Code ↔ Exigences) & Commande CLI | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-334-FULL**| - | Tests/Traceability | Harnais de Validation Intégrale, Tests de Non-Régression & Parité Documentaire | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---

## Épopée : EPIC-34-WFM-COGNITIVE-WIKI-GRAPH (Mémoire Cognitive mLoop & Moteur Wiki Graph Dual-Layer) [OPEN]

> 🧠 **Origine** : Étude scientifique de rupture **WFM: Wiki Foundation Model for Complex Agentic Reasoning** (*arXiv:2609.18182*, 16/09/2026) — formalisation du standard LLM-Wiki dual-layer $\mathcal{W} = (\mathcal{E}_w, \mathcal{R}_w, \mathcal{D})$ unissant entités discrètes et passages textuels denses, boucle de recherche réflexive à budget borné ($B \le 4$) avec arrêt adaptatif précoce ($f^{(t)} \in \{\text{Continue}, \text{Final}\}$), mode *Reject* souverain interdisant l'extrapolation sans preuve documentaire, et régularisation de variance anti-attention collapse. Références : ADR-0395, ADR-0202, ADR-0375, ADR-0376, ADR-0390. Backlog détaillé : [`epics/epic_wfm_cognitive_wiki_graph.md`](epics/epic_wfm_cognitive_wiki_graph.md). Récits Palier 1 (`status: DRAFT` / `grill_me: PENDING`).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **MLOOP-340-BE** | - | Core/Memory | Schéma Relationnel & Persistance SQLite du Wiki Graph Dual-Layer ($\mathcal{E}_w, \mathcal{R}_w, \mathcal{D}$) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-341-BE** | - | Pipelines/Ingest | Moteur d'Ingestion & Indexation Dual-Space (Passages Denses, Entités Métier & Hyper-Arêtes) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-342-BE** | - | Search/Reflection | Boucle de Fact-Search Réflexif à Budget Borné ($B \le 4$) & Arrêt Anticipé Adaptatif | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-343-BE** | - | QA/Grounding | Mode Reject Souverain Anti-Hallucination & Régularisation de Variance de Scoring | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-344-FULL**| - | CLI/VibeCheck | Commande CLI `mloop wiki-search`, Intégration Grill-Me & Sonde Vibe-Check Check 30 | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---

## Épopée : EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2 (Audit d'Artefacts 5-Axes, Détection d'Inversion Causale & Handoff Multi-Harnais) [OPEN]

> 📐 **Origine** : Étude scientifique de référence **ReFigBench: Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts** (*arXiv:2609.18844*, 16/09/2026) — passage au Rubric Standard 5-Axes ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$), détection mécanique de l'inversion causale silencieuse via comparaison de matrices d'adjacence ($\mathbf{A}_{\text{spec}} \text{ vs } \mathbf{A}_{\text{diag}}$), audit déterministe d'arbre d'objets natifs (anti-effondrement des connecteurs), et adaptation des profils de handoff selon le harnais cible (Claude Code, OpenCode, Codex, Cursor). Références : ADR-0396, ADR-0392, ADR-0202, ADR-0375, ADR-0376, ADR-0377, ADR-0394. Backlog détaillé : [`epics/epic_refigbench_artifact_harness_v2.md`](epics/epic_refigbench_artifact_harness_v2.md). Récits Palier 1 (`status: DRAFT` / `grill_me: PENDING`).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **MLOOP-350-BE** | - | Audit/Objects | Moteur d'Audit Déterministe d'Arbre d'Objets Natifs pour Livrables d'Architecture | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-351-BE** | - | Audit/Scoring | Grille d'Audit Découplée 5-Axes Pénétrante ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-352-BE** | - | Linter/Causality | Linter Matriciel d'Inversion Causale par Comparaison d'Adjacence ($\mathbf{A}_{\text{spec}} \text{ vs } \mathbf{A}_{\text{diag}}$) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-353-BE** | - | Handoff/Harness | Adaptateur de Dev Handoff Multi-Harnais Dédié (Claude Code, OpenCode, Codex & Cursor) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-354-FULL**| - | CLI/VibeCheck | Extension CLI `mloop artifact-check 5x`, Enrichissement Vibe-Check Check 27 & EvidencePack 2.0 | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---

