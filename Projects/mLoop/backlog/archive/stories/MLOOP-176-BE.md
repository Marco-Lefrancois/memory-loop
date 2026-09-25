---
id: MLOOP-176-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactor
title: Extraction Modulaire de src/converters/svg_to_md.py — Convertisseur OCR/SVG
  (BR=2, 991L)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #23 BR · Lot 3'
macro_size: S
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
created_at: '2026-09-23'
grilled_at: '2026-09-23'
grill_decisions_ref: micro-grill 176 Q1-Q5 (Q1 micro A, Q2/Q4/Q5 pré-résolus Search-Before-Ask,
  Q3 reprise macro Q2 Lot 3)
approved_at: '2026-09-23'
approved_by: humain (go explicite batch APPROVE 173/174/175/176/178/179)
ttl_cycles: 4
---

# Extraction Modulaire de src/converters/svg_to_md.py — Convertisseur OCR/SVG (BR=2, 991L)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,
**je veux** découper `src/converters/svg_to_md.py` (991 L, BR=2) en sous-modules cohérents inférieurs à 300 L chacun, en suivant le cas général §2 du protocole d'extraction modulaire,
**afin de** résorber la violation RULE-AST-01 du convertisseur SVG→Markdown sans altérer le pipeline d'ingestion OCR ni les 2 callers qui en dépendent.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #23, BR=2, Lot 3, 37.8 Ko)
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas général §2 (découpe par famille de responsabilités)**
- **Hypothèse de Chiffrage Retenue** : Découpe en 3-4 familles (parsing SVG, extraction texte/OCR, conversion Markdown, utilitaires) + shim de ré-export ; BR=2 callers, risque faible.
- **Enveloppe Macro Estimée** : S (fourchette de 0.5 à 1 jour)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie de `src/converters/svg_to_md.py` (991 L, 37.8 Ko) : identification des familles (parsing SVG, détection texte vs tracés vectoriels, pipeline OCR headless, rendu Markdown).
- Création du package `src/converters/svg_to_md/` avec sous-modules thématiques, chacun ≤ 300 L / 15 Ko.
- Shim de ré-export `src/converters/svg_to_md.py` garantissant la rétrocompatibilité des 2 callers.
- Vérification ADR-0369 sur les sous-modules : tout accès fichier via `with`, tout appel réseau/subprocess avec `timeout` explicite, zéro `except Exception: pass` nu.
- Check fumée imports + suite tests verte post-extraction.
- Mise à jour de `epic17_prioritization_matrix.md`.

### Out-of-Scope (Macro)
- Modification du comportement OCR ou des règles de conversion SVG→Markdown (portée strictement structurelle).
- Remplacement du moteur OCR (Chromium headless) — hors périmètre de refactoring.
- Autres fichiers Lot 3 (`server.py`, etc.) — traités dans MLOOP-177-BE.

---

## 4. Critères de Succès Préliminaires

- [x] Chaque sous-module du package `src/converters/svg_to_md/` passe `code-check --file` : ≤ 300 L, ≤ 15 Ko.
- [x] Shim `src/converters/svg_to_md.py` opérationnel : `python -c "from src.converters.svg_to_md import *"` sans erreur.
- [x] Check fumée vert : zéro symbole non résolu détecté.
- [x] ADR-0369 respecté dans tous les sous-modules : `with` sur fichiers, `timeout` sur subprocess, zéro exception silencieuse.
- [x] Suite tests inchangée : `pytest tests/ -x -q` — N_après ≥ N_avant PASS, 0 FAIL. (1404 PASS / 0 FAIL vs baseline 1395 PASS / 1 flaky)
- [x] Plan archivé sous `memory/plan/implementation_plan_MLOOP-176-BE.md` avec checklist §4 complétée.

---

## 5. Décisions Grill-Me 1:1 (Frontière Épuisée 2026-09-23)

> [!DONE]
> *Session contradictoire 1:1 clôturée — 5/5 questions tranchées (Q1 micro ici ; Q2/Q4/Q5 pré-résolus Search-Before-Ask ; Q3 reprise macro Q2 Lot 3).*
> *Récit éligible conversion Palier 2 après validation wikifix/rubber-duck et approbation humaine.*

- ✅ **Q1 — Découpe de `SvgSpatialParser` (484L) → Option A (5 modules + mixin)** : monolithe réel = la classe parser (484L), **pas l'OCR** (déjà séparé dans `svg_ocr_bridge.py`, F2). Découpe : `_svg_models.py` (`UIElement`+`compute_svg_path_bbox_accurate` ~165L) · `_svg_parser_core.py` (`parse`+`_traverse_node`+`_parse_transform` ~250L) · `_svg_parser_classify.py` (`ParserClassifyMixin` : `_associate_and_classify`+`_classify_outlined_svg`+fallback ~230L) · `_svg_output.py` (`generate_ascii_wireframe`+`parse_svg_to_md_text`+`convert_svg_file_to_md` ~266L) · `_svg_index.py` (`generate_maquettes_index` 45L) + shim. Option B rejetée (fusion index → 311L >300), Option C rejetée (functions pures cassent l'API `SvgSpatialParser` des tests).
- ✅ **Q2 — Effets de bord à l'import → pré-résolu Search-Before-Ask (F3)** : **pas de `_svg_init_effects.py`** — zéro `re.compile`/`basicConfig`/`subprocess`/`open()` top-level ; seul `logger = get_logger(...)` L19.
- ✅ **Q3 — Séquençage Lot 3 → reprise macro Q2** : **Lot 3 (176/177) gelé pour le BUILD** jusqu'à clôture du Lot 1 Beachhead (`state→db→sync→lifecycle→_registry`) — **grill autorisé maintenant**, exécution différée.
- ✅ **Q4 — Tests existants → pré-résolu Search-Before-Ask (F5)** : `test_svg_spatial_parser.py` (parse, modes 1/2, mock `ocr_vectorized_svg`) + `test_svg_ocr_bridge.py` — **couverture réelle existante**, pas de gate « ajouter tests d'abord ».
- ✅ **Q5 — Callers identifiés → pré-résolu Search-Before-Ask (F4)** : **2 callers lazy internes pipelines** (pas MCP/CLI) : `ingest_file_processors` → `parse_svg_to_md_text`, `ingest_indexers` → `generate_maquettes_index` — shim trivial, vigilance standard.

---

## Règles d'affaires

- **Plafond modulaire absolu** : chaque sous-module de `src/converters/svg_to_md/` doit rester sous 300 lignes et 15 Ko (ADR-0202 / RULE-AST-01).
- **Pattern mixin classify (décision Q1-A)** : `ParserClassifyMixin` + `SvgSpatialParserCore` — API `SvgSpatialParser.<méthode>()` intacte pour les tests et usages internes.
- **Rétrocompatibilité stricte des callers** : les 2 callers lazy (`parse_svg_to_md_text`, `generate_maquettes_index`) ne sont jamais modifiés — le shim rend tout import historique résoluble.
- **Séquençage Lot 3** : build gelé jusqu'à clôture du Lot 1 Beachhead (macro Q2) — grill clôturé, exécution en attente.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extraction SvgSpatialParser 5 Modules (Q1-A)
- [ ] Package `src/converters/svg_to_md/` créé : `_svg_models.py`, `_svg_parser_core.py`, `_svg_parser_classify.py`, `_svg_output.py`, `_svg_index.py` — chacun ≤ 300 L / 15 Ko
- [ ] Mixin `ParserClassifyMixin` + `SvgSpatialParserCore` — API `SvgSpatialParser.<méthode>()` intacte pour les tests et usages internes
- [ ] OCR déjà séparé (`svg_ocr_bridge.py`) — zéro couplage réintroduit

#### 2. Rétrocompatibilité & Non-Régression (Q4/Q5)
- [ ] Shim résout `parse_svg_to_md_text` + `generate_maquettes_index` pour les 2 callers lazy pipelines inchangés
- [ ] ADR-0369 respecté : `with` sur fichiers, `timeout` sur subprocess, zéro `except Exception: pass` nu
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après ≥ N_avant PASS, 0 FAIL
- [ ] Séquençage Lot 3 : build gelé jusqu'à clôture du Lot 1 Beachhead (macro Q2)

### Admission of Limits
- Avertissements rubber-duck génériques (timeout réseau, expiration de session, anti-rebond) hors domaine : convertisseur headless — dégradation OCR et fallback regex couverts par les piliers Gherkin.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/converters/svg_to_md.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-176` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `parse_svg_to_md_text` / `generate_maquettes_index` (shim) | Rétrocompatibilité 2 callers lazy pipelines |
| `SvgSpatialParser` (mixins) | API parser inchangée pour tests + usages |
| `code-check --file` sous-modules | ≤ 300 L / 15 Ko each (RULE-AST-01 PASS) |

---

## Scénarios de test

### Pilier 1 — Nominal (Happy path)
```gherkin
Scénario : Découpage modulaire transparent du convertisseur SVG
  Étant donné le package "src/converters/svg_to_md/" subdivisé en 5 modules <= 300 lignes
  Quand un caller importe "from src.converters.svg_to_md import parse_svg_to_md_text, SvgSpatialParser"
  Alors les symboles publics sont résolus sans régression ni avertissement
```

### Pilier 2 — Exceptions (Cas d'erreur)
```gherkin
Scénario : Dégradation gracieuse OCR préservée après extraction
  Étant donné un SVG vectorisé sans Chromium/OCR disponible
  Quand "parse_svg_to_md_text" appelle le pont OCR via le shim
  Alors le retour est None sans exception propagée (contrat svg_ocr_bridge inchangé)
```

### Pilier 3 — Résilience (Réseau / Timeout / Mode dégradé)
```gherkin
Scénario : Fallback regex sur SVG corrompu
  Étant donné un fichier SVG au XML invalide
  Quand "SvgSpatialParser.parse" échoue sur ElementTree
  Alors le parser retombe sur "_fallback_regex_parse" sans crash (comportement pré-extraction)
```

### Pilier 4 — UX / Accessibilité / État vide
```gherkin
Scénario : Conversion d'un maquette SVG vierge
  Étant donné un SVG sans éléments UI extractibles
  Quand "generate_ascii_wireframe" ou "convert_svg_file_to_md" est appelé
  Alors un rendu vide/clair est produit sans message parasite ni effet de bord d'import
```
