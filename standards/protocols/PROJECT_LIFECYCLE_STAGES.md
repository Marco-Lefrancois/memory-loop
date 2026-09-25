# 🚦 Protocole Normatif : Phases et Portes d'Étape du Cycle de Vie Projet (Project Lifecycle Stages)

**Statut** : SSOT Normatif (ADR-0375, ADR-0391)  
**Date d'effet** : Septembre 2026 (Mis à jour le 25/09/2026 — Auto-clôture Gate 5 & Alignement 5 Phases)  
**Domaine** : Gouvernance de Projet, Cycle en 5 Phases Universelles, Typologie d'Analyses, Parcours Fast-Track & Dualité Grill-Me  

---

## 1. Vue d'Ensemble du Cycle de Vie en 5 Phases

Tout projet géré dans l'écosystème mLoop transite par **5 phases d'ingénierie universelles**, jalonnées par des **Portes d'Étape (*Quality Gates*)** :

```mermaid
flowchart LR
    P1["1. INGEST & EXPLORE<br>(Init, Crawl, Matière première)"] -->|Gate 1 : Ingestion Complète| P2["2. PLAN & ANALYSE<br>(Macro-Cadrage & Grill-Me 1:1)"]
    P2 -->|Gate 2 : Definition of Ready (DoR 6/6)| P3["3. BUILD & DEV<br>(Développement & Tests Unitaires)"]
    P3 -->|Gate 3 : Definition of Done (DoD)| P4["4. VALIDATE & QA<br>(Audit QA, Evals & NLI)"]
    P4 -->|Gate 4 : Conformité Métier| P5["5. SHIP & SYNC<br>(Mise en Prod, Git & Jira Cloud)"]
```

---

## 2. Définition des 5 Phases Universelles & Quality Gates

### 🟡 Phase 1 : `INGEST & EXPLORE` (Socle Préalable Obligatoire)
* **Protocole Normatif** : [`INGESTION_AND_EXPLORATION_PROTOCOL.md`](INGESTION_AND_EXPLORATION_PROTOCOL.md) & [ADR-0377](../adr-system/0377-phase-1-ingest-and-explore-contract-and-gate-1.md).
* **Objectif** : Initialiser la structure du projet (`python src/swarm.py init`), permettre le dépôt humain dans `reference/` (sans sub-readme), et ingérer l'ensemble des sources brutes (maquettes, briefs, wikis, exports Jira, APIs).
* **Activités** :
  - Ingestion via `python src/swarm.py ingest`, `crawl`, `markitdown_convert`, `extract`, `agentic-extract`, `csv-normalize`.
  - Optimisation des maquettes SVG sous `docs/05-assets/` via `python src/swarm.py svg-optimize` (ADR-0332).
  - Analyse exploratoire via Fact-Search local et RAG multi-sources.
* **Livrables Autorisés** :
  - Documents bruts convertis et normalisés sous `docs/00-ingested/` avec `source_manifest.json` et sidecars LOD `.overview.md` (ADR-0335).
  - Actifs visuels et maquettes vectorielles épurées sous `docs/05-assets/` (ADR-0332).
  - Lexique du domaine auto-alimenté sous `docs/04-transverse/lexique_domaine.md`.
  - Index sémantique SQLite FTS5 et hypergraphe Graphify synchronisés (`python src/swarm.py sync`).
* **🚫 Interdictions (Check 13 / Anti-Ghost-Bias)** : Interdiction absolue et bloquante de créer des User Stories sous `backlog/stories/` ou de rédiger des livrables de cadrage macro (`TSHIRT_SIZE_*.md`, `SOW_*.md`) sous `docs/01-architecture/`.
* **🚪 Porte 1 (*Gate 1 : Ingestion Complète & Cadrage Initial Prêt*)** :
  1. G1 : Tous les fichiers bruts de `reference/` sont convertis en Markdown sous `docs/00-ingested/`.
  2. G2 : Les maquettes vectorielles SVG sont optimisées sous `docs/05-assets/`.
  3. G3 : SQLite FTS5 et l'hypergraphe Graphify sont synchronisés.
  4. G4 : Le manifeste `source_manifest.json` et les sidecars LOD `.overview.md` sont présents.
  5. G5 : Règle Check 13 respectée (0 story sous `backlog/stories/`).

---

### 🔵 Phase 2 : `PLAN & ANALYSE` (Dualité Macro-Planification & Micro-Analyse)
* **Objectif** : Transformer la matière brute en décisions d'architecture fermes et en un backlog de User Stories prêtes pour le dev.
* **Structure Bimodale** :
  1. **Sous-étape A : Planification Macro (Cadrage & Chiffrage)** :
     - **Grill-Me Macro (`python src/swarm.py grill-project`)** : Entrevue contradictoire transverse post-ingestion pour éliminer les zones d'ombre d'architecture (SSO, hébergement, conformité Loi 25, exclusions nettes).
     - **Types d'analyses activables (Optionnels)** :
       - Dimensionnement T-Shirt : `python src/swarm.py to-tshirt` ➔ `docs/01-architecture/TSHIRT_SIZE_<PROJET>.md`.
       - Engagement contractuel SOW : `python src/swarm.py to-sow` ➔ `docs/01-architecture/SOW_<PROJET>.md`.
     - **Découpage Macro (`python src/swarm.py to-tickets`)** : Génération des récits de cadrage de Palier 1 (`standards/blueprints/story_draft_template.md` avec `status: DRAFT` et `grill_me: PENDING`) dans `backlog/stories/` et initialisation de `backlog/sprint_backlog.md`.
  2. **Sous-étape B : Analyse Fine Récit par Récit (Agile Sprints)** :
     - **Grill-Me Micro 1:1 (`python src/swarm.py grill-me --story REC-XX`)** : Entrevue chirurgicale résolvant les questions ouvertes de l'ébauche pour produire le récit haute-fidélité (`standards/blueprints/story_template.md` avec `status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6).
* **Parcours Fast-Track (Mandats déjà contractualisés)** :
  - Si un projet démarre avec un SOW déjà signé et des spécifications existantes, les sous-commandes `to-tshirt` et `to-sow` sont **bypassées sans avertissement**. Le projet débute directement l'analyse fine des stories.
* **🚪 Porte 2 (*Definition of Ready*)** : Récits validés 100% sans erreur par WikiFix & Sentinel (DoR 6/6, 4 Piliers Gherkin, EvidencePacks complets).

---

### 🟢 Phase 3 : `BUILD & DEV` (Développement & Delivery)
* **Objectif** : Implémenter physiquement la solution technique validée.
* **Activités** :
  - Workers Herdr isolés (`python src/swarm.py worker-spawn`), développement TDD, refactoring.
* **Livrables Autorisés** :
  - Code source applicatif physique, tests unitaires et d'intégration.
* **🚪 Porte 3 (*Definition of Done*)** : 100% des tests unitaires et d'intégration verts.

---

### 🟣 Phase 4 : `VALIDATE & QA` (Assurance Qualité & Evals)
* **Objectif** : Auditer contradictoirement la qualité, la conformité sémantique et la non-régression.
* **Activités** :
  - Audit contradictoire Sentinel / Rubber Duck, vérification NLI, moisson d'Evals (`AutoEvalHarvester`).
* **Livrables Autorisés** :
  - Rapports d'audit de santé et suite de tests d'évaluation (`memory/evals/`).
* **🚪 Porte 4 (*Exit Criteria*)** : Approbation formelle QA / Sentinel.

---

### ⚪ Phase 5 : `SHIP & SYNC` (Mise en Production & Synchronisations)
* **Objectif** : Déployer en production et synchroniser tous les registres externes.
* **Activités** :
  - Synchronisation Jira Cloud Fail-Closed (`python src/swarm.py jira_sync`).
  - Synchronisation Git distant (`git push origin main`).
  - Clôture et archivage mémoire dans `memory/supersession_ledger.json`.
* **Livrables Autorisés** :
  - Release notes, tickets Jira synchronisés, base sémantique mise à jour (`swarm.py sync`).
* **🚪 Porte 5 (*Gate 5 : Clôture & Synchronisation*)** : Synchronisation Jira et Git scellée sans erreur. Auto-clôture 100% autonome (`requires_human: False`, ADR-0391) dès lors que les tests pré-vol, linters et audits sont au vert (0 FAIL). Intervention humaine par exception uniquement.

---

## 3. Typologie des 4 Types d'Analyses & Règle des 2 Templates

Dans mLoop, un livrable d'analyse n'est **jamais une phase**, mais un **artéfact analytique produit en Phase 2** :

| Type d'Analyse | Livrable Produit | Commande CLI | Statut dans le Cycle |
| :--- | :--- | :--- | :--- |
| **1. Dimensionnement Macro (T-Shirt Size)** | `docs/01-architecture/TSHIRT_SIZE_<PROJET>.md` | `python src/swarm.py to-tshirt` | **Optionnel** (Avant-projet / Enveloppe budgétaire) |
| **2. Cadrage Contractuel (SOW)** | `docs/01-architecture/SOW_<PROJET>.md` | `python src/swarm.py to-sow` | **Optionnel** (Contractualisation & Jalons) |
| **3. Architecture Transverse & Cadrage** | ADRs + `docs/01-architecture/PROJECT_CONSTRAINTS.md` | `python src/swarm.py grill-project` | **Recommandé** (Alignement global et choix structurants) |
| **4. Analyse Fine de Récit** | `backlog/stories/<ID>.md` (`story_template.md`) | `python src/swarm.py grill-me --story <ID>` | **Obligatoire** (Préparation au développement) |

### Règle des 2 Seuls Templates de Récits :
- **Gabarit Palier 1 : `standards/blueprints/story_draft_template.md`** ➔ `status: DRAFT`, `grill_me: PENDING`.
- **Gabarit Palier 2 : `standards/blueprints/story_template.md`** ➔ `status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6.
- *Tout autre gabarit de story est proscrit de l'écosystème.*
