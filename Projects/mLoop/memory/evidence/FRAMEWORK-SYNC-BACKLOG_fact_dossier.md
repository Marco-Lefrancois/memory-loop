# Fact Dossier — FRAMEWORK-SELFDEV-SYNC-BACKLOG

**Date** : 2026-09-24
**Type** : Framework Self-Dev (mLoop auto-development)
**ADR** : ADR-0376 (Ecosystem Rigor), ADR-0369 (Robustesse), ADR-0202 (Taille modules), ADR-0307 (Archivage plans)

---

## 1. Source de vérité canonique

| Source | Rôle |
| :--- | :--- |
| `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md` | Protocole 7 couches / 4 étapes |
| `standards/blueprints/plan_template.md` | Gabarit plan formel |
| Plan approuvé : `ralignement-ssot-du-sprint-bac-2026-09-24-approved.md` | SSOT du périmètre exécuté |
| `Projects/mLoop/backlog/sprint_backlog.md` | SSOT des statuts stories |

---

## 2. Fait établi : code mort sync.py

**Extrait** — Analyse froide Étape 1 : `src/pipelines/sync.py` (542 L) est entièrement masqué par le package `src/pipelines/sync/` (`import src.pipelines.sync` résout vers `sync/__init__.py`, prouvé par smoke test). Zéro importeur fonctionnel. Seule référence documentaire = `PHASE_FILES_AND_TEST_PLAN.md` L215 (repointée vers le package).

---

## 3. Fait établi : mocks inertes

`run_sync` (`_sync_run.py`) lie `sync_sprint_backlog` etc. par import direct local. Les tests patchaient `src.pipelines.sync.<fn>` = re-export du `__init__.py` → interception nulle. Les tests passaient par accident (no-op sur `tmp_path` vide). Cibles corrigées : `src.pipelines.sync._sync_run.<fn>` (10 cibles : 5 ×2 blocs resilience + 5 ×2 blocs logging).

---

## 4. Fait établi : parsing non colonne-aware

Ancien `re.search` sur la ligne entière capturait le 1er token status même dans un titre (preuve : titre contenant « READY_FOR_DEV » avec Statut=DRAFT → faux positif). Vocabulaire incomplet : `DONE_TESTED`, `DRAFT`, `TOMBSTONE` absents.

---

## 5. Structure backlog (6 tables, schémas variables)

- L23/L42/L54 : 7 col sans Grill-me (Statut idx 5)
- L68/L85 : 8 col avec Grill-me (Statut idx 6)
- L99 : 7 col (Statut idx 5)

Parser = détection en-tête via séparateur `|---|` + `_find_statut_col_index()` ; `split("|")` sans filtrage vides (stabilité des indices).

---

## 6. Matrice de résolution des conflits

| Conflit | Résolution | Autorité |
| :--- | :--- | :--- |
| ADR-0202 300 L vs fix inline | Extraction `_sync_backlog_parser.py` | ADR-0202 |
| FAIT/PENDING dans vocab ? | NON (colonne Grill-me) | Décision prompt §1 |
| DONE_TESTED ordre regex | Avant DONE | Évite ambiguïté |
| test_archify FAIL | Hors périmètre, préexistant | Scope plan |
| Réf sync.py L215 | Repointée vers package | Plan §3 |

---

## 7. Contrats déclaratifs cibles

- **Aucun changement de signature API** : `sync_sprint_backlog(project_name, project_path) -> None` inchangé.
- **Aucun payload synthétique** : parser lit le vrai `sprint_backlog.md`.

---

## 8. Frontière active & Admission of Limits

- Graphify `update` SKIPPED (non disponible PATH worker) — non bloquant, AST-only.
- Suite large : 1 FAIL `test_archify` préexistant (timeout subprocess) — hors périmètre, non corrigé.
- Rénumérotation ADR-0342 et normalisation MLOOP-205-BE : HORS PÉRIMÈTRE (dettes séparées).

---

## 9. Vérifications finales (Triple Gate)

| Gate | Résultat |
| :--- | :--- |
| A1 baseline 10/10 | PASS |
| A2 nouveaux 10/10 | PASS |
| A3 import smoke | PASS |
| A6 suite ciblée 20/20 | PASS |
| ADR-0202 _sync_docs | 269 L ≤ 300 |
| git commit/push | NONE CONFIRMED |
