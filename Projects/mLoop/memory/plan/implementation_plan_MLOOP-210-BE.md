---
id: PLAN-210-BE
story_id: MLOOP-210-BE
status: COMPLETED # DRAFT | APPROVED | EXECUTING | COMPLETED
harness: opencode
created_at: 2026-09-24
---

# Socle Protocolaire MCP 2026-07-28 — Négociation de Version, Header Routing & Observabilité

> **Objectif** : construire le socle protocolaire partagé de l'EPIC-21 (ADR-0387) — négociation de version à l'initialisation contre un **registre unique** (`2026-07-28`, `2025-11-25`, `2024-11-05`), routage par en-têtes HTTP/SSE sans lecture du corps, exposition honnête `_meta.routing` en stdio, politique de repli unifiée par requête (ADR-004 Q1) et observabilité (alertes / journal / adoption), **sans jamais rejeter une version connue**.

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes exigeant une confirmation explicite de l'utilisateur :**
> - **Découpage ADR-0202** : l'original `_mcp_protocol.py` (511 L / 19,8 Ko) violait RULE-AST-01 avant toute écriture → socle scindé en 4 modules (`core` / `routing` / `fallback` + façade). *Arbitrage 210-Q1 : « constante module unique » — le registre unique est conservé tel quel dans `_mcp_protocol_core.py`.*
> - **Extractions dérivées** : `mcp_recall.py`, `mcp_proxy_registry.py`, `_resilience_guard.py` créés pour ramener `mcp_loop_mem.py` (292 L), `mcp_proxy_router.py` (366 → **267 L**) et `mcp_resilience_guard.py` (279 → **233 L**) sous le plafond de 300 lignes. *La surface publique est préservée par ré-export (API historique intacte).*
> - **Tier B abandonné** : `mcp_graphify.py` (323 L) et `mcp_herdr.py` (581 L) **ne sont pas modifiés** — déjà en violation et verrouillés par le garde-fou anti-aggravation `src/pipelines/ast_delta_checker.py` (MLOOP-171-BE / OQ-171-02). *Aucun pont supplémentaire n'est présumé couvert.*
> - **Code d'erreur de version** : `-32600` (SSOT récit) plutôt que `UnsupportedProtocolVersionError` (spec 2026-07-28) — statut HTTP `400` aligné sur la spec → **OQ-210-02**.

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-210-01** : l'ADR-005 (Ligne 8) classe `mcp_proxy_router` parmi les « Transports HTTP », alors que `mcp_proxy_router.main()` et `mcp_resilience_guard.main()` lisent `sys.stdin` (boucles stdio). L'inventaire des transports HTTP n'est pas clôturé $\rightarrow$ *Recommandation : trancher avant le build de 211, sans bloquer 210 (ADR-004 Q5).*
> - **OQ-210-02** : conformité SEP-2243 $\rightarrow$ *Recommandation : conserver `MCP-Tool-Name` canonique + alias `Mcp-Name` (déjà implémenté), conserver `-32600` + `data.supported/requested`, et journaliser sans rejeter les divergences en-tête/corps — réouvrir uniquement si un client tiers exige le code dédié.*
> - **Sources de l'écart** : [`EPIC-21_namespace_conformity.md`](file:///c:/Memory%20Loop/Projects/mLoop/memory/evidence/EPIC-21_namespace_conformity.md)

---

## 3. Modifications Proposées (Proposed Changes)

### Socle protocolaire (nouveau)

- #### `[NEW]` [`src/bridges/_mcp_protocol_core.py`](file:///c:/Memory%20Loop/src/bridges/_mcp_protocol_core.py)
  - **Intention** : registre unique des versions + noms d'en-têtes + `COVERED_BRIDGES` + `FALLBACK_POLICY` + `KNOWN_METHODS` + `negotiate_version` / `declared_version` / `invalid_version_error` / helpers d'en-têtes.
  - **Impact** : source de vérité unique anti-dérive (poignée de main ↔ en-têtes) — 205 L.

- #### `[NEW]` [`src/bridges/_mcp_protocol_routing.py`](file:///c:/Memory%20Loop/src/bridges/_mcp_protocol_routing.py)
  - **Intention** : `route_from_headers()` (zéro lecture du corps), `response_headers()`, `build_routing_meta()` / `attach_routing_meta()` (`_meta.routing`), `enrich_initialize_result()` (+ `supportedVersions`).
  - **Impact** : 168 L.

- #### `[NEW]` [`src/bridges/_mcp_protocol_fallback.py`](file:///c:/Memory%20Loop/src/bridges/_mcp_protocol_fallback.py)
  - **Intention** : `apply_fallback_policy()` (une application par requête, `never_rejects`), alertes `protocol_version_obsolete`, journal de repli, métrique d'adoption, `reset_protocol_observability()`.
  - **Impact** : 189 L.

- #### `[NEW]` [`src/bridges/_mcp_protocol.py`](file:///c:/Memory%20Loop/src/bridges/_mcp_protocol.py)
  - **Intention** : façade de ré-export (API publique historique préservée pour `mcp_sse_server`, `mcp_proxy_router`, `mcp_resilience_guard`).
  - **Impact** : 101 L.

### Ponts Tier A (périmètre ADR-005)

- #### `[MODIFY]` [`src/bridges/mcp_loop_mem.py`](file:///c:/Memory%20Loop/src/bridges/mcp_loop_mem.py)
  - **Intention** : `handle_initialize(..., *, transport, headers, version_decision)` avec refus `-32600` **sans mutation de session** ; `process_message(..., *, transport, headers, version_decision, apply_fallback)` avec résolution de version, repli unique et `attach_routing_meta`.
  - **Impact** : `handle_initialize`, `process_message`, `__all__` — 292 L (plafond respecté).

- #### `[MODIFY]` [`src/bridges/mcp_sse_server.py`](file:///c:/Memory%20Loop/src/bridges/mcp_sse_server.py)
  - **Intention** : route résolue **avant** lecture du corps (version inconnue → HTTP 400 `-32600` sans lire le corps), désaccords en-tête/corps journalisés sans rejet, en-têtes de réponse, `apply_fallback_policy` unique, welcome SSE avec `supportedVersions`, `/health.protocol_adoption`.
  - **Impact** : `messages_endpoint`, `sse_endpoint`, `health_endpoint` — 289 L.

- #### `[MODIFY]` [`src/bridges/mcp_proxy_router.py`](file:///c:/Memory%20Loop/src/bridges/mcp_proxy_router.py)
  - **Intention** : négociation par requête, repli, `_meta.routing` dans la boucle stdio.
  - **Impact** : `handle_initialize`, `main` — 366 → **267 L** (violation corrigée).

- #### `[MODIFY]` [`src/bridges/mcp_resilience_guard.py`](file:///c:/Memory%20Loop/src/bridges/mcp_resilience_guard.py)
  - **Intention** : idem pour la boucle stdio de résilience.
  - **Impact** : `handle_initialize`, `main` — 279 → **233 L** (plafond respecté).

### Extractions de modularisation (dépendances des deux derniers points)

- #### `[NEW]` [`src/bridges/mcp_proxy_registry.py`](file:///c:/Memory%20Loop/src/bridges/mcp_proxy_registry.py)
  - **Intention** : `PHASE_TOOL_FILTER` + `TOOL_REGISTRY` sortis de `mcp_proxy_router` — 184 L.
- #### `[NEW]` [`src/bridges/_resilience_guard.py`](file:///c:/Memory%20Loop/src/bridges/_resilience_guard.py)
  - **Intention** : exceptions + `MCPResilienceGuard` + `compute_workflow_digest` sortis de `mcp_resilience_guard` — 187 L.
- #### `[NEW]` [`src/bridges/mcp_recall.py`](file:///c:/Memory%20Loop/src/bridges/mcp_recall.py)
  - **Intention** : `log_error`, `_PRELOAD_CACHE`, `auto_recall_passive_memory`, `preload_story_context`, `clear_preloaded_context` sortis de `mcp_loop_mem` (API publique ré-exportée) — 130 L.

### Tests & preuves

- #### `[NEW]` [`tests/test_mcp_protocol_socle.py`](file:///c:/Memory%20Loop/tests/test_mcp_protocol_socle.py)
  - **Intention** : Scénarios Gherkin **1 à 3** (nominal HTTP, rejet dur, version obsolète) — 241 L.
- #### `[NEW]` [`tests/test_mcp_protocol_routage.py`](file:///c:/Memory%20Loop/tests/test_mcp_protocol_routage.py)
  - **Intention** : Scénarios Gherkin **4 à 7** (repli hérité, stdio honnête, frontière active, observabilité) — 275 L.
- #### `[NEW]` [`Projects/mLoop/memory/evidence/EPIC-21_namespace_conformity.md`](file:///c:/Memory%20Loop/Projects/mLoop/memory/evidence/EPIC-21_namespace_conformity.md)
  - **Intention** : falsification externe des namespaces (ADR-004 Q5) + OQ-210-01/02.
- #### `[MODIFY]` [`Projects/mLoop/memory/evidence/MLOOP-210-BE_evidence.json`](file:///c:/Memory%20Loop/Projects/mLoop/memory/evidence/MLOOP-210-BE_evidence.json)
  - **Intention** : preuves fact-search externes, `external_references`, `open_questions`, `deliverables`, `admission_of_limits`, `test_results`, audit épistémique.

> **Aucun fichier hors périmètre 210 modifié.** `backlog/sprint_backlog.md` n'est **pas** touché (prérogative de l'orchestrateur) ; `sync` et `git commit` ne sont **pas** exécutés par ce worker.

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **Rejet involontaire d'une version connue** (rétrocompatibilité cassée) | Élevé | `FALLBACK_POLICY["never_rejects"] = True` + tests 3/4/7 ; rollback = rétablir `main`/`process_message` antérieurs (`git stash` ou commit précédent `01746c1`). |
| **Double application de la politique de repli** (endpoint + processeur) | Moyen | Drapeau `apply_fallback=False` passé par `messages_endpoint` ; couvert par le journal à 2 entrées exactes du scénario 7. |
| **Régression du préchargeur / SDK** après extraction `mcp_recall` | Moyen | Ré-exports dans `mcp_loop_mem` ; suites `test_preloader`, `test_mcp_loop_mem`, `test_mcp_sse_transport` → 11 + 60 tests verts. |
| **Agravation RULE-AST-01** sur `mcp_graphify` / `mcp_herdr` | Moyen | Aucune écriture sur ces fichiers (garde-fou `ast_delta_checker.py`) ; `code-check` 13/13 PASS. |
| **Dérive du registre** (poignée de main ≠ en-têtes) | Moyen | Constantes **une seule fois** dans `_mcp_protocol_core.py`, façade en ré-export ; test d'import (AST) `importateurs == COVERED_BRIDGES`. |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés

- [x] Commande(s) de test / linting exécutées :
  ```powershell
  # 1. Scenarios Gherkin du recit (22 tests attendus)
  python -m pytest tests/test_mcp_protocol_socle.py tests/test_mcp_protocol_routage.py -q -p no:cacheprovider
  # -> 22 passed

  # 2. Non-regression MCP (60 tests attendus)
  python -m pytest tests/test_mcp_loop_mem.py tests/test_mcp_sse_transport.py `
    tests/test_mcp_resilience_guard.py tests/test_mcp_openviking_bridge.py `
    tests/test_mcp_protocol_socle.py tests/test_mcp_protocol_routage.py -q -p no:cacheprovider
  # -> 60 passed

  # 3. Non-regression modules connexes (11 tests attendus)
  python -m pytest tests/test_preloader.py tests/test_aoep_governance.py `
    tests/test_unlearning.py tests/test_context_guard.py -q -p no:cacheprovider
  # -> 11 passed

  # 4. Gate C12 (Domain Sanity / structure) — Gatekeeper structurel Read-Only
  python src/swarm.py struct-check --project mLoop --file Projects/mLoop/backlog/stories/MLOOP-210-BE.md
  # -> MLOOP-210-BE.md — Conforme (struct-check)

  # 5. Astreinte ADR-0202 (plafond 300 L / 15 Ko) sur les 13 fichiers livres
  python src/swarm.py code-check --file <fichier>
  # -> 13/13 PASS, 0 violation RULE-AST-01
  ```

- [x] **Checklist FRAMEWORK_STATE (ADR-0352)** :
  1. **Status source vérifié** : frontmatter lu ce jour → `status: IN_DEV` (id `MLOOP-210-BE`, `layer: backend`, `invest_score: 6/6`).
  2. **Certificat NLI daté** : `struct-check` exécuté le **2026-09-24**, postérieur au dernier commit framework (`01746c1`, 2026-09-24 14:22) et à la dernière entrée `FRAMEWORK_STATE.md` (2026-09-24) → **non obsolète**.
  3. **`struct-check` inclus dans §5A** : ✅ commande + résultat *Conforme* (active Gate C12 — `DI-POL`, `DI-PHY`, `DI-TMP`, `DI-STA`, `DI-CRD`).
  4. **`verification_harness` non vide** : ✅ 7 scénarios renseignés (tableau §5D).
  5. **Transition d'état valide** : `IN_DEV → DONE_TESTED` conforme à `STORY_LIFECYCLE_PROTOCOL.md` (L16) ; la bascule de statut du récit et du `sprint_backlog.md` est **à la charge de l'orchestrateur**.

### B. Vérifications Manuelles & Scénarios Clés

- [x] **Scénario Nominal** : client `2026-07-28` sur `/messages` → 200, en-têtes échoyés (`MCP-Protocol-Version`, `MCP-Method`, `MCP-Tool-Name`), `initialize` publie `supportedVersions`.
- [x] **Scénario d'Exception / Résilience** : version hors registre → HTTP 400 + `-32600` **avant lecture du corps** (corps vide) ; version `2024-11-05` → 200 + alerte + repli ; client sans en-tête → 200 (jamais de rejet).
- [x] **Honnêteté stdio** : `_meta.routing` présent, aucun en-tête HTTP dans le dump JSON, compteur d'adoption inchangé.
- [x] **Frontière active** : `COVERED_BRIDGES` = 4 ponts ; importateurs AST du socle == `COVERED_BRIDGES` ; `mcp_graphify` / `mcp_herdr` hors inventaire.

### C. Definition of Done (DoD)

- [x] Tous les fichiers modifiés respectent les standards du projet (Zéro lint error) : `code-check` **13/13 PASS**, `struct-check` **Conforme**.
- [x] Archivage automatique du plan dans `Projects/mLoop/memory/plan/implementation_plan_MLOOP-210-BE.md` (le présent fichier).
- [x] EvidencePack mis à jour : `memory/evidence/MLOOP-210-BE_evidence.json` (32 clés, `status: VALIDATED`, `verification_harness` 7/7 PASS).
- [x] Falsification externe archivée : `memory/evidence/EPIC-21_namespace_conformity.md`.
- [x] Sidecar worker ADR-0355 : `memory/worker_MLOOP-210-BE.status` → `COMPLETED` (relecture via `read_worker_signal` validée).
- [ ] **Orchestrateur** : `sprint_backlog.md` → `DONE_TESTED`, `python src/swarm.py sync --project mLoop`, `git commit/push`.

### D. Verification Harness (ADR-0352 — non vide)

| # | Scénario Gherkin (récit §Scénarios de test) | Réf. de test | Statut |
| :-- | :--- | :--- | :-- |
| 1 | Négociation et routage nominal d'un client 2026-07-28 sur transport HTTP/SSE | `tests/test_mcp_protocol_socle.py::TestNominaleHTTP` (4 tests) | ✅ PASS |
| 2 | Rejet dur d'une version inconnue du registre | `tests/test_mcp_protocol_socle.py::TestRejetDurVersionInconnue` (4 tests) | ✅ PASS |
| 3 | Version obsolète admise avec alerte structurée et repli sans rejet | `tests/test_mcp_protocol_socle.py::TestVersionObsoleteAvecRepli` (3 tests) | ✅ PASS |
| 4 | Repli gracieux d'un client sans en-tête moderne | `tests/test_mcp_protocol_routage.py::TestRepliClientHeritage` (2 tests) | ✅ PASS |
| 5 | Exposition honnête des informations de routage en transport stdio | `tests/test_mcp_protocol_routage.py::TestRoutageStdioHonnete` (3 tests) | ✅ PASS |
| 6 | Frontière active sur l'inventaire des transports exposés en réseau | `tests/test_mcp_protocol_routage.py::TestFrontiereActivePonts` (3 tests) | ✅ PASS |
| 7 | Observabilité de l'obsolescence, du repli et de l'adoption des en-têtes | `tests/test_mcp_protocol_routage.py::TestObservabiliteProtocolaire` (3 tests) | ✅ PASS |
