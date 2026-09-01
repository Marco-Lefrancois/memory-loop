# 🏛️ Architecture SSOT : Cycle Spec-Driven Dev à 5 Phases & Graph Loop Engine

Ce document constitue la référence d'architecture officielle décrivant l'articulation entre le cycle d'analyse en 5 phases de mLoop et le moteur d'exécution **Graph Loop Engineering** (DAG Multi-Agents).

---

## 🗺️ Matrice d'Écosystème par Phase (5 Phases)

| Phase Cycle mLoop | Rôle de l'Analyse | Nœud DAG (`graph-run`) | Outils CLI & Plugins mLoop | Outils MCP & RAG | Guardrail & Critères Obligatoires |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1: SPEC / INGEST** | Ingestion documentaire & cadrage du périmètre | **`node_spec`** *(Scope)* | `python src/swarm.py ingest`<br>`markitdown_convert`<br>`office_read` | `on_search_notes`<br>`on_chat`<br>`opennotebook://` | Ingestion synchrone Open Notebook (registre SHA256 anti-doublons). |
| **Phase 2: PLAN / ARCHI** | Découpage des besoins & arbitrage des choix d'architecture | **`node_plan_be`** / **`node_plan_fe`** *(Fan-Out)* | `python src/swarm.py grill`<br>`python src/swarm.py wayfinder`<br>`python src/swarm.py to-spec`<br>`python src/swarm.py to-tickets` | `loop_mem_search`<br>`graphify query`<br>`graphify explain` | Protocole **Plan-First** (`implementation_plan.md`), **Grill-with-Docs** (Auto-ADR & OQ), gabarits `blueprints/`. |
| **Phase 3: BUILD** | Domaine d'Analyse & Validation de la Frontière | **`node_reducer`** *(Barrier & Reduce)* | `python src/swarm.py confidence`<br>`write_to_file`<br>`replace_file_content` | `loop_mem_preload_context` | Boundary strict (`C:\Memory Loop\src\` ou `Projects/<p>/backlog/`) + Fusion déterministe Python des `EvidencePacks`. |
| **Phase 4: VALIDATE / QA** | Audit contradictoire & contrôle qualité | **`node_critic`** *(Evaluator Node)* | `python src/swarm.py wikifix`<br>`python src/swarm.py aoep`<br>`python src/swarm.py deepen`<br>`python src/swarm.py audit-loop` | `loop_mem_search` | Blindage **4 Piliers Gherkin** (Nominal, Rejet/Exception, Mode Dégradé, UX/Observabilité) + Score **INVEST** + Exit 0. |
| **Phase 5: SHIP / SYNC** | Clôture d'analyse & synchronisation | **Orchestrateur** *(Ship & Sync)* | `python src/swarm.py sync`<br>`python src/swarm.py cycle-status`<br>`python src/swarm.py calibrate` | `loop_mem_search` | Indexation SQLite FTS5, mise à jour Graphify et **8/8 PASS** au Calibrage. |

---

## ⚡ Optimisations Python & Invariants d'Ingénierie IA

Le code Python sous-jacent respecte les **8 piliers d'optimalité en AI Engineering** :

1. **Générateurs et Évaluation Paresseuse (*Lazy Evaluation*)** :
   - Parcours et moissonnage streaming dans `wikifix.py` et `calibrate.py` pour un profil mémoire plat (< 30 Mo).
2. **Context Managers (`with`)** :
   - Isolation et fermeture garantie des descripteurs de fichiers, bases SQLite et sessions RAG.
3. **Resilience Network avec Backoff Exponentiel & Jitter (`src/utils/retry.py`)** :
   - Décorateur `@robust_api_call` prévenant les échecs 429 Rate Limit et micro-coupures réseau.
4. **Token Budget Guard (`src/utils/token_budget.py`)** :
   - Calcul rapide de l'empreinte en jetons et tronquage prioritaire des contextes sous le plafond (`context_budget_tokens: 8000`), préservant les preuves `CRITICAL` et `HIGH`.
5. **State Checkpointing & Resume (`src/pipelines/graph_router.py`)** :
   - Sauvegarde d'état sous `.mloop_tmp/checkpoints/<initiative>.json` permettant la reprise immédiate via `graph-run --resume`.
6. **Nœuds Déterministes Pure Code (`EvidenceReducer`)** :
   - Fusion et déduplication des preuves sur les barrières du DAG en pure logique Python à 0ms de surcoût LLM.
7. **Dataclasses Typées & Validations Pydantic (`src/pipelines/evidence.py`)** :
   - Modèles `EvidencePack`, `EvidenceItem`, `EvaluationResult` garantissant la cohérence des structures sur toutes les arêtes.
8. **Composition Déclarative via Méthodes Magiques (`src/pipelines/base.py`)** :
   - Surcharge de `__or__` (`|`) et `__call__` pour enchaîner les étapes de pipeline de façon lisible et extensible.
