---
dossier_id: MLOOP-171-BE_fact_dossier
story_id: MLOOP-171-BE
dossier_status: CURRENT
created_at: "2026-09-22"
sources_hashes:
  epic_modular_refactoring_ast_debt.md: "pending"
---

# Dossier de Preuves Documentaires — MLOOP-171-BE

## 🧭 1. Sources Physiques & Matrice de Vérité

| Source | Type | Rôle | Statut |
| :--- | :---: | :--- | :--- |
| `backlog/epic_modular_refactoring_ast_debt.md` (§2) | Épic | Cartographie & priorisation 39 modules | ✅ CURRENT |
| Audit AST frais (22/09) | Session | Top `_registry.py` 2028L, `server.py` 1632L, `svg_to_md.py` 991L | ✅ Vérifié |
| Grill-Me 1:1 (5/5 OQ) | Séance PO | Arbitrages verbatim sur blast radius et ordre de lot | ✅ Acté |
| Rubber Duck Sentinel | Rapport | 🟢 CONFORME (Prêt pour Dev) | ✅ APPROUVÉ |

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

> Extrait 1 — Cadrage EPIC-17 (§2) :
> « Cartographie & Priorisation des 39 Modules en Dépassement (blast radius) »
> ➔ Fait établi : périmètre = 39 fichiers en violation RULE-AST-01 (hors pilote 170).

> Extrait 2 — Top modules critiques (audit frais) :
> « `_registry.py` 2028L, `server.py` 1632L, `svg_to_md.py` 991L »
> ➔ Fait établi : 3 cibles >900L identifiées pour priorisation par blast radius.

> Extrait 3 — Arbitrages Grill-Me (5/5 OQ résolues, séance 22/09) :
> « 🟢 Grillée (5/5 OQ) » — statut `READY_FOR_GROOMING`, `grill_me: DONE`
> ➔ Fait établi : frontière de cadrage close, aucun OQ résiduel ouvert.

> Extrait 4 — Verdict Sentinel (rubber_duck_MLOOP-171-BE.md) :
> « 🟢 CONFORME (Prêt pour Dev) » — 0 problème bloquant
> ➔ Fait établi : DoR Sentinel satisfait pour passage Palier 2.

## 🗄️ 3. Périmètre Structurel

- **Livrable** : matrice de priorisation des 39 modules (blast radius ascendant/descendant) + ordre de lots.
- **Non impacté** : exécution des refactors (170 pilote + 172 pattern), `_registry.py` (routé récit dédié MLOOP-111-BE selon FRAMEWORK_STATE).

## 🎯 4. Contrats Déclaratifs Cibles

- **Aucune route HTTP** — composant d'analyse interne (exemption ADR-0319 : `OQ-171` + `[API de soumission à définir]` si route découverte).

## 🏁 5. Évaluation de la Frontière Active (Admission of Limits)

- **Ce que le dossier PROUVE** : volume 39 modules, top 3 critiques, 5 arbitrages PO, verdict Sentinel.
- **Ce qu'il ne PRUVE PAS** : l'ordre de lot final (produit en Phase 3), le blast radius calculé réellement (méthode à exécuter).
- **Frontière** : cadrage Phase 2 — le calcul de blast radius et la publication de la matrice appartiennent à MLOOP-171-BE (Phase 3).
