# Plan de Build Consolidé — Phase 3 : 15 Récits (EPIC-26 + EPIC-30 + EPIC-32)

## 0. Diagnostic Pré-Build & Risques Identifiés

### État réel du code vs récits
| Épopée | Récits | Code existant | Verdict |
|--------|--------|---------------|----------|
| **EPIC-26** | 5 récits | ~80% déjà implémenté (bridge, rules_mirror, circuit-breaker, Plan/Act) | **Complétion + CLI manquant** |
| **EPIC-30** | 5 récits | 0% (aucun fichier cœur n'existe) | **Création pure** |
| **EPIC-32** | 5 récits | ADR-0393 acceptée, 0% code (aucune garde mécanique) | **Création + refactoring** |

### Risques bloquants ADR-0202 (plafond 300L)
| Fichier | Lignes actuelles | Impact | Action requise |
|---------|:---:|--------|----------------|
| `state_machine.py` | 642 | EPIC-32 (322) | Extraction `_fsm_authority.py` |
| `herdr_worker_core.py` | 418 | EPIC-26 (262,263) | Extraction `_plan_act_guard.py` |
| `_vc_governance.py` | 296 | EPIC-30+32 (check_27, check_28) | Nouveau sous-module `_vc_artifact.py` |
| `_engine.py` | 297 | EPIC-32 (322) | Extraction `_grill_guards.py` |
| `vibe_check/__init__.py` | 286 | EPIC-30+32 | Serré mais absorbable (~+8L d'imports) |

---

## 1. Stratégie de Parallélisation (3 Workers Herdr)

```
┌─────────────────────────────────────────────────────────┐
│ Worker A (EPIC-26)  │ Worker B (EPIC-30)  │ Orchestrateur │
│ Cline Ecosystem     │ Multimodal Artifacts│ EPIC-32       │
│ (Complétion)        │ (Création pure)     │ (Séquentiel)  │
│                     │                     │               │
│ 260+261+262+263+264 │ 300+301+302+303+304 │ 320→321→322   │
│ ~2h                 │ ~3h                 │ →323→324      │
│                     │                     │ ~4h           │
└─────────────────────────────────────────────────────────┘
        ↓ Harvest A         ↓ Harvest B        ↓ Séquentiel
        └──────────────┬────────────────────────┘
                       ↓
              Intégration Finale
              (vibe_check/__init__.py : check_27+28)
              guide --sync (parité CLI)
              pytest complet (suite globale)
              Commit & Push
```

---

## 2. Worker A — EPIC-26 Cline Ecosystem (5 récits)

### Constat : code largement existant
- `MemoryBankBridge` (256L) → MLOOP-260-BE : **DÉJÀ IMPLÉMENTÉ** avec tests
- `ClineRulesMirror` (82L) → MLOOP-261-BE : **DÉJÀ IMPLÉMENTÉ** avec tests
- Plan/Act guard dans `herdr_worker_core.py` → MLOOP-262-BE : **PARTIELLEMENT IMPLÉMENTÉ**
- Circuit-Breaker dans `herdr_worker_core.py` → MLOOP-263-BE : **PARTIELLEMENT IMPLÉMENTÉ**
- Commande CLI `cline-sync` → MLOOP-264-FULL : **MANQUANT**

### Fichiers à créer/modifier
| Action | Fichier | Récit(s) | Lignes |
|--------|---------|----------|--------|
| `[NEW]` | `src/commands/handlers/cline_sync.py` | 264 | ~150L |
| `[NEW]` | `src/core/_plan_act_guard.py` | 262,263 | ~120L |
| `[MODIFY]` | `src/core/herdr_worker_core.py` | 262,263 | Extraction → import |
| `[MODIFY]` | `src/bridges/cline/memory_bank_bridge.py` | 260 | Ajout `harvest_cline_notes()` complet |
| `[MODIFY]` | `src/bridges/cline/rules_mirror.py` | 261 | Ajout `verify_parity()` |
| `[MODIFY]` | `src/commands/_registry/_reg_analysis_ext.py` | 264 | +`cline-sync`, `cline-status` |
| `[MODIFY]` | `src/pipelines/guide_data.py` | 264 | +2 entrées |
| `[MODIFY]` | `tests/test_cline_bridge.py` | 260,261 | Compléter coverage |
| `[MODIFY]` | `tests/test_herdr_circuit_breaker.py` | 262,263 | +test format/scope |

---

## 3. Worker B — EPIC-30 Multimodal Artifacts (5 récits)

### Constat : création pure, ordre imposé par dépendances
300 (gate) → 301 (connectors) → 302 (ORBIT) → 303 (decoupler) → 304 (CLI + check_27)

### Fichiers à créer/modifier
| Action | Fichier | Récit(s) | Lignes |
|--------|---------|----------|--------|
| `[NEW]` | `src/pipelines/artifact_gate.py` | 300 | ~200L |
| `[NEW]` | `src/pipelines/connector_validator.py` | 301 | ~180L |
| `[NEW]` | `src/pipelines/orbit_caption_harvester.py` | 302 | ~200L |
| `[NEW]` | `src/pipelines/audit_decoupler.py` | 303 | ~150L |
| `[NEW]` | `src/commands/handlers/artifact_check.py` | 304 | ~200L |
| `[NEW]` | `src/pipelines/vibe_check/_vc_artifact.py` | 304 | ~150L (check_27) |
| `[MODIFY]` | `tools/archify/archify_runner.py` | 301 | +validation topologique |
| `[MODIFY]` | `src/pipelines/ingest_file_processors.py` | 302 | +hook ORBIT |
| `[MODIFY]` | `src/commands/_registry/_reg_analysis_ext.py` | 304 | +`artifact-check` |
| `[MODIFY]` | `src/pipelines/vibe_check/__init__.py` | 304 | +import check_27 |
| `[MODIFY]` | `src/pipelines/guide_data.py` | 304 | +1 entrée |
| `[NEW]` | `tests/test_artifact_harness.py` | 300-304 | ~250L |

---

## 4. Orchestrateur — EPIC-32 Grill Modality (5 récits, séquentiel)

### Constat : séquentiel strict (320→321→322→323→324)
- 320 = normative (standards/protocols/AGENTS.md) — PAS de code Python
- 321 = refonte skill grill (SKILL.md) — PAS de code Python
- 322 = gardes mécaniques FSM + GrillEngine — CODE PYTHON
- 323 = Check 28 + CLI --format/--scope — CODE PYTHON
- 324 = tests Pytest + guide --sync — CODE PYTHON + DOCS

### 4A. MLOOP-320-BE (Normative — thread principal)
| Action | Fichier |
|--------|---------|
| `[MODIFY]` | `standards/adr-system/0393-*.md` (ajustements si nécessaire) |
| `[MODIFY]` | `standards/protocols/STORY_LIFECYCLE_PROTOCOL.md` (+arrêt post-grill, mandat unitaire) |
| `[MODIFY]` | `AGENTS.md` (+orthogonalité Format×Scope, interdit auto-promo) |
| `[MODIFY]` | `standards/adr-system/0320-*.md` (§F restriction avancement auto) |

### 4B. MLOOP-321-BE (Skill refonte — thread principal)
| Action | Fichier |
|--------|---------|
| `[MODIFY]` | `.agents/skills/grill/SKILL.md` (matrice 2×2, table anti-rationalisation) |
| `[MODIFY]` | `tools/export/grill-with-docs-kit/SKILL.md` (miroir) |
| `[MODIFY]` | `docs/01-architecture/framework/grill_with_docs_protocol.md` (diagramme Mermaid) |

### 4C. MLOOP-322-BE (Gardes mécaniques — worker-spawn)
| Action | Fichier | Lignes |
|--------|---------|--------|
| `[NEW]` | `src/pipelines/_fsm_authority.py` | ~120L (LifecycleAuthorityError + validate_gate2) |
| `[NEW]` | `src/pipelines/grill/_grill_guards.py` | ~80L (assert_no_story_mutation) |
| `[MODIFY]` | `src/pipelines/state_machine.py` | Import + delegation vers _fsm_authority |
| `[MODIFY]` | `src/pipelines/grill/_engine.py` | Import _grill_guards, bridage mark_story_grilled |
| `[MODIFY]` | `src/pipelines/grill/_cli_handler.py` | Journal violations |

### 4D. MLOOP-323-BE (Check 28 + CLI — worker-spawn après 322)
| Action | Fichier | Lignes |
|--------|---------|--------|
| `[NEW]` | `src/pipelines/vibe_check/_vc_cascade.py` | ~150L (check_28) |
| `[MODIFY]` | `src/pipelines/vibe_check/__init__.py` | +import check_28 |
| `[MODIFY]` | `src/commands/_registry/_reg_pipelines_arch.py` | +--format, +--scope |
| `[MODIFY]` | `src/pipelines/grill/_cli_handler.py` | +parsing format/scope |
| `[MODIFY]` | `src/pipelines/guide_data.py` | +entrées format/scope |

### 4E. MLOOP-324-FULL (Tests + guide — worker-spawn après 323)
| Action | Fichier | Lignes |
|--------|---------|--------|
| `[NEW]` | `tests/test_grill_modality_decoupling.py` | ~250L (6 scénarios) |
| `[MODIFY]` | `src/pipelines/guide_data.py` | Parité finale |
| `[MODIFY]` | `standards/protocols/CLI_PIPELINE_GUIDE.md` | guide --sync |

---

## 5. Intégration Finale (Orchestrateur, post-harvest de tous les workers)

1. `pytest tests/ -q` — suite globale complète (objectif : 0 FAIL)
2. `python src/swarm.py vibe-check --project mLoop` — 28+ checks (objectif : 0 FAIL)
3. `python src/swarm.py guide --sync` — parité CLI
4. `python src/swarm.py struct-check --project mLoop` — C13 BLOCKING
5. Promotion des 15 récits via `set_story_status()` → DONE_TESTED
6. Commit isolé framework (`C:\Memory Loop`) + projet (`Projects/mLoop`)
7. Push framework + projet
8. `python src/swarm.py sync --project mLoop`

---

## 6. Périmètre d'Écriture des Workers (CA-7)

| Worker | Peut écrire | Ne peut PAS écrire |
|--------|-------------|--------------------|
| Worker A (EPIC-26) | `src/**, tests/**, .clinerules/**` | `backlog/**, standards/**, AGENTS.md, memory/**` |
| Worker B (EPIC-30) | `src/**, tests/**, tools/archify/**` | `backlog/**, standards/**, AGENTS.md, memory/**` |
| EPIC-32 (322-324) | `src/**, tests/**` | `backlog/**, standards/** (sauf via 320/321 sur main)` |

---

## 7. Budget Estimé

| Épopée | Fichiers NEW | Fichiers MODIFY | Taille estimée | Durée |
|--------|:---:|:---:|:---:|:---:|
| EPIC-26 | 2 | 7 | ~800L net | ~2h |
| EPIC-30 | 7 | 5 | ~1500L net | ~3h |
| EPIC-32 | 4 | 12 | ~1200L net | ~4h |
| **Intégration** | 0 | 3 | ~50L | ~30min |
| **TOTAL** | **13 NEW** | **27 MODIFY** | **~3550L** | **~5h (parallélisé)** |

---

## 8. Ordonnancement d'Exécution

1. **T0** : Lancer Worker A (EPIC-26) et Worker B (EPIC-30) en parallèle via Herdr
2. **T0** : Exécuter MLOOP-320-BE (normative) et MLOOP-321-BE (skill) sur thread principal
3. **T1** (~320+321 terminés) : Lancer Worker C pour MLOOP-322-BE (gardes FSM)
4. **T2** (harvest Worker C) : Lancer Worker D pour MLOOP-323-BE (Check 28 + CLI)
5. **T3** (harvest Worker D) : Lancer Worker E pour MLOOP-324-FULL (tests + guide)
6. **T4** (harvest A+B+E) : Intégration finale, suite complète, commit, push

---

## 9. Modèle LLM pour les Workers

Conformément à l'autorisation de l'utilisateur de basculer sur des modèles gratuits/optimaux :
- **Workers A & B** (création parallèle) : `opencode` avec modèle courant ou free si quota atteint
- **Workers 322/323/324** (séquentiel) : idem
- **Thread principal** (320/321 normative + intégration) : modèle courant (Opus)

---

**Approbation requise avant lancement.**