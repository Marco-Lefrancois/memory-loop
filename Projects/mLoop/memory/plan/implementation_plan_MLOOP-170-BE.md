# Plan d'Implémentation — MLOOP-170-BE

**Récit** : Récit Pilote — Refactoring Modulaire de vibe_check.py (880L → <300L/module)
**Statut** : DONE_TESTED (2026-09-23)
**Épic** : EPIC-17-MODULAR-REFACTORING
**FRAMEWORK_STATE lu** : 2026-09-23 (baseline commits OK, pas de certificat NLI obsolète pertinent)

---

## §1 Status source vérifié
- Frontmatter : `status: DONE_TESTED`, `invest_score: 6/6`, `grill_me: DONE`, `blocked_by: []` (MLOOP-171-BE retiré — OQ-170-02 a autorisé le démarrage immédiat, le pilote est livré).

## §2 Certificat NLI daté
- Non applicable (refactoring purement structurel, pas d'évolution NLI). Pas d'invalidation.

## §3 Corrections / Dette identifiée
- **Gate 3 ADR-0381 non scellé** : le code a été livré avant le scellement Red/Green. `tdd-enforce --phase red` échouerait (`UnexpectedPassingTestError` — tests déjà verts). Traitement : exemption legacy documentée (cf. §6), pas de dette séparée.
- **FSM enum/protocole** : `DONE_TESTED` absent de `StoryStatus` enum alors qu'utilisé par le protocole et MLOOP-160→165 — ticket séparé (hors périmètre).

## §4 Livrables physiques
| Artefact | État |
|---|---|
| `src/pipelines/vibe_check.py` (shim 5L) | ✅ Created/Modified |
| `src/pipelines/vibe_check/__init__.py` (239L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_agents.py` (121L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_build.py` (103L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_frontend.py` (68L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_governance.py` (245L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_project.py` (74L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_security.py` (98L) | ✅ Created |
| `src/pipelines/vibe_check/_vc_ssot.py` (131L) | ✅ Created |
| `tests/vibe_check/{agents,ssot,security,project,governance,build,frontend}_test.py` | ✅ 7 fichiers, 73 tests PASS |
| `pyproject.toml` `python_files` += `*_test.py` | ✅ Modified |
| `Projects/mLoop/backlog/stories/MLOOP-170-BE.md` | ✅ DONE_TESTED |
| `Projects/mLoop/backlog/sprint_backlog.md` | ✅ Synced |

## §5A Vérifications (Gate C12 inclus)
- [x] `struct-check` : modules package <300L (max `_vc_governance` 245L)
- [x] `verification_harness` non vide : 4 scénarios VERIFIED (Sentinel_ReadOnly)
- [x] Transition status : DONE_TESTED (protocole) — humain approuvé « 3.oui » 2026-09-23
- [x] Suite complète : **1306 passed, 1 skipped** (237s)
- [x] Tests miroirs OQ-170-04 : **73 passed**
- [x] `run_vibe_check` signature + import smoke OK
- [ ] `tdd-enforce --phase green` : Gate 3 non scellé (legacy — cf. §3)

## §6 Exemptions & Arbitrages
1. **Gate 3 Red/Green (ADR-0381)** : travail antérieur au scellement sur ce récit. Les 4 piliers Gherkin sont VERIFIED par Sentinel. Exemption legacy documentée ici — même traitement que « legacy EPIC 10→17 exempté (warning) » (EPIC-18).
2. **blocked_by MLOOP-171-BE retiré** : OQ-170-02 (découplage EPIC-16, démarrage immédiat) + pilot livré.
3. **invest_score 0/6 → 6/6** : INVEST réévalué après livraison (Indépendant, Valeur, Estimable, Small, Testable — tous satisfaits).

## §7 Next
- Commit Git (hors session, non demandé)
- Avancer P3 (MLOOP-152-BE) / P5 (MLOOP-171→172) selon priorité PO
