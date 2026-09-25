---
id: PLAN-MLOOP-106-BE
story_id: MLOOP-106-BE
status: DRAFT
harness: opencode
created_at: 2026-09-21
---

# Plan d'Implémentation — Découpage Modulaire des Handlers CLI

> **Objectif** : Ramener 100% de la couche d'orchestration CLI (`src/commands/handlers/`) en conformité ADR-0202 (plafonds 300L / 15 Ko) en découpant les 4 handlers monolithiques (`project.py` 462L, `analysis.py` 525L, `export.py` 340L, `architecture.py` 320L) en packages à façades de réexport intangibles, sans aucune régression fonctionnelle sur les 16 commandes CLI impactées.
> **Source** : Grill-Me 1:1 du 2026-09-21 (4 arbitrages Option A/B) — dossier `memory/evidence/MLOOP-106-BE_fact_dossier.md` ; `FRAMEWORK_STATE.md` lu (baseline 257 violations, init 2026-09-20). Rubber-duck : **APPROUVÉ** (Trust Score 91.6, 0 bloquant).

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes nécessitant la confirmation humaine avant BUILD :**
> - **Conversion module → package** : `project.py`, `analysis.py`, `export.py`, `architecture.py` deviennent des packages (`handlers/project/`, etc.). Les imports dynamiques de `_registry.py` doivent continuer de résoudre `handlers.project:handle_init` via la façade `__init__.py`.
> - **Façades intangibles** : la signature `handle_*(args, state, project_path) -> int` est gelée — aucune rupture de contrat d'import autorisée.
> - **`_registry.py` hors périmètre** : la découpe du registre central (2000L) est reportée à un récit dédié (MLOOP-111-BE) pour isoler le risque de dérive CLI (ADR-0370).
> - **Séquencement 4 lots** : `project` → `analysis` → `export` → `architecture` (ordre de criticité métier décroissante).
> - **Promotion `READY_FOR_DEV`** : subordonnée à l'approbation de ce plan (Interdiction d'Auto-Approbation).


## 3. Modifications Proposées (Proposed Changes)

### A. Package Project (découpage project.py — 462L)

- #### `[NEW]` [`src/commands/handlers/project/__init__.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/__init__.py)
  - **Intention** : Façade de réexport des 6 handlers (`init`, `resume`, `focus`, `vibe_check`, `lifecycle_status`, `lifecycle_clean`) — contrat d'import `_registry.py` préservé.
- #### `[NEW]` [`src/commands/handlers/project/init.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/init.py)
  - **Intention** : `handle_init` — arborescence projet (Loi des 3 Piliers, ADR-0375) (~80L).
- #### `[NEW]` [`src/commands/handlers/project/resume.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/resume.py)
  - **Intention** : `handle_resume` — restauration anti-amnésie (~60L).
- #### `[NEW]` [`src/commands/handlers/project/focus.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/focus.py)
  - **Intention** : `handle_focus` — verrou d'attention (Phase ≥ 2) (~70L).
- #### `[NEW]` [`src/commands/handlers/project/vibe_check.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/vibe_check.py)
  - **Intention** : `handle_vibe_check` — guardrail pré-vol (19 contrôles) (~80L).
- #### `[NEW]` [`src/commands/handlers/project/lifecycle.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/lifecycle.py)
  - **Intention** : `handle_lifecycle_status` + `handle_lifecycle_clean` (~90L).
- #### `[NEW]` [`src/commands/handlers/project/git_hooks.py`](file:///c:/Memory%20Loop/src/commands/handlers/project/git_hooks.py)
  - **Intention** : Extraction du bloc Git-hooks (L156-236, ~80L) — nom imposé anti-collision avec `handlers/hook.py` existant (ADR-0364).
- #### `[DELETE]` [`src/commands/handlers/project.py`](file:///c:/Memory%20Loop/src/commands/handlers/project.py)
  - **Intention** : Remplacé par le package `project/` (conversion module → package).

### B. Package Analysis (découpage analysis.py — 525L)

- #### `[NEW]` [`src/commands/handlers/analysis/__init__.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis/__init__.py)
  - **Intention** : Façade de réexport des 6 handlers d'analyse.
- #### `[NEW]` [`src/commands/handlers/analysis/code_explore.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis/code_explore.py)
  - **Intention** : `handle_code_explore` — exploration AST.
- #### `[NEW]` [`src/commands/handlers/analysis/graph_query.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis/graph_query.py)
  - **Intention** : `handle_graph_query` — consultation du graphe sémantique.
- #### `[NEW]` [`src/commands/handlers/analysis/fact_search.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis/fact_search.py)
  - **Intention** : `handle_fact_search` — recherche plein-texte FTS5.
- #### `[NEW]` [`src/commands/handlers/analysis/deep_search.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis/deep_search.py)
  - **Intention** : `handle_deep_search` — recherche sémantique profonde.

### C. Package Export (découpage export.py — 340L)

- #### `[NEW]` [`src/commands/handlers/export/__init__.py`](file:///c:/Memory%20Loop/src/commands/handlers/export/__init__.py)
  - **Intention** : Façade de réexport des 3 handlers d'export.
- #### `[NEW]` [`src/commands/handlers/export/export.py`](file:///c:/Memory%20Loop/src/commands/handlers/export/export.py)
  - **Intention** : `handle_export` (markdown / json / pdf).
- #### `[NEW]` [`src/commands/handlers/export/notebooklm.py`](file:///c:/Memory%20Loop/src/commands/handlers/export/notebooklm.py)
  - **Intention** : `handle_notebooklm` — export du carnet SSOT.
- #### `[NEW]` [`src/commands/handlers/export/archify.py`](file:///c:/Memory%20Loop/src/commands/handlers/export/archify.py)
  - **Intention** : `handle_archify` — génération de diagrammes vectoriels.
- #### `[DELETE]` [`src/commands/handlers/export.py`](file:///c:/Memory%20Loop/src/commands/handlers/export.py)
  - **Intention** : Remplacé par le package `export/` (conversion module → package).

### D. Package Architecture (découpage architecture.py — 320L)

- #### `[NEW]` [`src/commands/handlers/architecture/__init__.py`](file:///c:/Memory%20Loop/src/commands/handlers/architecture/__init__.py)
  - **Intention** : Façade de réexport des 3 handlers d'architecture.
- #### `[NEW]` [`src/commands/handlers/architecture/architecture.py`](file:///c:/Memory%20Loop/src/commands/handlers/architecture/architecture.py)
  - **Intention** : `handle_architecture` (SOW / TSHIRT_SIZE / ADR).
- #### `[NEW]` [`src/commands/handlers/architecture/doc_gen.py`](file:///c:/Memory%20Loop/src/commands/handlers/architecture/doc_gen.py)
  - **Intention** : `handle_doc_gen` — génération documentaire.
- #### `[NEW]` [`src/commands/handlers/architecture/blueprint.py`](file:///c:/Memory%20Loop/src/commands/handlers/architecture/blueprint.py)
  - **Intention** : `handle_blueprint` — gestion des gabarits SSOT.
- #### `[DELETE]` [`src/commands/handlers/architecture.py`](file:///c:/Memory%20Loop/src/commands/handlers/architecture.py)
  - **Intention** : Remplacé par le package `architecture/` (conversion module → package).

### E. Harnais de Tests (Stratégie 3 couches — OQ-3 Option A)

- #### `[NEW]` [`tests/handlers/`](file:///c:/Memory%20Loop/tests/handlers/)

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **Rupture d'import lors de la conversion module → package** | Élevé | Conversion atomique dans une seule passe par lot ; rejouer la suite non-régression immédiatement ; `git checkout -- src/commands/handlers/<handler>.py` en rollback. |
| **Dérive du guide CLI** (registre non synchronisé) | Élevé | `python src/swarm.py guide --sync` obligatoire après chaque lot ; échec = lot non clôturable (ADR-0370). |
| **Régression silencieuse d'une commande critique** | Moyen | Couche 2 (16 commandes via subprocess) obligatoire ; comparaison sortie / code retour / effets de bord. |
| **Perte d'ordre d'initialisation** (imports au niveau module) | Moyen | Sous-modules sans état global ; vérification `python -c "from src.commands.handlers.project import handle_init"`. |
| **Régression de performance** sur le chemin chaud boot | Moyen | Couche 3 (p95 < 50 ms) ; échec = lot non clôturable. |
| **Conflit parallèle avec MLOOP-100-BE** (`sync_engine.py`) | Faible | Fichiers disjoints ; focus unique = MLOOP-106-BE. |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] Couche 1 — Tests unitaires directs :
  ```powershell
  python -m pytest tests/handlers/ -v
  ```
- [ ] Couche 2 — Non-régression CLI (16 commandes) :
  ```powershell
  python -m pytest tests/test_cli_handlers_regression.py -v
  ```
- [ ] Couche 3 — Harnais performance :
  ```powershell
  python -m pytest tests/performance/test_handlers_latency.py -v
  ```
- [ ] Conformité déterministe (0 violation RULE-AST-01 attendue) :
  ```powershell
  python src/swarm.py code-check --file src/commands/handlers/project/__init__.py; python src/swarm.py code-check --file src/commands/handlers/analysis/__init__.py; python src/swarm.py code-check --file src/commands/handlers/export/__init__.py; python src/swarm.py code-check --file src/commands/handlers/architecture/__init__.py
  ```
- [ ] Parité Guide CLI (ADR-0370) :
  ```powershell
  python src/swarm.py guide --sync
  ```
- [ ] Gate structurelle (Gate C12 — Domain Sanity, exigence FRAMEWORK_STATE) :
  ```powershell
  python src/swarm.py struct-check --project mLoop --file MLOOP-106-BE.md
  ```
- [ ] Validité JSON de l'EvidencePack :
  ```powershell
  python -c "import json; json.load(open(r'Projects/mLoop/memory/evidence/MLOOP-106-BE_evidence.json', encoding='utf-8')); print('OK')"
  ```

### B. Vérifications Manuelles & Scénarios Clés
- [ ] **Scénario Nominal** : `python src/swarm.py vibe-check --project TestProjet` — les handlers découpés répondent identiquement via `_registry.py`.
- [ ] **Scénario d'Exception / Résilience** : conflit de verrou sur `project/git_hooks.py` → trace explicite (ADR-0369), code de sortie non nul, zéro silence.
- [ ] **Scénario Performance** : p95 < 50 ms confirmée par la Couche 3.
- [ ] **Scénario Parité** : `guide --sync` affiche 100% de parité sans dérive.

### C. Definition of Done (DoD)
- [ ] Tous les packages créés respectent ADR-0202 (≤ 300L / ≤ 15 Ko) et ADR-0369 (zéro `except: pass`, zéro ressource hors `with`).
- [ ] `code-check --file` PASS sur les 4 packages.
- [ ] Signature `handle_*(args, state, project_path) -> int` : imports publics inchangés (vérifiés par la Couche 2).
- [ ] Couches 1, 2 et 3 au vert ; `guide --sync` sans dérive.
- [ ] Archivage du plan dans `Projects/mLoop/memory/plan/implementation_plan_MLOOP-106-BE.md` (fait — ce fichier).

  - **Intention** : ~25 tests unitaires directs (1 par point d'entrée) — Couche 1.
- #### `[NEW]` [`tests/test_cli_handlers_regression.py`](file:///c:/Memory%20Loop/tests/test_cli_handlers_regression.py)
  - **Intention** : Suite d'intégration CLI sur les 16 commandes impactées — Couche 2.
- #### `[NEW]` [`tests/performance/test_handlers_latency.py`](file:///c:/Memory%20Loop/tests/performance/test_handlers_latency.py)
  - **Intention** : Harnais de latence (p95 import + exécution < 50 ms) — Couche 3.

---

- #### `[NEW]` [`src/commands/handlers/analysis/code_impact.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis/code_impact.py)
  - **Intention** : `handle_code_impact` + `handle_code_affected` — analyse d'impact AST.
- #### `[DELETE]` [`src/commands/handlers/analysis.py`](file:///c:/Memory%20Loop/src/commands/handlers/analysis.py)
  - **Intention** : Remplacé par le package `analysis/` (conversion module → package).

---

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> **OQ-106 (résolue — exemption de traçabilité)** : Matrice des Contrats API non applicable — composant headless sans route REST/CTA `[API de soumission à définir]`, consignée dans la story (validation rubber-duck 2026-09-21, 0 bloquant).
> **Aucune OQ bloquante restante** : les 4 arbitrages de cadrage sont tranchés (§5 du dossier de preuves).

---
