---
created: 2026-09-24T14:51:54.105Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, mloop-176-be]
---

[[Plannotator Plans]]

# Plan d'Implémentation — MLOOP-176-BE : Extraction Modulaire de `src/converters/svg_to_md.py`

> Protocole : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` (Cas général §2)
> Story : MLOOP-176-BE (EPIC-17) · READY_FOR_DEV · Grill DONE (Q1-A) · Approuvé humain
> Criticité Plan-First : **Niveau 3** (touche cœur mLoop `src/`, 7 couches ADR-0376) → plan bloquant

---

## §0 Baseline vérifiée (faits établis, pas d'hypothèses)

| Fait | Valeur | Preuve |
|:--|:--|:--|
| Source | `src/converters/svg_to_md.py` = **991 L / 38 720 o** | `code-check --file` → FAIL RULE-AST-01 (2 violations) |
| Tests SVG baseline | **13 PASS** (`test_svg_spatial_parser.py` + `test_svg_ocr_bridge.py`) en 0.13s | `pytest` ciblé |
| Callers (BR=2, lazy) | `ingest_file_processors.parse_svg` L30 → `parse_svg_to_md_text` ; `ingest_indexers.generate_maquettes_index` L152 → `generate_maquettes_index` | grep AST |
| OCR déjà séparé | `svg_ocr_bridge.py` (242 L) — zéro couplage à réintroduire | Read intégral |
| Effets de bord import | AUCUN (`logger = get_logger()` L19 seulement) — pas de `_svg_init_effects.py` (Q2) | Read intégral |
| **Piège de test critique** | `test` L114/L142 patchent `src.converters.svg_to_md.ocr_vectorized_svg` | grep tests |

### Résolution du piège de patch (validé empiriquement avant plan)
Un probe isolé a prouvé que `patch('<shim>.dep')` atteint une fonction extraite **si** celle-ci résout la dépendance par **lookup dynamique paresseux** : `import src.converters.svg_to_md as _md; _md.ocr_vectorized_svg(...)`. Résultat probe = `MOCKED`. → Les tests restent **inchangés**.

---

## §1 Familles de responsabilités (découpe Q1-A, 5 modules)

| Module cible | Symboles (lignes source) | Est. |
|:--|:--|--:|
| `_svg_models.py` | `UIElement` (22-35) + `compute_svg_path_bbox_accurate` (38-186) | ~170 L |
| `_svg_parser_core.py` | `SvgSpatialParserCore` : `__init__`, `parse`, `_parse_transform`, `_traverse_node`, `_fallback_regex_parse` (195-248, 250-265, 267-442, 660-672) | ~255 L |
| `_svg_parser_classify.py` | `ParserClassifyMixin` : `_associate_and_classify`, `_classify_outlined_svg` (444-658) | ~235 L |
| `_svg_output.py` | `generate_ascii_wireframe` (675-753), `parse_svg_to_md_text` (756-906, **OCR via lookup paresseux**), `convert_svg_file_to_md` (956-991) | ~270 L |
| `_svg_index.py` | `generate_maquettes_index` (909-953) | ~55 L |
| `__init__.py` | `class SvgSpatialParser(SvgSpatialParserCore, ParserClassifyMixin): pass` + `__all__` + ré-exports (dont `ocr_vectorized_svg`) | ~30 L |
| `svg_to_md.py` | SHIM : `from src.converters.svg_to_md import *  # noqa: F401,F403` | ≤5 L |

**Assemblage mixin (décision Q1-A)** : `SvgSpatialParserCore` porte parse/traverse ; `ParserClassifyMixin` porte les 2 classifieurs ; `SvgSpatialParser(Core, Mixin)` recompose l'API publique **identique** (les tests instancient `SvgSpatialParser(...)`).

---

## §2 Étapes d'exécution (ordre déterministe)

1. `git mv src/converters/svg_to_md.py` → sauvegarde mentale ; créer `src/converters/svg_to_md/` (package).
2. Créer `_svg_models.py` (imports : `re`, `dataclasses`, `typing`).
3. Créer `_svg_parser_core.py` (importe `UIElement`, `compute_svg_path_bbox_accurate` depuis `._svg_models` ; classe `SvgSpatialParserCore`).
4. Créer `_svg_parser_classify.py` (importe `UIElement` ; classe `ParserClassifyMixin`).
5. Créer `_svg_output.py` (importe `UIElement`, `SvgSpatialParser` depuis `.` ; `parse_svg_to_md_text` appelle OCR via `import src.converters.svg_to_md as _md; _md.ocr_vectorized_svg(...)`).
6. Créer `_svg_index.py`.
7. Créer `__init__.py` : recompose `SvgSpatialParser`, ré-exporte tous les symboles publics **+ `ocr_vectorized_svg`** (depuis `svg_ocr_bridge`) pour préserver la cible de patch, définit `__all__`.
8. Écrire le shim `svg_to_md.py` (5 L).
9. `python -m src.pipelines.import_smoke_check --module src/converters/svg_to_md.py` → VERT.
10. `code-check --file` sur les 6 fichiers du package → tous PASS (≤300 L / 15 Ko).
11. `pytest tests/test_svg_spatial_parser.py tests/test_svg_ocr_bridge.py -q` → **13 PASS** (zéro régression).
12. Contrôle non-régression élargi via **worker délégué** (suite complète `pytest tests/` dépasse 120s sur thread principal — Délégation Gate critère Durée) → N_après ≥ N_avant.

---

## §3 ADR-0369 (vérifié par construction — code déplacé, non réécrit)
- Accès fichiers : `read_text`/`write_text`/`with open` déjà conformes (déplacés tels quels).
- `subprocess` avec `timeout` : réside dans `svg_ocr_bridge.py` (hors périmètre, déjà conforme).
- Zéro `except Exception: pass` nu : tous les `except` portent `logger.debug/warning(exc_info=True, extra={...})` (préservés).

## §4 Livrables
- 6 fichiers package + 1 shim (code déplacé, **zéro changement comportemental**).
- `memory/plan/implementation_plan_MLOOP-176-BE.md` (ce plan archivé + résultats §6).
- `memory/evidence/MLOOP-176-BE_evidence.json` (EvidencePack).
- `memory/evidence/MLOOP-176-BE_fact_dossier.md` (dossier de preuves).
- MAJ `memory/evidence/epic17_prioritization_matrix.md` (Rang #23 → DONE).
- MAJ `backlog/sprint_backlog.md` : MLOOP-176-BE → **DONE_TESTED**.

## §5 Périmètre & garde-fous respectés
- ❌ NE touche PAS : MLOOP-190→194 (EPIC-19), w1:p1/p3C/p3D/p3E.
- 🚫 Zéro écriture Jira (moratoire PO).
- Push : `Projects/mLoop` → `git push origin HEAD:project-mLoop` uniquement (racine seulement si hooks/blueprints requis — non prévu ici).
- TDD : les tests existants SONT le harnais de non-régression (aucun nouveau test requis, refactoring pur ; couverture Q4 confirmée).
- Hooks : `MLOOP_SKIP_HOOKS` NON utilisé (le garde-fou autorise la baisse de lignes).

## §6 Résultats post-extraction (à compléter à l'exécution)
| Métrique | Avant | Après |
|:--|--:|--:|
| Lignes module source | 991 | ≤5 (shim) |
| Lignes max sous-module | — | (cible ≤270) |
| Tests SVG PASS | 13 | (cible 13) |
| Violations RULE-AST-01 | 2 | (cible 0) |
| Fumée imports | — | (cible ✅) |