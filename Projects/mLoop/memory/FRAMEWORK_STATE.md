---
document_type: framework_state
last_updated: "2026-09-24"
maintainer: "AGY session mLoop"
scope: "mLoop (framework core)"
---

# FRAMEWORK_STATE — Changelog Opérationnel du Framework mLoop

> **Lecture obligatoire avant toute génération de plan, audit, ou fact-check.**
> Ce fichier consigne les changements du framework qui impactent la validité
> des plans, certificats et audits passés. Un plan généré SANS lire ce fichier
> est invalide par défaut.

---

## Initialisation — 2026-09-20

- **Contexte** : Initialisation du registre pour le projet mLoop (auto-développement du framework, `C:\Memory Loop\src`).
- **Baseline déterministe de référence** : `python src/swarm.py code-check --all` du 2026-09-20 — 258 fichiers analysés, 170 conformes, 257 violations AST, dont **16 violations sur 8 modules `src/utils/`** (détail : `Projects/mLoop/memory/evidence/MLOOP-101-BE_fact_dossier.md` §3.1).
- **Aucun changement du framework appliqué à cette date** : aucune invalidation de plan, certificat ou audit antérieur n'est à déclarer. Le premier chantier attendu est MLOOP-101-BE (rénovation modulaire utils).

---

## Checklist de validation d'un plan (à vérifier par tout agent générant un plan)

Avant de soumettre un plan pour revue humaine, l'agent DOIT confirmer :

- [ ] **Status source vérifié** : lire le frontmatter YAML du récit, pas supposer
- [ ] **Certificat NLI daté** : si `timestamp` antérieur à la date du dernier
       commit du framework, marquer comme obsolète et inclure la régénération
       dans §3 du plan
- [ ] **struct-check inclus dans §5A** : obligatoire pour activer Gate C12
       (Domain Sanity — `DI-POL`, `DI-PHY`, `DI-TMP`, `DI-STA`, `DI-CRD`)
- [ ] **verification_harness non vide** : si `verification_harness: {}`, OQ à
       résoudre AVANT clôture, pas en dette séparée
- [ ] **Transition d'état valide** : vérifier le statut courant du frontmatter,
       pas celui supposé ou mémorisé de la session précédente

## 2026-09-21 — Rénovation modulaire utils livrée & DoR handlers CLI

- **Changement appliqué** : MLOOP-101-BE `DONE_TESTED` — packages `src/utils/lexicon/` et `src/utils/token_ledger/` créés, 7 audits ADR-0369, fix `sqlite3` L143. **Impact** : tout certificat, plan ou audit antérieur traitant `src/utils/lexicon_resolver.py` (411L) et `src/utils/token_ledger.py` (350L) comme modules monolithiques est marqué obsolète.
- **Baseline déterministe 2026-09-21** : `src/commands/handlers/project.py` 462L, `analysis.py` 525L, `export.py` 340L, `architecture.py` 320L, `_registry.py` 2000L — **5 violations RULE-AST-01** sur les 4 handlers cibles (registre exclu).
- **Chantier en cours** : MLOOP-106-BE (Découpage Modulaire des Handlers CLI) — Grill-Me 1:1 clos (4 arbitrages : `_registry` → récit dédié, granularité 1:1, tests 3 couches, lots séquentiels), dossier de preuves `MLOOP-106-BE_fact_dossier.md` (VALIDATED), rubber-duck **APPROUVÉ** (Trust Score 91.6, 0 bloquant), plan `memory/plan/implementation_plan_MLOOP-106-BE.md` (**DRAFT**, en attente d'approbation humaine). `_registry.py` routé vers un récit dédié (MLOOP-111-BE).
- **Observation framework (à router)** : l'extraction automatique du `verification_harness` (regex `Scénario:` ancrée en début de ligne dans `src/pipelines/evidence_pack.py`) ne capture pas les scénarios Gherkin **indentés** du gabarit officiel `story_template.md` → `verification_harness` vide pour la quasi-totalité des récits. Candidat à un correctif dédié (non couvert par MLOOP-106-BE, hors périmètre).

## 2026-09-22 — Extension schema EvidencePack (5 champs de parité Phase 2)

- **Changement appliqué** : MLOOP-180-BE `IN_QA` — `src/pipelines/evidence_pack.py` étendu : 4 TypedDict (`VerbatimExtract`, `ImplementationDecision`, `DeclarativeContract`, `ConflictResolution`) + `DecisionCategory` Literal fermé (7 valeurs) + validators `_validate_verbatim_extract` / `_validate_decision_category` (`ValueError` contextualisée, zéro swallow) + multiplicateur Déc.5 (`score × (0.7 + 0.3 × min(1, richness/10))`, HIGH→MEDIUM si mult < 0.85) + `richness_penalty` injecté dans `epistemic_audit` + 5 champs Optionals dans le dict retourné par `extract_evidence`. **Impact** : tout certificat, plan ou audit antérieur supposant un pack sans les 5 champs de richesse (`verbatim_extracts`, `implementation_decisions`, `declarative_contracts`, `epistemic_audit` riche, `conflict_matrix`) est obsolète — recharger un legacy via le nouveau moteur produira les 5 champs defaultés (`.get(..., [])`, jamais de KeyError sur les 71 packs).
- **Baseline déterministe 2026-09-22** : `evidence_pack.py` dépasse RULE-AST-01 (>300L, préexistant — modularisation = story séparée) ; 0 violation nouvelle introduite par ce chantier. Tests : `test_evidence_pack.py` 6→28 tests (28/28 vert), croisé `test_grill_engine.py` 35/35 vert.
- **Suite EPIC-18** : MLOOP-181-BE (intégration harnais Phase 3 Build) et MLOOP-182-BE (backfill rétroactif) restent `READY_FOR_DEV`, séquence stricte blocked_by 180.

## 2026-09-24 — Extraction modulaire svg_to_md livrée (EPIC-17 Lot 3)

- **Changement appliqué** : MLOOP-176-BE `DONE_TESTED` — monolithe `src/converters/svg_to_md.py` (991L, BR=2) remplacé par le package `src/converters/svg_to_md/` (6 fichiers : `_svg_models` 178L · `_svg_parser_core` 287L · `_svg_parser_classify` 231L · `_svg_output` 298L · `_svg_index` 57L · `__init__` 49L) + shim 4L. **Impact** : tout certificat, plan ou audit antérieur traitant `svg_to_md.py` comme monolithique (dont `epic17_top40_oversized.txt`, baselines BR de la matrice EPIC-17) est marqué obsolète pour ce qui concerne sa structure — le comportement public est strictement inchangé (shim + ré-exports, surface `ocr_vectorized_svg` préservée pour les monkeypatchs de tests).
- **Baseline déterministe 2026-09-24** : suite complète `pytest tests/` → **1404 PASS / 0 FAIL** (257s ; baseline pré-build 1395 PASS / 1 FAIL flaky latence) ; `code-check --file` 7/7 PASS (0 violation RULE-AST-01) ; fumée imports 7/7 callers résolus ; struct-check story conforme. Probes runtime : fallback regex SVG corrompu ✅, wireframe vierge ✅.
- **Suite EPIC-17 Lot 3** : MLOOP-177-BE (`server.py` 1634L) reste le prochain chantier du lot (statut courant à vérifier dans `backlog/sprint_backlog.md` — SSOT des statuts).

