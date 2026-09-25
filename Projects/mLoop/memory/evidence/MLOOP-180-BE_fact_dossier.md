---
dossier_id: MLOOP-180-BE_fact_dossier
story_id: MLOOP-180-BE
dossier_status: CURRENT
created_at: "2026-09-22"
sources_hashes:
  epic_evidence_impl_decisions.md: "pending"
  evidence_pack.py: "pending"
  critic.py: "pending"
---

# Dossier de Preuves Documentaires — MLOOP-180-BE

## 🧭 1. Sources Physiques & Matrice de Vérité

| Source | Type | Rôle | Statut |
| :--- | :---: | :--- | :--- |
| `backlog/epic_evidence_impl_decisions.md` | Épic | Cadrage EPIC-18, 6 décisions Grill | ✅ CURRENT |
| `src/pipelines/evidence_pack.py` | Code | Composant cible (656 lignes, schema actuel) | ✅ Vérifié |
| `src/engine/rubber_duck/critic.py` | Code | Détecteurs Gate 5 / ADR-0319 / Gherkin | ✅ Vérifié |
| `docs/01-architecture/ADR-001_*.md` | ADR | Cadrage macro Grill-project | ✅ Généré |
| `docs/01-architecture/ADR-002_*.md` | ADR | Qualification micro Grill-Me 180-BE | ✅ Généré |
| Audit comparatif Phase 2 vs Phase 3 (22/09) | Session | Écart mesuré (citations, décisions, contrats) | ✅ Acté |

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

> Extrait 1 — `evidence_pack.py` (structure actuelle du pack) :
> « story_id, jira_key, fact_search_proofs, verification_harness, sources_consulted, confidence, confidence_score, status »
> ➔ Fait établi : le schema actuel ne contient **aucun** champ `implementation_decisions`, `verbatim_extracts`, `declarative_contracts`, `conflict_matrix`.

> Extrait 2 — Audit comparatif Phase 2 vs Phase 3 (22/09/2026) :
> « Phase 3 : Aucun extrait cité ❌ | Pas d'ancrage ligne ❌ | Matrice conflits absente ❌ | Décisions absentes ❌ | Contrats absents ❌ | Admission of Limits ⚠️ vide »
> ➔ Fait établi : écart épistémique mesuré sur 8 dimensions, 5 en `❌`, 2 en `⚠️`.

> Extrait 3 — Décisions Grill 1:1 (6/6 actées) :
> « 1-D Hybride citations | 2-D Toutes sources+hook | 3-D JSON+fact_dossier | 4-D Blocking new only | 5-D Multiplicateur+richness_penalty | 6-A Legacy exclus »
> ➔ Fait établi : périmètre = EPIC 10→18 (code parfait), EPIC 1-9 legacy intouché.

> Extrait 4 — `critic.py` (détecteur contextualisation, l.117-124) :
> « if "## Critères d'acceptation" not in content and "## Contexte métier" not in content: critical_flaws.append(...) »
> ➔ Fait établi : headings **exacts** H2 requis — variances de casse/numérotation rejetées.

> Extrait 5 — `critic.py` (détecteur OQ exemption, l.303-309) :
> « has_oq = bool(re.search(r"\bOQ-\d{3,4}\b", content)) ... has_deferred_marker = "[API de soumission à définir]" in content or ... »
> ➔ Fait établi : regex exige **chiffres** (`OQ-001`, pas `OQ-XXX`) + marqueur différé.

> Extrait 6 — `state_machine.py` (anti-tampering, l.488-497) :
> « if not stored_hash or status not in ("READY_FOR_GROOMING", "READY_FOR_DEV"): return True ; if current_hash != stored_hash: raise ContentTamperingError »
> ➔ Fait établi : hash frontmatter obligatoire après édition sur statuts READY_* — ré-estampillage `stamp_content_hash` requis.

## 🗄️ 3. Périmètre Structurel

- **Composant modifié** : `src/pipelines/evidence_pack.py` — classe `EvidencePackEngine`, méthode `extract_evidence` + helpers.
- **Champs ajoutés (5, tous `Optional`)** :
  1. `verbatim_extracts: Optional[List[VerbatimExtract]]` — `{source_file, lines, quote, established_fact}`
  2. `implementation_decisions: Optional[List[ImplementationDecision]]` — `{decision_id, category, rationale, alternatives_considered, timestamp}`
  3. `declarative_contracts: Optional[List[DeclarativeContract]]`
  4. `epistemic_audit.what_it_does_not_prove` — exigé non vide pour `VALIDATED`
  5. `conflict_matrix: Optional[List[ConflictResolution]]`
- **Non impacté** : gabarits, CLI registry, autres pipelines.

## 🎯 4. Contrats Déclaratifs Cibles

- **Aucune route HTTP** — extension schema interne (exemption ADR-0319 actée, `OQ-001` de repli si découverte fortuite).
- **Hook API Python** : `record_decision(category, rationale, alternatives) -> ImplementationDecision` (public, dédoublonnage hash).

## 🏁 5. Évaluation de la Frontière Active (Admission of Limits)

- **Ce que le dossier PROUVE** : existence de l'écart, structure du schema cible, 6 décisions PO, contraintes des détecteurs existants.
- **Ce qu'il ne PRUVE PAS** : performance du schema étendu sur 100+ packs, rétrocompatibilité réelle avec les 71 packs (testé en Phase 3 seulement), format natif du tournoi multi-draft.
- **Frontière** : ce dossier couvre le **cadrage** (Phase 2) — la validation code appartient à MLOOP-180-BE (Phase 3).
