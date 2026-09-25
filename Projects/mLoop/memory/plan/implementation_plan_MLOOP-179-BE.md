# Plan d'Implémentation — MLOOP-179-BE

## Métadonnées

| Champ | Valeur |
|:---|:---|
| Story ID | MLOOP-179-BE |
| Titre | Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10) |
| Date | 2026-09-23 |
| Protocole | MODULAR_EXTRACTION_PROTOCOL.md — Cas général §2 (famille Sync/Jira/Git) |
| Statut Plan | EXECUTED |

---

## §1. Contexte & Décision Q1-B

Source monolithique : `src/pipelines/sync.py` — 542 L / 23.2 Ko — RULE-AST-01 FAIL.

**Décision Q1-B retenue** : 3 sous-modules thématiques + shim de ré-export.

| Module | Responsabilités | Cible |
|:---|:---|:---|
| `_sync_docs.py` | cache disque, directives ADRs, OQs → wayfinder, sprint backlog SSOT | ≤ 300 L |
| `_sync_graph.py` | git pull wikis (timeout=8), hypergraphe ADR-0343 | ≤ 300 L |
| `_sync_run.py` | orchestrateur `run_sync`, imports lazy db/struct | ≤ 300 L |
| `__init__.py` | shim ré-export, logger, WikiFixAgent, GraphifyAgent | ≤ 100 L |

---

## §2. Contraintes Appliquées

- **ADR-0202 / RULE-AST-01** : chaque module < 300 L / 15 Ko ✅
- **ADR-0369** : `subprocess.run(git pull, timeout=8)` conservé tel quel dans `_sync_graph.py` — 1/1 appels réseau bornés ✅
- **Q5** : `from src.state import LoopState, JournalEntry` top-level dans `_sync_run.py` (dépend shim MLOOP-173-BE) ✅
- **db lazy** : import dans le corps de `run_sync` (dépend shim MLOOP-178-BE) ✅
- **Zéro import lifecycle** : vérifié par grep — aucun import lifecycle dans les 4 fichiers ✅
- **Rétrocompatibilité 10 callers** : aucun caller modifié — le package résout tous les imports via `__init__.py` ✅

---

## §3. Séquence d'Exécution

1. Lecture complète de `src/pipelines/sync.py` (542 L) — cartographie des familles.
2. Création du répertoire `src/pipelines/sync/`.
3. Écriture de `_sync_docs.py` (cache + directives + OQ + sprint — 298 L / 11.6 Ko).
4. Écriture de `_sync_graph.py` (wikis git + hypergraphe — 199 L / 8.0 Ko).
5. Écriture de `_sync_run.py` (orchestrateur — 213 L / 7.6 Ko).
6. Écriture de `__init__.py` (shim — 63 L / 1.9 Ko).
7. Vérification : Python résout `src.pipelines.sync` → package (pas le fichier `.py`).
8. Correction logger : pattern `_get_logger()` via `sys.modules` pour patchabilité tests.
9. code-check 4/4 PASS.
10. import smoke PASS (8 symboles).
11. pytest 1380 PASSED / 0 FAILED (baseline 1378 + 2 SKIPPED→PASS).

---

## §4. Checklist de Clôture

- [x] Chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS)
- [x] Shim `__init__.py` : `from src.pipelines.sync import *` — zéro ImportError
- [x] Smoke check : 8 symboles résolus (load_sync_cache, save_sync_cache, sync_project_directives, sync_open_questions, sync_sprint_backlog, sync_live_reference_wikis, sync_hypergraph, run_sync)
- [x] ADR-0369 : 1 appel réseau (`subprocess.run`), 1 avec `timeout=8`
- [x] Suite tests : 1380 PASSED / 0 FAILED / 0 regressions
- [x] Fichier original `src/pipelines/sync.py` shadowed par le package (aucune suppression nécessaire)
- [x] Plan archivé : `memory/plan/implementation_plan_MLOOP-179-BE.md`
- [x] EvidencePack : `memory/evidence/MLOOP-179-BE_evidence.json`
- [x] Sidecar statut : `Projects/mLoop/memory/worker_MLOOP-179-BE.status`

---

## §5. Fichiers Créés/Modifiés

| Fichier | Action | Lignes | Ko |
|:---|:---|:---|:---|
| `src/pipelines/sync/__init__.py` | CRÉÉ | 63 | 1.9 |
| `src/pipelines/sync/_sync_docs.py` | CRÉÉ | 298 | 11.6 |
| `src/pipelines/sync/_sync_graph.py` | CRÉÉ | 199 | 8.0 |
| `src/pipelines/sync/_sync_run.py` | CRÉÉ | 213 | 7.6 |
| `src/pipelines/sync.py` | INCHANGÉ (shadowed par le package) | 542 | 23.2 |

---

## §6. Rollback BR=10

BR=10 < 20 → autonomie worker (macro Q3). Si smoke FAIL : `git checkout src/pipelines/sync.py` et suppression du répertoire `src/pipelines/sync/`. Non déclenché — tous les checks verts.
