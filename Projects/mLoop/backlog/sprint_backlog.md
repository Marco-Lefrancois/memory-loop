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

## Épopée : EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE (Traçabilité Bidirectionnelle Code ↔ Exigences, Preuves de Programmation AST & EvidencePack 2.0) [OPEN]

> 🧬 **Origine** : Cadrage formel du 25/09/2026 — liaison déterministe entre chaque bloc de code physique (symboles AST qualifiés) et la règle d'affaires (`RM-XXX`) ou critère Gherkin qui justifie son existence. Élimination complète du "code fantôme" (*Ghost Code*) et de la sur-ingénierie non auditée, tout en préservant la pureté no-code des User Stories Markdown (confinement dans le plan d'implémentation et l'EvidencePack JSON). Références : ADR-0394, ADR-0320, ADR-0326, ADR-0369, ADR-0375, ADR-0376, `ECOSYSTEM_RIGOR_PROTOCOL.md`. Backlog détaillé : [`epics/epic_requirement_to_code_traceability.md`](epics/epic_requirement_to_code_traceability.md). Récits Palier 1 (`status: DRAFT` / `grill_me: PENDING`).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-330-BE** | - | Standards/Blueprints | Normalisation des Gabarits de Traçabilité Code ↔ Exigences & Schéma EvidencePack 2.0 | `✅ DONE` | 🟡 `READY_FOR_QA` | ✅ Sentinel PASS (2026-09-25) · Trust 83.2 |
| [x] | **MLOOP-331-BE** | - | Core/AST | Moteur d'Extraction AST & Résolution Déterministe des Symboles de Code | `✅ DONE` | 🟡 `READY_FOR_QA` | ✅ Sentinel PASS (2026-09-25) · Trust 83.2 |
| [ ] | **MLOOP-332-BE** | - | Pipelines/EvidencePack | Pipeline d'Harmonisation Synchrone EvidencePack 2.0 & Archivage des Preuves | `✅ DONE` | 🟡 `READY_FOR_QA` | 👤 PO Marco (Gate 2 validée le 25/09/2026) |
| [ ] | **MLOOP-333-BE** | - | QA/VibeCheck | Sonde Vibe-Check Check 29 (Intégrité Traçabilité Code ↔ Exigences) & Commande CLI | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-334-FULL**| - | Tests/Traceability | Harnais de Validation Intégrale, Tests de Non-Régression & Parité Documentaire | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---

## Épopée : EPIC-34-WFM-COGNITIVE-WIKI-GRAPH (Mémoire Cognitive mLoop & Moteur Wiki Graph Dual-Layer) [OPEN]

> 🧠 **Origine** : Étude scientifique de rupture **WFM: Wiki Foundation Model for Complex Agentic Reasoning** (*arXiv:2609.18182*, 16/09/2026) — formalisation du standard LLM-Wiki dual-layer $\mathcal{W} = (\mathcal{E}_w, \mathcal{R}_w, \mathcal{D})$ unissant entités discrètes et passages textuels denses, boucle de recherche réflexive à budget borné ($B \le 4$) avec arrêt adaptatif précoce ($f^{(t)} \in \{\text{Continue}, \text{Final}\}$), mode *Reject* souverain interdisant l'extrapolation sans preuve documentaire, et régularisation de variance anti-attention collapse. Références : ADR-0395, ADR-0202, ADR-0375, ADR-0376, ADR-0390. Backlog détaillé : [`epics/epic_wfm_cognitive_wiki_graph.md`](epics/epic_wfm_cognitive_wiki_graph.md). Récits Palier 1 (`status: DRAFT` / `grill_me: PENDING`).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **MLOOP-340-BE** | - | Core/Memory | Schéma Relationnel & Persistance SQLite du Wiki Graph Dual-Layer ($\mathcal{E}_w, \mathcal{R}_w, \mathcal{D}$) | `✅ DONE` | 🟢 `READY_FOR_DEV` | 👤 Humain (Gate 2 Marco, 2026-09-25) |
| [ ] | **MLOOP-341-BE** | - | Pipelines/Ingest | Moteur d'Ingestion & Indexation Dual-Space (Passages Denses, Entités Métier & Hyper-Arêtes) | `✅ DONE` | 🟢 `READY_FOR_DEV` | 👤 Humain (Gate 2 Marco, 2026-09-25) |
| [ ] | **MLOOP-342-BE** | - | Search/Reflection | Boucle de Fact-Search Réflexif à Budget Borné ($B \le 4$) & Arrêt Anticipé Adaptatif | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-343-BE** | - | QA/Grounding | Mode Reject Souverain Anti-Hallucination & Régularisation de Variance de Scoring | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-344-FULL**| - | CLI/VibeCheck | Commande CLI `mloop wiki-search`, Intégration Grill-Me & Sonde Vibe-Check Check 30 | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---

## Épopée : EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2 (Audit d'Artefacts 5-Axes, Détection d'Inversion Causale & Handoff Multi-Harnais) [OPEN]

> 📐 **Origine** : Étude scientifique de référence **ReFigBench: Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts** (*arXiv:2609.18844*, 16/09/2026) — passage au Rubric Standard 5-Axes ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$), détection mécanique de l'inversion causale silencieuse via comparaison de matrices d'adjacence ($\mathbf{A}_{\text{spec}} \text{ vs } \mathbf{A}_{\text{diag}}$), audit déterministe d'arbre d'objets natifs (anti-effondrement des connecteurs), et adaptation des profils de handoff selon le harnais cible (Claude Code, OpenCode, Codex, Cursor). Références : ADR-0396, ADR-0392, ADR-0202, ADR-0375, ADR-0376, ADR-0377, ADR-0394. Backlog détaillé : [`epics/epic_refigbench_artifact_harness_v2.md`](epics/epic_refigbench_artifact_harness_v2.md). Récits Palier 1 (`status: DRAFT` / `grill_me: PENDING`).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **MLOOP-350-BE** | - | Audit/Objects | Moteur d'Audit Déterministe d'Arbre d'Objets Natifs pour Livrables d'Architecture | `✅ DONE` | 🟢 `READY_FOR_DEV` | 👤 Humain (Gate 2 Marco, 2026-09-25) |
| [ ] | **MLOOP-351-BE** | - | Audit/Scoring | Grille d'Audit Découplée 5-Axes Pénétrante ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$) | `✅ DONE` | 🟢 `READY_FOR_DEV` | 👤 Humain (Gate 2 Marco, 2026-09-25) |
| [ ] | **MLOOP-352-BE** | - | Linter/Causality | Linter Matriciel d'Inversion Causale par Comparaison d'Adjacence ($\mathbf{A}_{\text{spec}} \text{ vs } \mathbf{A}_{\text{diag}}$) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-353-BE** | - | Handoff/Harness | Adaptateur de Dev Handoff Multi-Harnais Dédié (Claude Code, OpenCode, Codex & Cursor) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |
| [ ] | **MLOOP-354-FULL**| - | CLI/VibeCheck | Extension CLI `mloop artifact-check 5x`, Enrichissement Vibe-Check Check 27 & EvidencePack 2.0 | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---

## Épopée : EPIC-36-HERDR-WORKER-PERMISSIONS-AND-RUNTIME-GOVERNANCE (Gouvernance & Unification des Permissions des Workers Herdr, Auto-Approbation Zéro-Blindspot & Runtimes Multi-Agents) [OPEN]

> 🛡️ **Origine** : Cadrage formel du 25/09/2026 suite à la découverte de l'angle mort critique de permissions des workers OpenCode & Cline sous Herdr v0.8.2. OpenCode 1.18.30 nécessitant `--auto` et `--agent worker` pour lever les invites bloquantes d'édition (`edit: ask`) et de commandes (`bash: ask`), Cline 3.0.65 requérant `--auto-approve true`, et la directive `external_directory: { "*": "allow" }` étant indispensable pour autoriser les invocations transverses depuis les sous-dossiers de projets. Références : ADR-0389, ADR-0029, ADR-0205, ADR-0346, ADR-0376, ADR-0377, ADR-0202, `ECOSYSTEM_RIGOR_PROTOCOL.md`. Backlog détaillé : [`epics/epic_herdr_worker_permissions_and_runtime_governance.md`](epics/epic_herdr_worker_permissions_and_runtime_governance.md).

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **MLOOP-389-BE** | - | Core/WorkerRuntimes | Gouvernance & Unification des Permissions des Workers Herdr (OpenCode & Cline) | `✅ DONE` | 🟢 `QA_CERTIFIED` | ✅ Sentinel PASS (2026-09-25) · 38/38 Tests PASS |
| [ ] | **MLOOP-390-BE** | - | Commands/Sync | Migration & Synchronisation Idempotente des Permissions `opencode.json` Multi-Projets | `✅ DONE` | 🟡 `READY_FOR_QA` | 👤 PO Marco (Gate 2 validée le 25/09/2026) |
| [ ] | **MLOOP-391-BE** | - | Pipelines/VibeCheck | Sonde Vibe-Check Check 31 : Audit Dynamique de Santé des Permissions & Runtimes Workers | `✅ DONE` | 🟡 `READY_FOR_QA` | 👤 PO Marco (Gate 2 validée le 25/09/2026) |
| [ ] | **MLOOP-392-BE** | - | Core/WorkerRuntimes | Extension Multi-Runtimes Déclarative Herdr (Claude Code, Gemini CLI, Cursor CLI, Codex) | `PENDING` | ⚪ `DRAFT` | ⚪ À faire |

---
