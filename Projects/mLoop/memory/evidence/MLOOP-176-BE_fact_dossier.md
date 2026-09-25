---
story_id: MLOOP-176-BE
dossier_status: VALIDATED
created_at: 2026-09-23T15:08:56Z
updated_at: 2026-09-23T15:08:56Z
sources_hashes:
  source_1: epic17_prioritization_matrix
  source_2: modular_extraction_protocol
---

# Dossier de Preuves Documentaires & Cadrage — `MLOOP-176-BE` (Extraction Modulaire de src/converters/svg_to_md.py — Convertisseur OCR/SVG (BR=2, 991L))

> **Titre Fonctionnel Pur** : Extraction Modulaire de src/converters/svg_to_md.py — Convertisseur OCR/SVG (BR=2, 991L)  
> **Epic Jira** : `EPIC-17-MODULAR-REFACTORING` (Extraction Modulaire RULE-AST-01)  
> **Couche** : `backend`  
> **Récit Précédent / Dépendances** : [`MLOOP-172-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-172-BE.md)

---

### 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local |
| :--- | :--- | :--- |
| **Maquette Principale** | — | *N/A - Composant Headless* |
| **Cible d'extraction** | Code source monolithique | [`src/converters/svg_to_md.py`](file:///C:/Memory%20Loop/src/converters/svg_to_md.py) |
| **Protocole SSOT** | Règle d'extraction modulaire | [MODULAR_EXTRACTION_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md) |
| **Matrice priorisation** | Blast radius & ordre Lot | [epic17_prioritization_matrix.md](file:///C:/Memory%20Loop/Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md) |
| **Gabarit dossier** | Template officiel | [dossier_de_preuves_template.md](file:///C:/Memory%20Loop/standards/blueprints/dossier_de_preuves_template.md) |

> *Note Headless* : Récit de refactoring modulaire 100% headless — aucune interface visuelle, le code source physique `src/converters/svg_to_md.py` est la source principale.

---

### 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue |
| :--- | :--- | :--- | :--- |
| *N/A — zéro conflit de sources détecté* | — | — | — |

---

### 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> NOTE
**Extrait 1 — Monolithe SvgSpatialParser 484 lignes**  
**Source** : [`src/converters/svg_to_md.py`](file:///C:/Memory%20Loop/src/converters/svg_to_md.py)  
*« Le fichier src/converters/svg_to_md.py pèse 991 lignes (37.8 Ko) dont la classe SvgSpatialParser en occupe 484 — le vrai monolithe est le parser spatial, pas l'OCR qui est déjà séparé dans svg_ocr_bridge.py (hypothèse couplage OCR réfutée par F2). »*  
➔ **Fait établi** : 991L total, SvgSpatialParser 484L, OCR déjà séparé (svg_ocr_bridge.py), BR=2 callers..

> NOTE
**Extrait 2 — Callers lazy pipelines internes**  
**Source** : [`src/pipelines/ingest_file_processors.py`](file:///C:/Memory%20Loop/src/pipelines/ingest_file_processors.py)  
*« Deux callers lazy internes aux pipelines identifiés par Search-Before-Ask : ingest_file_processors → parse_svg_to_md_text, et ingest_indexers → generate_maquettes_index — ni MCP ni CLI, shim trivial avec vigilance standard. »*  
➔ **Fait établi** : 2 callers lazy pipelines, shim trivial, zéro appelant externe..

> NOTE
**Extrait 3 — Tests existants couverture réelle**  
**Source** : [`tests/test_svg_spatial_parser.py`](file:///C:/Memory%20Loop/tests/test_svg_spatial_parser.py)  
*« Couverture test réelle déjà existante confirmée par Search-Before-Ask : test_svg_spatial_parser.py (parse, modes 1/2, mock ocr_vectorized_svg) et test_svg_ocr_bridge.py — pas de gate ajouter tests d'abord requis avant l'extraction. »*  
➔ **Fait établi** : 2 fichiers de tests existants, couverture réelle vérifiée, pas de gate tests préalables..

---

### 3. Schéma de Données & Tables Clés

Pas d'entité transactionnelle : récit purement structurel (refactoring modulaire), zéro schéma DB modifié.

---

### 4. Contrats Déclaratifs Cibles

* **Backend** : `N/A - Exemption ADR-0319` — aucune route HTTP n'est consommée ni exposée. Exemption déclarée avec `OQ-176` + `[API de soumission à definir]`.
* **Contrat d'import (shim)** : `from src.converters.svg_to_md import *` résout tous les symboles publics historiques sans `ImportError`.
* **Plafond** : chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS via `code-check --file`).

---

### 5. Evaluation de la Frontiere Active

#### CAS A — Arbitrages tranches en Grill-Me 1:1 : Decisions Consignees

| Question Grill | Decision Arbitree |
| :--- | :--- |
| Q1 — Découpe SvgSpatialParser | Option A (5 modules + mixin) — OCR déjà séparé F2, 484L parser = vrai monolithe |
| Q3 — Séquençage Lot 3 | reprise macro Q2 — build gelé, grill autorisé, exécution différée |
| Q5 — Callers identifiés | pré-résolu F4 — 2 callers lazy pipelines internes |

> **Frontiere close** — toutes les questions d'arbitrage ont ete tranchees en session Grill-Me 1:1 contradictoire (frontiere epuisee), puis approuvees par l'humain (batch APPROVE 2026-09-23). Zero question ouverte residuelle.

---

### 6. Résultats Build (post-extraction, 2026-09-24)

| Métrique | Avant | Après |
| :--- | ---: | ---: |
| Lignes module source | 991 L (38 720 o) | 4 L (shim) |
| Lignes max sous-module | 991 L | 298 L (`_svg_output.py`) |
| Violations RULE-AST-01 | 2 | 0 (7/7 `code-check --file` PASS) |
| Fumée imports (`import_smoke_check`) | — | ✅ VERT (7 callers résolus, 0 symbole non résolu) |
| Tests SVG ciblés | 13 PASS (baseline) | 13 PASS (0.14s) — dont les 2 tests `patch("src.converters.svg_to_md.ocr_vectorized_svg")` inchangés |
| Suite complète `pytest tests/` | 1395 PASS / 1 FAIL (248s) | **1403 PASS / 1 FAIL (251.39s)** — FAIL identique (`test_resolve_story_query_latency`, flaky pré-existant hors périmètre) |

**Résolution technique clé** : le mécanisme de patch de test `unittest.mock.patch("src.converters.svg_to_md.ocr_vectorized_svg", ...)` a été préservé **sans modifier les tests** en faisant résoudre `ocr_vectorized_svg` par `parse_svg_to_md_text` (désormais dans `_svg_output.py`) via un lookup dynamique paresseux sur le module shim (`import src.converters.svg_to_md as _svg_to_md_shim`). Ce patron a été validé empiriquement par un probe isolé avant écriture du code de production.

**Non-régression confirmée** : callers réels (`ingest_file_processors.parse_svg`, `ingest_indexers.generate_maquettes_index`) résolus à l'exécution sans modification. Aucune ligne de `tests/` ni des 2 callers n'a été touchée.

**Statut final** : `DONE_TESTED` — worker de vérification `worker_mloop_176_be` (w1:p3K) moissonné puis fermé (Zéro Session Zombie).
