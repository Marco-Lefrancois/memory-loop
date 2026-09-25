---
dossier_id: MLOOP-181-BE_fact_dossier
story_id: MLOOP-181-BE
dossier_status: CURRENT
created_at: "2026-09-22"
sources_hashes:
  epic_evidence_impl_decisions.md: "pending"
  state_machine.py: "pending"
  evidence_pack.py: "pending"
---

# Dossier de Preuves Documentaires — MLOOP-181-BE

## 🧭 1. Sources Physiques & Matrice de Vérité

| Source | Type | Rôle | Statut |
| :--- | :---: | :--- | :--- |
| `backlog/epic_evidence_impl_decisions.md` | Épic | 5 champs de parité + 6 décisions actées | ✅ CURRENT |
| `backlog/stories/MLOOP-180-BE.md` | Story amont | Schema cible (bloquant, `blocked_by` de 181) | ✅ READY_FOR_GROOMING |
| `src/pipelines/state_machine.py` | Code | Harnais Phase 3 : `stamp_content_hash`, `validate_content_integrity`, FSM transitions | ✅ Vérifié |
| `src/pipelines/evidence_pack.py` | Code | `EvidencePackEngine.extract_evidence` — point d'intégration | ✅ Vérifié |
| `src/engine/rubber_duck/critic.py` | Code | Détecteurs de richesse (Gate 5, ADR-0319, Gherkin) | ✅ Vérifié |
| Décisions Grill 1:1 (6/6, 22/09) | Séance PO | Arbitrages verbatim (D hybride, TDD+hook, JSON+dossier, blocking new only, multiplicateur, legacy exclu) | ✅ Actées |

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

> Extrait 1 — Décision 4 (Gate 5) appliquée au harnais :
> « Gate 5 **blocking new only** — legacy EPIC 10→17 exempté (warning), nouveau `DONE_TESTED`+ exige ≥1 citation »
> ➔ Fait établi : l'intégration doit brancher un gate **rétrocompatible** — pas de blocage rétroactif sur les 71 packs legacy.

> Extrait 2 — Décision 5 (Confiance) :
> « multiplicateur `score × (0.7 + 0.3 × min(1, richesse/max))` + `richness_penalty` dans `epistemic_audit` »
> ➔ Fait établi : la dérivée de confiance est **déterministe et traçable** — le harnais doit exposer `richness_penalty` dans l'audit, pas le calcul en silence.

> Extrait 3 — Décision 3 (Emplacement) :
> « `implementation_decisions` dans `<SID>_evidence.json`, `verbatim_extracts` dans `<SID>_fact_dossier.md` »
> ➔ Fait établi : **double écriture** — le harnais Phase 3 doit écrire aux deux emplacements (JSON sidecar + Markdown fact_dossier).

> Extrait 4 — `state_machine.py` (integrity, l.488-497) :
> « if current_hash != stored_hash: raise ContentTamperingError »
> ➔ Fait établi : toute régénération de pack après édition exige `stamp_content_hash` — le harnais doit préserver cet ordre (éditer → stamper → sync).

> Extrait 5 — Dépendance structurelle :
> « MLOOP-181-BE blocked_by: MLOOP-180-BE »
> ➔ Fait établi : intégration **impossible avant** le schema de 180 — séquence stricte imposée par le frontmatter.

## 🗄️ 3. Périmètre Structurel

- **Composant** : `src/pipelines/evidence_pack.py` (hooks d'intégration) + `src/pipelines/state_machine.py` (gates).
- **Branchements** : 5 champs du schema 180 → validation Gate 5 rétrocompatible + calcul `richness_penalty` + double écriture citations/décisions.
- **Non impacté** : schema 180 (livré par amont), 71 packs legacy (exemptés), gabarits, CLI registry.

## 🎯 4. Contrats Déclaratifs Cibles

- **Aucune route HTTP** — extension du pipeline interne d'EvidencePack (exemption ADR-0319 : `OQ-001` de repli, `[API de soumission à définir]`).
- **Hooks Python** : `extract_evidence(story_file)` enrichi, `stamp_content_hash(path)` préservé, gate Gate 5 en warning legacy / blocking nouveau.

## 🏁 5. Évaluation de la Frontière Active (Admission of Limits)

- **Ce que le dossier PROUVE** : séquence d'intégration (bloqué par 180), formule de confiance exacte, double emplacement, contrainte anti-tampering, rétrocompatibilité legacy exigée.
- **Ce qu'il ne PRUVE PAS** : que les 5 champs survivent à une régénération sur 100+ packs (test Phase 3), le coût de perf du double écrit, le comportement FSM sur les transitions intermédiaires.
- **Frontière** : cadrage Phase 2 — l'exécution des hooks et les tests d'intégration appartiennent à MLOOP-181-BE (Phase 3).
