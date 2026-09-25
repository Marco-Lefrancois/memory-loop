# Plan d'Extraction Modulaire — src/converters/svg_to_md.py

> **Protocole** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` (Cas général §2)
> **Story** : MLOOP-176-BE (EPIC-17-MODULAR-REFACTORING)
> **Date** : 2026-09-24
> **Statut** : DONE
> **Audit** : ADR-0376 (7 couches) · ADR-0352 (FRAMEWORK_STATE lu) · ADR-0369 · ADR-0202
> **Approbation** : plan approuvé via Plannotator 2026-09-24 (`plan-dimplmentation-mloop-176--2026-09-24-approved.md`)

---

## Pré-requis FRAMEWORK_STATE (ADR-0352)

1. **Status source vérifié** ✅ — frontmatter lu : `status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6.
2. **Certificat NLI daté** ✅ N/A — aucun certificat NLI émis pour ce récit (gabarit extraction MLOOP-172-BE : pas de gate NLI). FRAMEWORK_STATE régénéré : entrée changelog `2026-09-24 — Extraction modulaire svg_to_md` ajoutée (post-build, ADR-0352 §6).
3. **`struct-check` dans §5A** ✅ — exécuté avant clôture (Gate C12 Domain Sanity).
4. **`verification_harness` non vide** ✅ — 4 scénarios Gherkin (preuves runtime en §5 du protocole / probes §5B).
5. **Transition d'état valide** ✅ — `READY_FOR_DEV` → `IN_DEV` → `DONE_TESTED` conforme state machine (Gate C9+C12).

---

## §1 Module Source & Callers

| Champ | Valeur |
|:------|:-------|
| Chemin source | `src/converters/svg_to_md.py` |
| Lignes avant extraction | 991 L |
| Ko avant extraction | 37.8 Ko (38 720 o) |
| Blast Radius (callers) | 2 fichiers (lazy imports) |
| Méthode BR | ast_import_count |
| Lot EPIC-17 | Lot 3 (rang #23, dégelé 2026-09-23) |

**Callers identifiés** (INTACTS — jamais modifiés) :
- `src/pipelines/ingest_file_processors.py:30` → `parse_svg_to_md_text`
- `src/pipelines/ingest_indexers.py:152` → `generate_maquettes_index`

**Consommateurs de surface** (lecture seule, non-régression) :
- `tests/test_svg_spatial_parser.py` — imports + **monkeypatch `src.converters.svg_to_md.ocr_vectorized_svg`** (L114, L142)
- `tests/test_svg_ocr_bridge.py` — pont OCR (hors périmètre)

**Baselines (Étape 0, exécutées)** :
- `code-check --file src/converters/svg_to_md.py` → **FAIL**, 991 L, 38 720 o, 2 violations RULE-AST-01
- `pytest tests/ -q` → **1395 PASS / 1 FAIL** en 248 s — FAIL = `test_utils_latency::test_resolve_story_query_latency` (pré-existant, flaky, re-passe solo 0.17 s)

---

## §2 Familles de Responsabilités (décision grill Q1-A : 5 modules + mixin)

| Famille | Symboles (plages L.) | Sous-module cible | Lignes estimées |
|:--------|:---------------------|:------------------|:----------------|
| Modèles & géométrie | `UIElement` (L22-36), `compute_svg_path_bbox_accurate` (L38-187) | `_svg_models.py` | ~181 L |
| Parseur cœur | `SvgSpatialParserCore` : `__init__` (L195), `parse` (L204), `_parse_transform` (L250), `_traverse_node` (L267-443) + assemblage `SvgSpatialParser` | `_svg_parser_core.py` | ~270 L |
| Classification (mixin) | `ParserClassifyMixin` : `_associate_and_classify` (L444), `_classify_outlined_svg` (L512), `_fallback_regex_parse` (L660-674) | `_svg_parser_classify.py` | ~249 L |
| Sortie Markdown | `generate_ascii_wireframe` (L675), `parse_svg_to_md_text` (L756), `convert_svg_file_to_md` (L956-991) + wrapper OCR | `_svg_output.py` | ~297 L ⚠️ |
| Index maquettes | `generate_maquettes_index` (L909-955) | `_svg_index.py` | ~53 L |

**Contingence pré-autorisée** (ADR-0202 absolu > nombre de modules) : si `_svg_output.py` ≥ 300 L / 15 Ko → extraire `generate_ascii_wireframe` (L675-754, ~80 L) dans `_svg_wireframe.py` (6ᵉ module, output → ~217 L).

**Règles critiques** :
1. **Surface de patch OCR** : `__init__.py` ré-exporte `ocr_vectorized_svg` ; `_svg_output.py` appelle via wrapper à résolution dynamique `from src.converters import svg_to_md as _pkg` au niveau fonctionnel (Red/Green : les 2 tests OCR échouent si binding statique).
2. **Assemblage MRO** : `class SvgSpatialParser(ParserClassifyMixin, SvgSpatialParserCore)` en bas de `_svg_parser_core.py` ; le mixin n'importe jamais le core (zéro cycle).
3. **Logger** : `get_logger("converters.svg_to_md")` idempotent par sous-module (même instance, handlers non dupliqués).
4. **Shim** : package l'emporte sur module fichier (précédent `state/`, `lifecycle/`, `_registry/`) ; shim style MLOOP-174 (`lifecycle.py`) : docstring MASQUÉ + imports nommés + `__all__`.
5. **ADR-0369** : déplacement pur — zéro nouvelle règle, code-check AST vert.

---

## §3 Cas Spécial Applicable

- [ ] Registre déclaratif → voir §3.1 du protocole
- [ ] Singleton d'état → voir §3.2 du protocole
- [ ] Effets de bord à l'import → voir §3.3 du protocole
- [x] Aucun cas spécial (découpe standard §2) — getters/setters + mixins, pas d'import side-effect critique

---

## §4 Livrables Physiques

| Artefact | Action | Lignes | Statut |
|:---------|:-------|-------:|:-------|
| `src/converters/svg_to_md.py` | SHIM (ré-export) | 4 L | ☑ |
| `src/converters/svg_to_md/__init__.py` | NEW | 49 L | ☑ |
| `src/converters/svg_to_md/_svg_models.py` | NEW | 178 L | ☑ |
| `src/converters/svg_to_md/_svg_parser_core.py` | NEW | 287 L | ☑ |
| `src/converters/svg_to_md/_svg_parser_classify.py` | NEW | 231 L | ☑ |
| `src/converters/svg_to_md/_svg_output.py` | NEW | 298 L | ☑ |
| `src/converters/svg_to_md/_svg_index.py` | NEW | 57 L | ☑ |
| `(_svg_wireframe.py)` | contingence NEW | ~80 L | ☐ (non requise) |
| `Projects/mLoop/memory/plan/implementation_plan_MLOOP-176-BE.md` | NEW (ce fichier) | — | ☑ |

**Intouchables absolus** : `tests/**` (0 fichier), `src/pipelines/ingest_file_processors.py`, `src/pipelines/ingest_indexers.py`, `src/converters/svg_ocr_bridge.py`, EPIC-19 (190-194), panneaux `w1:*`, Jira (moratoire).

---

## §5 Checklist Non-Régression

```
PRÉ-EXTRACTION
[x] code-check --file src/converters/svg_to_md.py : 2 violations (991 L / 38 720 o) — baseline
[x] pytest tests/ -q --tb=no : 1395 PASS / 1 FAIL (flake latency pré-existant, solo OK)
[x] Callers : 2 identifiés (ingest_file_processors, ingest_indexers)

EXTRACTION
[x] Sous-modules créés, chacun ≤300 L / ≤15 Ko (code-check --file × 7 : tous PASS — max 298 L)
[x] Shim de ré-export créé (991 L → 4 L, star-import résolu via `__all__` du package)
[x] __init__.py expose tous les symboles publics + ocr_vectorized_svg (10 symboles vérifiés)
[x] Aucun import circulaire (python -c "import src.converters.svg_to_md" → OK)

POST-EXTRACTION
[x] check fumée : python -m src.pipelines.import_smoke_check --module src/converters/svg_to_md.py → VERT (7 callers, aucun symbole non résolu)
[x] code-check --file sur chaque sous-module : PASS (7/7 — max 298 L `_svg_output.py`, contingence `_svg_wireframe.py` NON nécessaire)
[x] pytest tests/test_svg_spatial_parser.py tests/test_svg_ocr_bridge.py -q : 13/13 PASS (dont les 2 tests patch OCR `ocr_vectorized_svg` — mécanisme lookup dynamique paresseux validé)
[x] pytest tests/ -q --tb=no (délégué worker_mloop_176_be, w1:p3K) : **1403 PASS / 1 FAIL en 251.39s** — le FAIL (`test_resolve_story_query_latency`, dépassement micro 5.005ms > seuil 5.0ms) est **identique** au FAIL baseline pré-extraction (1395 PASS/1 FAIL), zéro nouvelle régression, N_après (1403) ≥ N_avant (1395)
[x] Probes runtime (Piliers 3-4) : couverts par la suite verte (tests SVG corrompu/fallback + SVG vierge inclus dans les 13 PASS)
[x] git diff borné : uniquement src/converters/svg_to_md* (7 nouveaux fichiers package + shim réécrit) — zéro tests/, zéro callers/ modifiés
[x] MLOOP_SKIP_HOOKS non utilisé
[x] struct-check story (Gate C12) — statut source vérifié READY_FOR_DEV en préambule
[x] Plan archivé mis à jour → DONE
```

---

## §6 Résultats Post-Extraction

| Métrique | Avant | Après |
|:---------|------:|------:|
| Lignes module source | 991 L (38 720 o) | 4 L (shim) |
| Lignes max sous-module | 991 L | 298 L (`_svg_output.py`) |
| Tests SVG ciblés PASS | 13 | 13 (0 régression, dont 2 tests patch OCR) |
| Tests suite complète PASS | 1395 (+1 FAIL flaky pré-existant) | **1404 PASS / 0 FAIL** (re-run orchestrateur, 257s — flaky non reproduit) · 1403+1 FAIL flaky (worker, 251s) |
| Violations RULE-AST-01 | 2 | 0 (7/7 modules PASS) |
| Fumée imports | — | ✅ VERT (7 callers résolus) |
| Callers réels (`ingest_file_processors`, `ingest_indexers`) | intacts | intacts, résolus à l'exécution |

**Statut final** : **DONE** — extraction complète, zéro régression, worker de vérification harvesté et fermé (`worker_mloop_176_be`, w1:p3K).

### Clôture gouvernance (post-vert)
1. ✅ EvidencePack enrichi (harvest worker + résultats build)
2. ✅ fact_dossier §6 Résultats Build ajouté
3. ✅ Matrice EPIC-17 L43 → DONE_TESTED
4. ✅ sprint_backlog L31 → DONE_TESTED
5. ✅ Workers MLOOP-176 fermés (zéro zombie) : `worker_176`@wA:p1 + `worker_mloop_176_be`@w1:p3K — vérifié par `worker-status` (aucun résidu ; panneaux `w1:p1/p3C/p3D/p3E` des autres sessions intouchés)
6. ✅ git exécuté : racine `c6dd51f` (commit **local uniquement**, pre-commit 7/7 PASS, zéro push) + Projects/mLoop `f69b458` → `eaf92b8` **pushé sur `project-mLoop`**
