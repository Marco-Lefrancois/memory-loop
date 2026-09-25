# Dossier de Preuves — Grill Macro EPIC-17 (Décisions Q1→Q4)

> **Session** : `grill-project` Étape 2 — 2026-09-23
> **Périmètre** : Décisions transverses Lot 1 / Lot 3 avant micro-grill des 7 ébauches DRAFT
> **Frontière** : Épuisée (4/4 questions atomiques tranchées, zéro zone d'ombre macro restante)

---

## Matrice de Résolution des Décisions

| Q | Sujet | Décision | Rationnel |
|:-:|:------|:---------|:----------|
| Q1 | Création DRAFTs manquantes Lot 1 | **A — Créer MLOOP-178-BE + MLOOP-179-BE** | Blindspot P6-A : 3/5 du Lot 1 seulement (db BR=20 rang #2 et sync BR=10 rang #3 absents de la matrice Beachhead OQ-171-05). |
| Q2 | Séquençage + parallélisme + gel Lot 3 | **A — Séquence stricte 1-par-1 Beachhead, Lot 3 gelé** | Ordre `state(78) → db(20) → sync(10) → lifecycle(8) → _registry(3)` ; un worker à la fois ; smoke check vert avant le suivant. Cohérent `blocked_by` écrits (174→173, 179→178). Évite shims concurrents sur `state.py` singleton BR=78. |
| Q3 | Politique de rollback Lot 1 | **A — Revert Git immédiat, 0 FAIL strict, seuil humain BR≥20** | Rollback atomique par revert ; arbitrage humain obligatoire pour `state`(78)/`db`(20) ; autonomie worker pour `sync`(10)/`lifecycle`(8)/`_registry`(3). Zéro tolérance temporaire. |
| Q4 | Critères de sortie Lot 1 (dégel Lot 3) | **A — Barre stricte 5/5** | (1) 5 récits `DONE_TESTED` + Gate 3/EvidencePack ; (2) `code-check --all` = zéro RULE-AST-01 sur les 5 cibles (compteur 39→34) ; (3) pytest complet vert (1306+) ; (4) hypergraphe resyncé. Aucun dégel `svg_to_md`/`server` avant cette barre. |

---

## Extraits Sourcés (Grounding)

**Extrait 1 — Matrice Beachhead OQ-171-05 (epic17_prioritization_matrix.md)**
Lot 1 Top 5 = `state.py` (BR=78) → `db.py` (BR=20) → `sync.py` (BR=10) → `lifecycle.py` (BR=8) → `_registry.py` (BR=3)
➔ Fait établi : l'ordre de priorité par blast radius est déjà SSOT ; Q2 ne fait que confirmer l'exécution séquentielle stricte de CET ordre.

**Extrait 2 — Pilote MLOOP-170-BE (sprint_backlog L208)**
`DONE_TESTED` — 1306 tests verts, 73 miroirs ; extraction vibe_check 880L→package <300L en solo.
➔ Fait établi : le pattern « un module à la fois + suite verte » est validé par le pilote ; Q2/Q4 s'alignent dessus.

**Extrait 3 — frontmatter des ébauches (MLOOP-174-BE, MLOOP-179-BE)**
`blocked_by: ["MLOOP-172-BE"]` et questions §5 « Séquençage vs state.py / vs db.py ».
➔ Fait établi : les récits themselves anticipaient le risque de parallélisme ; Q2 le tranche en faveur du séquentiel.

**Extrait 4 — MODULAR_EXTRACTION_PROTOCOL §2 (SSOT)**
Cas général : smoke check imports + suite tests = N_après PASS = N_avant PASS, 0 FAIL avant merge.
➔ Fait établi : le seuil 0 FAIL est déjà normatif ; Q3 (revert atomique) en est la conséquence opérationnelle.

---

## Frontière Active & Admission of Limits

- **Décidé ici** : ordre d'exécution, mode (séquentiel), rollback, barre de sortie Lot 1, gel Lot 3.
- **Non décidé ici (route micro-grill §5 récit)** : frontières internes de chaque module (pool vs queries, familles Git/Jira/graph, signatures ADR-0369), dépendances fines state/lifecycle par récit, contenu exact des 4 piliers Gherkin et INVEST 6/6.
- **Hors périmètre** : exécution des extractions (P6-C), promotion `READY_FOR_DEV` (humain seul, ADR-0375), Lot 3, EPIC-18.

**STATUS: DONE**
