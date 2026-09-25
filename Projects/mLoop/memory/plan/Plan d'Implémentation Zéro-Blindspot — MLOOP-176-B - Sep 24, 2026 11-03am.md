---
created: 2026-09-24T15:03:25.165Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, ro-blindspot, python]
---

[[Plannotator Plans]]

# Plan d'Implémentation Zéro-Blindspot — MLOOP-176-BE
# Extraction Modulaire de `src/converters/svg_to_md.py` (991L → package ≤300L/module)

> **Récit** : `Projects/mLoop/backlog/stories/MLOOP-176-BE.md` — `status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6, approuvé (batch APPROVE 2026-09-23)
> **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — Cas général §2 + Décision grill Q1-A (5 modules + mixin)
> **Audit 360°** : ADR-0376 (7 couches balayées ci-dessous) · ADR-0352 (FRAMEWORK_STATE lu) · ADR-0369 · ADR-0202
> **Date** : 2026-09-24 · **Statut** : DRAFT (en attente feu vert humain)

---

## §0. Cadre & Pré-requis Vérifiés (avant toute écriture)

| Contrôle | Résultat |
|:---|:---|
| Boot Sequence | ✅ resume · vibe-check **22 PASS / 1 WARNING / 0 FAIL** · focus → story `IN_ANALYZE` (réalignée SSOT `READY_FOR_DEV`) |
| FRAMEWORK_STATE (ADR-0352) | ✅ Lu — `last_updated 2026-09-22` ; aucun certificat NLI émis pour ce récit (gabarit extraction MLOOP-172-BE : item N/A) ; entries MLOOP-170→179 absentes du changelog → régénération ajoutée en §6 |
| Frontmatter source | ✅ Lu direct : `READY_FOR_DEV` · transition cible `IN_DEV` → `DONE_TESTED` (state machine Gate C9+C12 valide) |
| `verification_harness` | ✅ Non vide : 4 scénarios Gherkin (preuves runtime en §5C) |
| Lot 3 dégelé | ✅ sprint_backlog : « Lot 3 DÉGELÉ 2026-09-23 (humain) » ; Lot 1 Beachhead clos (170/171/172/173/174/175/177/178/179 = DONE_TESTED) |
| **Baseline code-check** | `src/converters/svg_to_md.py` → **FAIL, 991 L / 38 720 o, 2 violations RULE-AST-01** (plafond lignes + taille) |
| **Baseline pytest complet** | **1395 PASS / 1 FAIL** en 248 s — FAIL = `tests/performance/test_utils_latency.py::test_resolve_story_query_latency` (**pré-existant, flaky** : re-passe solo en 0.17 s). N_avant = 1395P ; cible N_après ≥ 1395P et **0 nouveau FAIL** |
| DELEGATION GATE (ADR-0346) | **4/4 OUI** (≥3 fichiers · >5 min · type build · pollution contexte) → **délégation obligatoire** : réutilisation du worker existant **`worker_176` (pane `wA:p1`, IDLE)** — né pour cette story. **Zéro spawn doublon** ; `w1:p1`/`w1:p3C`/`w1:p3D`/`w1:p3E` intouchés |
| Fact-Search | ✅ 5 preuves FTS5 (ADR-0351/0332 + protocole ingestion) — tracées dans l'EvidencePack |
| Verrous utilisateur | 🚫 zéro écriture Jira · 🚫 aucun autre récit ouvert (EPIC-19 hors périmètre) · tests/ intacts · callers intacts |

---

## §1. Module Source & Callers (protocole §2.1 Étape 0)

| Champ | Valeur |
|:------|:-------|
| Chemin source | `src/converters/svg_to_md.py` |
| Avant | **991 L · 38 720 o (37.8 Ko)** · BR = 2 (`ast_import_count`) |
| Lot EPIC-17 | Lot 3 (rang #23, dégelé) |

**Callers (2, lazy, INTACTS — jamais modifiés)** :
- `src/pipelines/ingest_file_processors.py:30` → `from src.converters.svg_to_md import parse_svg_to_md_text`
- `src/pipelines/ingest_indexers.py:152` → `from src.converters.svg_to_md import generate_maquettes_index`

**Consommateurs de surface (vérification non-régression, lecture seule)** :
- `tests/test_svg_spatial_parser.py` — importe `SvgSpatialParser, generate_ascii_wireframe, parse_svg_to_md_text, convert_svg_file_to_md` ET **monkeypatche `src.converters.svg_to_md.ocr_vectorized_svg`** (L114, L142) → **surface de patch obligatoire** (voir §3.1)
- `tests/test_svg_ocr_bridge.py` — pont OCR (hors périmètre, intouché)
- `src/converters/svg_ocr_bridge.py`, `src/pipelines/evidence_pack.py` — références documentaires uniquement

---

## §2. Découpe par Familles de Responsabilités (Décision grill Q1-A, verbatim)

| # | Sous-module cible | Symboles (plages L. du monolithe) | L estimées | Plafond |
|:-:|:--|:--|--:|:--:|
| 1 | `_svg_models.py` **[NEW]** | `UIElement` (L22-36) + `compute_svg_path_bbox_accurate` (L38-187) | ~181 L | ✅ |
| 2 | `_svg_parser_core.py` **[NEW]** | `SvgSpatialParserCore` : `__init__` (L195) · `parse` (L204) · `_parse_transform` (L250) · `_traverse_node` (L267-443) + assemblage `class SvgSpatialParser(ParserClassifyMixin, SvgSpatialParserCore)` | ~270 L | ✅ |
| 3 | `_svg_parser_classify.py` **[NEW]** | `ParserClassifyMixin` : `_associate_and_classify` (L444) · `_classify_outlined_svg` (L512) · `_fallback_regex_parse` (L660-674) | ~249 L | ✅ |
| 4 | `_svg_output.py` **[NEW]** | `generate_ascii_wireframe` (L675) · `parse_svg_to_md_text` (L756) · `convert_svg_file_to_md` (L956-991) + helper `_call_ocr_vectorized_svg` | ~297 L ⚠️ | ✅ serré |
| 5 | `_svg_index.py` **[NEW]** | `generate_maquettes_index` (L909-955) | ~53 L | ✅ |
| 6 | `__init__.py` **[NEW]** | Ré-exports complets + `__all__` + `ocr_vectorized_svg` (surface de patch) + `logger` | ~35 L | ✅ |
| 7 | `src/converters/svg_to_md.py` **[MODIFY → SHIM]** | Shim de ré-export style `lifecycle.py` (masqué par le package — précedent MLOOP-174-BE) | ~45 L | ✅ |

**⚠️ Contingence pré-autorisée (ADR-0202 absolu > nombre de modules)** : si `code-check` sort `_svg_output.py` ≥ 300 L / 15 Ko → extraire `generate_ascii_wireframe` (L675-754, ~80 L) dans **`_svg_wireframe.py` [NEW]** (6ᵉ module, output retombe à ~217 L). Aucune re-approbation requise — le plafond 300 L est une règle inviolable, l'Option B/C du grill restent rejetées.

---

## §3. Règles d'Implémentation Critiques (zéro régression)

### 3.1 🔴 Surface de patch OCR — contrat de non-régression décisif
Les tests patchent **`src.converters.svg_to_md.ocr_vectorized_svg`**. Après extraction, ce nom résout le **package** `__init__`, mais le point d'appel migrera dans `_svg_output.py` → un binding statique local casserait `mock_ocr.assert_called_once()`.

**Solution imposée au worker** :
1. `__init__.py` : `from src.converters.svg_ocr_bridge import ocr_vectorized_svg  # noqa: F401` (surface de patch publique).
2. `_svg_output.py` : wrapper à résolution **dynamique au moment de l'appel** (import de package au niveau fonctionnel → zéro cycle à l'init, patch intercepté à l'exécution) :
   ```python
   def _call_ocr_vectorized_svg(svg_path):
       from src.converters import svg_to_md as _pkg  # package masqué, import tardif
       return _pkg.ocr_vectorized_svg(svg_path)
   ```
   Remplacer l'appel unique `ocr_vectorized_svg(svg_path)` (ex-L793) par `_call_ocr_vectorized_svg(svg_path)`.
3. **TDD** : `tests/test_svg_spatial_parser.py` (inchangé) est le harnais — 2 tests OCR font échouer immédiatement si la résolution est statique (Red) → wrapper (Green).

### 3.2 Assemblage classe (MRO mixins)
- `SvgSpatialParserCore` (modèle 2) porte `__init__/parse/_traverse_node/_parse_transform` ; `ParserClassifyMixin` (modèle 3) porte la classification ; **assemblage en bas de `_svg_parser_core.py`** : `class SvgSpatialParser(ParserClassifyMixin, SvgSpatialParserCore): ...` (docstring uniquement).
- `from ._svg_parser_classify import ParserClassifyMixin` dans le core ; **le mixin n'importe JAMAIS le core** (pas de cycle). API `SvgSpatialParser.<méthode>()` intacte (L189+).

### 3.3 Logger (Q2 — zéro nouvel effet de bord)
- `get_logger` est **idempotent** (`if not logger.handlers`, `src/utils/logger.py:162`) : chaque sous-module appelle `logger = get_logger("converters.svg_to_md")` → même instance `mloop.converters.svg_to_md`, handlers non dupliqués, fichier `memory/logs/` ouvert une seule fois. Aucun `basicConfig`, aucune regex compilée, aucun `open()` top-level.
- Strings d'extra `"component": "converters.svg_to_md"` (ex-L243) conservées telles quelles.

### 3.4 Imports & ADR-0369
- Chaque sous-module n'importe que ce qu'il utilise (pas d'import star inter-modules). Déplacement **pur** : zéro changement de comportement, zéro nouvelle règle — `code-check` (AST ADR-0381/0369) doit rester au vert : `with`/méthodes Path sur fichiers, pas de `subprocess` dans ce fichier (OCR est déjà dans `svg_ocr_bridge.py`), aucun `except Exception: pass` nu (les handlers existants loggent — conservés).

### 3.5 Shim & rétrocompatibilité (2 callers + surface historique)
- Le **package l'emporte sur le module fichier** (précedent vérifié empiriquement : `state/`, `lifecycle/` + `lifecycle.py`, `_registry/` + `_registry.py`, `vibe_check/`, `sync/`, `db/`).
- `svg_to_md.py` (shim, style MLOOP-174) : docstring « MASQUÉ par le package — NE PAS MODIFIER » + imports nommés explicites + `__all__`.
- `__init__.py` ré-exporte la surface publique historique observée (`dir()` baseline) : `SvgSpatialParser`, `UIElement`, `compute_svg_path_bbox_accurate`, `generate_ascii_wireframe`, `parse_svg_to_md_text`, `generate_maquettes_index`, `convert_svg_file_to_md`, `ocr_vectorized_svg`, `logger` + nouveaux `SvgSpatialParserCore`, `ParserClassifyMixin`.

---

## §4. Livrables Physiques

| Artefact | Action | Détail |
|:---------|:------:|:-------|
| `src/converters/svg_to_md/_svg_models.py` | **[NEW]** | Modèles + bbox (~181 L) |
| `src/converters/svg_to_md/_svg_parser_core.py` | **[NEW]** | Core parser + assemblage classe (~270 L) |
| `src/converters/svg_to_md/_svg_parser_classify.py` | **[NEW]** | Mixin classification (~249 L) |
| `src/converters/svg_to_md/_svg_output.py` | **[NEW]** | Wireframe + Markdown + convert + wrapper OCR (~297 L) |
| `src/converters/svg_to_md/_svg_index.py` | **[NEW]** | Index maquettes (~53 L) |
| `src/converters/svg_to_md/__init__.py` | **[NEW]** | Ré-exports + `__all__` (~35 L) |
| `src/converters/svg_to_md.py` | **[MODIFY]** | 991 L → shim ~45 L |
| `(_svg_wireframe.py)` | *(contingence)* | Si plafond 300 L franchi sur `_svg_output` |
| `Projects/mLoop/memory/plan/implementation_plan_MLOOP-176-BE.md` | **[NEW]** | Plan archivé (ADR-0307, gabarit `modular_extraction_plan_template.md`) — requête explicite du récit §4 |

**Intouchables absolus** : `tests/**` (0 fichier), `src/pipelines/ingest_file_processors.py`, `src/pipelines/ingest_indexers.py`, `src/converters/svg_ocr_bridge.py`, tout récit hors MLOOP-176, EPIC-19 (190-194), panneaux `w1:*`.

---

## §5A. Séquence d'Exécution (Phase BUILD)

1. **Archiver le plan** dans `Projects/mLoop/memory/plan/implementation_plan_MLOOP-176-BE.md` (statut IN_PROGRESS) — satisfait Story §4 + ADR-0307 + Check 22 (plan_dir = `Projects/mLoop/memory/plan`, glob satisfied par `implementation_plan_critic_extraction.md` existant + futur plan).
2. **struct-check** (ADR-0352 Gate C12) : `python src/swarm.py struct-check --file Projects/mLoop/backlog/stories/MLOOP-176-BE.md`.
3. **Délégation** : `herdr_agent_prompt` → worker `worker_176` (wA:p1) avec brief contenant §2-§3 intégraux (pwd vérifié = `C:\Memory Loop`, TDD, interdiction de toucher callers/tests, pas de commit worker).
4. **Attente** : `herdr_agent_wait worker_176` → DONE/IDLE (poll ≤10s/appel) ; si worker mort → `worker-spawn --task-type build` en fallback, puis teardown des 2.
5. **Harvest** : lecture rapports worker (`herdr_agent_read`) + vérification orchestrateur indépendante (§5B).

## §5B. Checklist Non-Régression (protocole §4 — post-extraction, preuve par l'orchestrateur)

```
PRÉ-EXTRACTION ✅ (déjà exécuté, §0)
[x] code-check --file : 2 violations baseline (991L/38720o)
[x] pytest : 1395 PASS / 1 FAIL flaky pré-existant (1396e solo OK)
[x] Callers : 2 identifiés (ingest_file_processors, ingest_indexers)

EXTRACTION (worker + vérif orchestrateur)
[ ] 5(+1 contingence) sous-modules créés — code-check --file × chacun = PASS ≤300L/15Ko
[ ] Shim créé · __init__ expose surface complète · aucun import circulaire
    (python -c "import src.converters.svg_to_md")

POST-EXTRACTION
[ ] python -m src.pipelines.import_smoke_check --module src/converters/svg_to_md.py → 🟢
[ ] python -c "from src.converters.svg_to_md import *" → OK
[ ] 2 callers résolus sans modification de leur fichier
[ ] pytest tests/test_svg_spatial_parser.py tests/test_svg_ocr_bridge.py -q → 100% vert
    (dont patch OCR via surface historique)
[ ] pytest tests/ -q --tb=no → N_après ≥ 1395 PASS, 0 NOUVEAU FAIL
    (si latency-flake rechute : re-run solo pour prouver flake, consigner §6)
[ ] Probes runtime Pilier 3/4 (Level-3, ADR-0385) :
    - SVG XML corrompu → parse() retombe sur _fallback_regex_parse sans crash
    - SVG vierge → wireframe « Aucun composant détecté », rendu Markdown vide/clair
[ ] git diff borné : uniquement src/converters/svg_to_md* (root) — zéro tests/, zéro callers/
[ ] MLOOP_SKIP_HOOKS non utilisé
```

## §5C. Preuves des 4 Piliers Gherkin (verification_harness)

| Pilier | Scénario | Preuve |
|:--:|:--|:--|
| 1 | Découpage transparent (import shim) | smoke + `from ... import *` + tests import historique |
| 2 | Dégradation OCR gracieuse | `test_convert_svg_vectorized_falls_back_to_placeholder_when_ocr_unavailable` (mock `None` → `ocr_status: UNAVAILABLE`) |
| 3 | Fallback regex SVG corrompu | probe runtime explicite (§5B) |
| 4 | Rendu SVG vierge sans parasite | probe runtime explicite (§5B) |

---

## §6. Clôture & Livrables de Gouvernance (après vert complet)

1. **Plan** → statut `DONE` + §6 résultats (métriques Avant/Après du gabarit) ; checklist Story §4 cochée.
2. **EvidencePack** `Projects/mLoop/memory/evidence/MLOOP-176-BE_evidence.json` (existant, VALIDATED) → enrichi : `implementation_decisions` (Option A 5 modules · wrapper OCR dynamique · shim masqué style 174 · contingence wireframe), `verbatim_extracts` sourcés L., `declarative_contracts` (shim import · ≤300L · callers intacts), proof `implementation_plan_MLOOP-176-BE.md` passée de « introuvable » → SHA-256 réel, `next_actions` → post-build (sync), confidence recalculée.
3. **fact_dossier** → section « §6 Résultats Build » (verbatim tests/code-check/smoke + probes) + `updated_at` frais.
4. **Matrice EPIC-17** L43 → annotation `**DONE_TESTED** — MLOOP-176-BE 2026-09-24 — package svg_to_md/ (5 modules ≤300L)` (format miroir de la L15/MLOOP-175).
5. **sprint_backlog.md** L31 → statut `**DONE_TESTED**` + note harvest (modules, code-check, tests) — SSOT de statut ; `python src/swarm.py sync --project mLoop` réaligne le frontmatter du récit (mécanisme vérifié en Boot).
6. **FRAMEWORK_STATE.md** → entrée 2026-09-24 (monolithe 991L → package ; tout audit traitant `svg_to_md.py` comme monolithe devient obsolète).
7. **vibe-check** final `--project mLoop` → ≥22 PASS, Check 22 PASS.
8. **Teardown** : `worker-status` → **fermer `worker_176` uniquement** ; `w1:p1/p3C/p3D/p3E` non touchés ; zéro zombie.
9. **Git** :
   - `Projects/mLoop` (sub-repo) : `add .` → `commit` → **`git push origin HEAD:project-mLoop`** (autorisé) — inclus story/sprint/evidence/plan/fact_dossier/matrice.
   - Racine `C:\Memory Loop` : commit **local uniquement** des `src/converters/*` (pré-commit ast_delta_checker attendu VERT : shim ≤300L, modules ≤300L) — **zéro push racine** (règle : main racine seulement hooks/blueprints).
10. 🚫 **Zéro écriture Jira** (moratoire respecté).

---

## §7. Risques & Réponses

| Risque | Probabilité | Réponse |
|:--|:--:|:--|
| `_svg_output` >300L | Moyenne | Contingence `_svg_wireframe.py` pré-autorisée (§2) |
| Patch OCR non intercepté (binding statique) | Haute si ongorithme naïf | §3.1 obligatoire + 2 tests OCR comme détecteur Red |
| Cycle d'import core↔mixin | Faible | Arrowhead imposé §3.2 |
| Latency-flake rechute en suite complète | Faible | Re-run solo + consignation (baseline déjà documentée) |
| Worker `wA:p1` mort | Faible | Fallback `worker-spawn --task-type build` |
| Dérive de périmètre (callers/tests/EPIC-19) | Faule si brief flou | Brief worker = §2-§4 intégraux ; `git diff` borné en §5B |

**Effort** : ~15-25 min worker + ~10 min vérifications/clôture (enveloppe macro S : 0.5-1 j respectée).
**Audit 360° 7 couches (ADR-0376)** : 1 Blueprints (aucun touché) · 2 Protocoles (suivi `MODULAR_EXTRACTION_PROTOCOL`) · 3 ADR (0202/0369/0376 applicables, 0370 N/A — zéro registry) · 4 Directives (`directives/` absent — non applicable) · 5 Skills (aucun SKILL.md touché) · 6 Core Python (7 fichiers converters) · 7 Tests & Parité (suite inchangée + guide CLI inchangé).