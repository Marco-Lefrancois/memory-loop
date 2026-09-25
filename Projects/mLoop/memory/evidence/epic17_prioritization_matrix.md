# Matrice de Priorisation EPIC-17 — 39 Modules RULE-AST-01

> Audit : `code-check --all` — 2026-09-23 | 329 fichiers | 39 violations RULE-AST-01 | Ecart vs baseline : +1 (archify.py cree hors plafond EPIC-16)
> Methode Blast Radius : ast_import_count (fallback deterministe — CodeGraph indispo, Pilier 3 annote)

## Sequence Beachhead (OQ-171-05)

| Lot | Contenu | Statut |
|:---:|:--------|:------:|
| Lot 0 Pilote | `src/pipelines/vibe_check.py` decoupage sous-modules | DONE_TESTED MLOOP-170-BE 2026-09-23 |
| Lot 1 Top 5 critiques | state.py / db.py / sync.py / lifecycle.py / _registry.py | Recits unitaires a creer |
| Lot 2 BR 2-5 | ingest_agent, retriever, standards_graph, state_machine, graphify/agent, crawler, critic, llm_client, evidence_pack, compaction, gates, struct_checker, domain_invariants | Lots adaptatifs |
| Lot 3 Residus BR 0-1 | 21 fichiers restants incl. archify.py + server.py (OQ-171-03) | Lots adaptatifs |

Zero derogation (OQ-171-04) : plafond 300L strict pour 100% des fichiers, _registry.py inclus.

## Matrice complete (39 fichiers, tri BR decroissant)

| # | Fichier | Lignes | Ko | Blast Radius | Methode BR | Criticite | Lot |
|--:|:--------|-------:|---:|-------------:|:-----------|:----------|:----|
| 1 | src/state.py | 770 | 31.1 | 78 | ast_import_count | coeur | Lot 1 |
| 2 | src/loop_mem/db.py | 956 | 36.6 | 20 | ast_import_count | coeur | Lot 1 |
| 3 | src/pipelines/sync.py | 542 | 22.7 | 10 | ast_import_count | coeur | Lot 1 |
| 4 | src/core/lifecycle.py | 852 | 38.6 | 8 | ast_import_count | coeur | Lot 1 |
| 5 | src/pipelines/ingest_agent.py | 302 | 11.9 | 7 | ast_import_count | coeur | Lot 2 |
| 6 | src/engine/fact_search/retriever.py | 681 | 24.0 | 6 | ast_import_count | coeur | Lot 2 |
| 7 | src/core/standards_graph.py | 738 | 29.6 | 6 | ast_import_count | coeur | Lot 2 |
| 8 | src/pipelines/state_machine.py | 592 | 22.6 | 5 | ast_import_count | coeur | Lot 2 |
| 9 | src/pipelines/graphify/agent.py | 476 | 20.3 | 5 | ast_import_count | coeur | Lot 2 |
| 10 | src/pipelines/crawler.py | 927 | 38.2 | 4 | ast_import_count | coeur | Lot 2 |
| 11 | src/engine/rubber_duck/critic.py | 392 | 16.3 | 3 | ast_import_count | coeur | Lot 2 |
| 12 | src/core/llm_client.py | 380 | 14.6 | 3 | ast_import_count | coeur | Lot 2 |
| 13 | src/pipelines/evidence_pack.py | 821 | 36.7 | 3 | ast_import_count | coeur | Lot 2 |
| 14 | src/engine/hooks/compaction.py | 633 | 26.1 | 3 | ast_import_count | coeur | Lot 2 |
| 15 | src/commands/_registry.py | 2028 | 73.1 | 3 | ast_import_count | coeur | Lot 1 | **DONE_TESTED** — MLOOP-175-BE 2026-09-23 — package _registry/ (9 modules ≤300L) |
| 16 | src/core/gates.py | 747 | 26.4 | 3 | ast_import_count | coeur | Lot 2 |
| 17 | src/pipelines/struct_checker.py | 937 | 42.0 | 3 | ast_import_count | coeur | Lot 2 |
| 18 | src/engine/fact_check/domain_invariants.py | 710 | 29.9 | 3 | ast_import_count | coeur | Lot 2 |
| 19 | src/pipelines/completion_gate.py | 317 | 12.1 | 2 | ast_import_count | coeur | Lot 3 |
| 20 | src/bridges/mcp_graphify.py | 323 | 11.4 | 2 | ast_import_count | outillage | Lot 3 |
| 21 | src/pipelines/guide_generator.py | 360 | 14.8 | 2 | ast_import_count | outillage | Lot 3 |
| 22 | src/core/hypergraph_engine.py | 387 | 15.1 | 2 | ast_import_count | coeur | Lot 3 |
| 23 | src/converters/svg_to_md.py | 991 | 37.8 | 2 | ast_import_count | outillage | Lot 3 | **DONE_TESTED** — MLOOP-176-BE 2026-09-24 — package `svg_to_md/` (5 modules + `__init__.py` ≤298L) + shim 4L, smoke import VERT (7 callers), code-check 7/7 PASS, 1403 PASS/1 FAIL (flaky pré-existant identique baseline), harvest OK |
| 24 | src/dashboard/routers/archify.py | 463 | 16.7 | 2 | ast_import_count | outillage | Lot 3 OQ-171-03 |
| 25 | src/pipelines/graph_router.py | 477 | 21.1 | 2 | ast_import_count | coeur | Lot 3 |
| 26 | src/pipelines/plugin_validate.py | 392 | 15.0 | 2 | ast_import_count | outillage | Lot 3 |
| 27 | src/pipelines/calibrate.py | 837 | 41.2 | 2 | ast_import_count | outillage | Lot 3 |
| 28 | src/bridges/drawdb_bridge.py | 465 | 17.5 | 1 | ast_import_count | outillage | Lot 3 |
| 29 | src/core/herdr_worker_core.py | 381 | 14.6 | 1 | ast_import_count | coeur | Lot 3 |
| 30 | src/pipelines/wikifix_core.py | 304 | 13.0 | 1 | ast_import_count | outillage | Lot 3 |
| 31 | src/pipelines/worker_pipeline.py | 376 | 14.9 | 1 | ast_import_count | coeur | Lot 3 |
| 32 | src/core/declarative_extractor.py | 343 | 15.9 | 1 | ast_import_count | coeur | Lot 3 |
| 33 | src/pipelines/rho_optimizer.py | 325 | 12.4 | 1 | ast_import_count | outillage | Lot 3 |
| 34 | src/pipelines/jira/jira_item_sync.py | 317 | 10.6 | 1 | ast_import_count | outillage | Lot 3 |
| 35 | src/bridges/mcp_proxy_router.py | 366 | 13.5 | 0 | ast_import_count | outillage | Lot 3 |
| 36 | src/dashboard/server.py | 144 | 4.8 | 0 | ast_import_count | outillage | Lot 3 OQ-171-03 · RESOLU MLOOP-177-BE |
| 37 | src/pipelines/graft_deep_test.py | 318 | 10.7 | 0 | ast_import_count | outillage | Lot 3 |
| 38 | src/bridges/mcp_herdr.py | 581 | 23.7 | 0 | ast_import_count | outillage | Lot 3 |
| 39 | src/pipelines/token_counter.py | 305 | 9.7 | 0 | ast_import_count | outillage | Lot 3 |

Archive 2026-09-23 MLOOP-171-BE source codecheck_audit_epic17.txt