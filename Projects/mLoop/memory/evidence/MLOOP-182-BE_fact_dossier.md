---
dossier_id: MLOOP-182-BE_fact_dossier
story_id: MLOOP-182-BE
dossier_status: CURRENT
created_at: "2026-09-22"
sources_hashes:
  epic_evidence_impl_decisions.md: "pending"
  evidence_packs_legacy: "pending"
---

# Dossier de Preuves Documentaires — MLOOP-182-BE

## 🧭 1. Sources Physiques & Matrice de Vérité

| Source | Type | Rôle | Statut |
| :--- | :---: | :--- | :--- |
| `backlog/epic_evidence_impl_decisions.md` | Épic | Périmètre backfill EPIC 10→17, décision 4 (legacy exempté) + décision 6 (EPIC 1-9 exclu) | ✅ CURRENT |
| `backlog/stories/MLOOP-180-BE.md` | Story amont | Schema source des 5 champs (bloquant) | ✅ READY_FOR_GROOMING |
| 71 EvidencePacks EPIC 10→17 | Artefacts | Cibles du backfill (régénérés une 1ʳᵉ fois en session antérieure) | ✅ Existant |
| Décisions Grill 1:1 4 + 6 (22/09) | Séance PO | « blocking new only » + « EPIC 1-9 strictement exclus » | ✅ Actées |

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

> Extrait 1 — Décision 6 (Legacy) :
> « **EPIC 1-9 strictement exclus** — focus prioritaire EPIC 10→18, code parfait exigé »
> ➔ Fait établi : le backfill ne touche **jamais** EPIC 1-9 — périmètre borné à EPIC 10→17 uniquement (18 est neuf, déjà conforme).

> Extrait 2 — Décision 4 (Gate 5) appliquée au backfill :
> « legacy EPIC 10→17 exempté (warning) — nouveau `DONE_TESTED`+ exige ≥1 citation »
> ➔ Fait établi : le backfill de 182 **ne doit pas déclencher de blocage Gate 5** sur les packs existants — seul l'audit warning est toléré.

> Extrait 3 — État mesuré des packs (session antérieure) :
> « 43 frontmatter → SHIPPED ; 39 EvidencePacks régénérés (EPIC-10→17) »
> ➔ Fait établi : le backfill structurel est **partiellement déjà fait** — 182 doit compléter (5 champs de parité riches) sans double régénération hasardeuse.

> Extrait 4 — Dépendance structurelle :
> « MLOOP-182-BE blocked_by: MLOOP-180-BE »
> ➔ Fait établi : impossible d'enrichir les packs legacy avec les 5 champs **avant** l'existence du schema (180).

> Extrait 5 — Exigence de richesse (épic §parité) :
> « `verbatim_extracts` ≥1 citation/fichier modifié + ≥1/décision (décision 1 hybride) »
> ➔ Fait établi : le backfill doit injecter des citations granulaires D, pas un placeholder vide.

## 🗄️ 3. Périmètre Structurel

- **Cibles** : 39 fichiers `Projects/mLoop/memory/evidence/<SID>_evidence.json` pour EPIC 10→17 (IDs 100→179, audit disque du 23/09/2026). Les 32 packs legacy (EPIC 1-9 + DEMO/LAB/REC) et les 3 packs du triptyque 180-182 sont hors périmètre — le chiffre « 71 » antérieur comptait à tort l'ensemble des packs hors triptyque.
- **Enrichissement** : injection des 5 champs de parité (granularité hybride décision 1).
- **Non impacté** : EPIC 1-9 (exclus, décision 6), EPIC 18 (neufs, déjà conformes), stories sources, gabarits.

## 🎯 4. Contrats Déclaratifs Cibles

- **Aucune route HTTP** — traitement batch local de JSON sidecars (exemption ADR-0319 : `OQ-001` + `[API de soumission à définir]`).
- **Contrat d'entrée** : schema 180 (amont) ; **contrat de sortie** : packs enrichis 5 champs, Gate 5 en warning seul.

## 🏁 5. Évaluation de la Frontière Active (Admission of Limits)

- **Ce que le dossier PROUVE** : périmètre exact (EPIC 10→17, 71 packs), exemption Gate 5, exclusion EPIC 1-9, dépendance à 180, granularité hybride exigée.
- **Ce qu'il ne PRUVE PAS** : le taux de remplissage réel des citations après backfill (mesuré en Phase 3), l'intégrité des JSON legacy (récupération sur erreur), le temps batch sur 71 fichiers.
- **Frontière** : cadrage Phase 2 — l'exécution du backfill et la validation Gate 5 warning appartiennent à MLOOP-182-BE (Phase 3).
