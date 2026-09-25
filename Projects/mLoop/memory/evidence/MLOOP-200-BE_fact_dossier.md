# Dossier de Preuves — MLOOP-200-BE

> Protocole : DOSSIER_DE_PREUVES_PROTOCOL · ADR-0320 / ADR-0326 / ADR-0361
> Session Grill-Me 1:1 : 2026-09-23 · Frontière épuisée (Q1, Q2, Q3, Q3b)

---

## 1. Sources SSOT & Notes

- **Directives projet** : `Projects/mLoop/directives/` — **absentes** (mLoop = projet framework interne).
- **Hiérarchie SSOT retenue** : Canonique `src/core/lifecycle/` (code) > Protocole `standards/protocols/PROJECT_LIFECYCLE_STAGES.md` > État disque `Projects/*/memory/lifecycle_state.json`.
- **Fact-Search FTS5** : 5 preuves (score max 47.4) — `gates_ingest.template.md` (OWNS lifecycle_state), `PROJECT_LIFECYCLE_STAGES.md` (Grill-Me micro), audits Phase 4.

---

## 2. Matrice de Résolution des Conflits

| Conflit | Affermation initiale | Vérification | Résolution |
| :--- | :--- | :--- | :--- |
| « 3 parse errors bloquants » | Draft §5 / inventaire | Relecture `ConvertFrom-Json` sur 4 fichiers : **tous JSON valides** | **Faux positif outil** (dates ISO+timezone PowerShell) — pas de dette schema |
| Stage BoireFrere = nommage erroné | Guess agent : alias obsolete | Humain : *« STAGE2 est pour le module Incubation »* | **Sémantique module conducteur** — pas un bug de nommage |
| Metro_FOOD `STAGE_0` vs CLI Phase 2 | Fichier = vérité ? | CLI + sprint_backlog (30 stories, Gate 2 EN COURS) | **CLI + backlog gagnent** — JSON à reconstruire |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `_lc_transitions.py` migration legacy (L44-62)** :
« `raw_stage = data.get("current_stage")` … `data["current_stage"] = ProjectLifecycleStage.STAGE_2_PLAN_ANALYSE.value` »
➔ Fait établi : le moteur connaît déjà une remontée de stage legacy — mais **inutilisée** pour Metro_* (fichiers jamais alimentés depuis init).

**Extrait 2 — Relecture JSON 23/09/2026** :
« `Metro_FOOD … JSON OK (len=204) stage=STAGE_0_TSHIRT` » / « `mLoop … JSON OK (len=1377) stage=STAGE_5_SHIP` »
➔ Fait établi : déséquilibre **données** (gates absentes), pas corruption structurelle.

**Extrait 3 — `PROJECT_LIFECYCLE_STAGES.md` L56-66** :
« Grill-Me Micro 1:1 … produit le récit haute-fidélité (`status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6) »
➔ Fait établi : process de promotion canonique — prerequisite de cette story.

**Extrait 4 — Décision humaine (Q1, 23/09/2026)** :
« A » → reconstruction JSON depuis CLI/backlog, zéro re-gate rétroactive.
➔ Décision PO : source de vérité = preuves de phase, pas le fichier amont.

**Extrait 5 — Décision humaine (Q3b, 23/09/2026)** :
« A — STAGE2 = module Incubation » + validation option A agent.
➔ Décision PO : BoireFrere conserve la sémantique **module conducteur** ; sémantique documentée.

**Extrait 6 — `_lc_transitions.py` `get_state` (L44-60), établi à l'exécution 24/09/2026** :
« `if raw_stage == "STAGE_0_TSHIRT"` … `has_work = sprint_file.exists() or …` … `data["current_stage"] = STAGE_2_PLAN_ANALYSE.value if has_work else STAGE_1_INGEST.value` » — **sans appel à `save_state`**.
➔ Fait établi (NOUVEAU) : `lifecycle-status` est **read-only** sur le fichier. Il dérive le stage canonique en mémoire à partir de la présence du backlog ; il **ne matérialise jamais** le stage sur disque. Prouvé empiriquement : SHA-256 de `Metro_FOOD/lifecycle_state.json` **identique** (`f1689078…`) avant et après un appel `lifecycle-status`. C'est la cause racine du décalage badge/fichier pour les 3 Metro (`STAGE_0_TSHIRT` sur disque, `STAGE_2` à l'affichage).

**Extrait 7 — `_lc_gates.py` `approve_gate` (L148-151), 24/09/2026** :
« `state.gates[str(gate_number)] = record` … `state.current_stage = next_stage` ».
➔ Fait établi : seul `approve_gate` matérialise une gate et fait avancer `current_stage` sur disque. Aucune gate n'ayant été franchie via `approve_gate` pour les 3 Metro (Gate 0/1 VERROUILLÉES au CLI), la reconstruction écrit `gates: {}` — zéro gate inventée.

---

## 4. Contrats Déclaratifs Cibles

- **Aucun contrat API/CTA** — story purement gouvernance d'état local (fichiers JSON sous `Projects/*/memory/`).
- **Contrat fichier** : `lifecycle_state.json` conforme `_lc_models.py` (`current_stage`, `gates{}`, timestamps) ; écriture via chemins du moteur lifecycle **uniquement en réécriture de données** (pas de modif `src/`).

---

## 5. Frontière Active & Admission of Limits

- **Ne prouve pas** : que `STAGE_2_PLAN_GRILL` est un alias universel déprécié sur d'autres projets (seul BoireFrere concerné par le fait module).
- **Ne prouve pas** : l'absence totale de parse error sur d'autres projets passifs (HTC archivé, App_Sante sans lifecycle).
- **Hors périmètre** : moteur lifecycle, promotion de récits, multi-lifecycle par module (ADR éventuelle séparée).
- **Risque résiduel** : promotion de stage sans `gate-approve` historique — mitigé par traçage delta EvidencePack + approbation humaine de ce récit.

---

## 6. Journal d'Exécution (24/09/2026)

- **Réalignés (3)** : Metro_FOOD, Metro_COMMERCE, Metro_SANTE — `STAGE_0_TSHIRT` → `STAGE_2_PLAN_ANALYSE`, `gates: {}` (aucune gate prouvée). `project_name` et `created_at_utc` préservés.
- **Intacts (2)** : BoireFrere_Segment2 (`STAGE_2_PLAN_GRILL` + gates 0/1, sémantique module conducteur Incubation conservée) et Shopify_AI_Item_Creator (`STAGE_2_PLAN_GRILL` + gate 1) — déjà cohérents avec la preuve CLI (canonical = STAGE_2_PLAN_ANALYSE), zéro écriture destructive.
- **Exceptions (0)** : aucune preuve absente/contradictoire, aucun fichier hors schéma.
- **Validation post-correction** : `lifecycle-status` réexécuté sur les 3 Metro → STAGE_2_PLAN_ANALYSE, exit 0, aucun échec bloquant.
- **Astreintes** : aucune écriture sous `src/` ; aucun `git commit`/`push` ; PowerShell sans `&&` ; `subprocess` (via CLI mLoop) bornés par timeout explicite ; un `lifecycle-status` à la fois.

---

*Généré : 2026-09-23 · Exécuté : 2026-09-24 · Story : MLOOP-200-BE · Grill : COMPLETE · Exécution : EXECUTED*
