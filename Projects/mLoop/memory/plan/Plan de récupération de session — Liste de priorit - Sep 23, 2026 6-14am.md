---
created: 2026-09-23T10:14:02.406Z
source: plannotator
tags: [plannotator, memory-loop, cup, ration, session]
---

[[Plannotator Plans]]

# Plan de récupération de session — Liste de priorités 1→8 & état MLOOP-170

**Projet** : mLoop · **Boot Sequence** : `resume` ✅ · `vibe-check` 21 PASS/1 WARNING ✅ · `focus MLOOP-170-BE` ✅  
**Date** : 2026-09-23 · **Phase** : STAGE_5_SHIP

---

## 0. Constat de perte & ce qui a été retrouvé sur disque

La liste de priorités **1→8** n'a **pas été persistée** nulle part (ni `memory/`, ni `backlog/`, ni EvidencePack, ni FTS5). Elle a été perdue avec la session Sentinel One. En revanche, la **source** que vous avez collée et l'état physique du dépôt permettent de la **reconstruire fidèlement**.

### Ce qui existe encore (vérifié)
| Artefact | État |
|---|---|
| Audit source 2026-09-22 (P1→P4 explicites) | ✅ Fourni en message |
| Récit `MLOOP-170-BE` + Fact Dossier + EvidencePack + Rubber Duck | ✅ VALIDATED / CONFORME |
| **Refactoring physique de `vibe_check.py`** | ✅ **FAIT** — package `src/pipelines/vibe_check/` (7 modules, max 245L) + shim 5L |
| Tests `vibe_check` (37) + `guide_parity` (5) + e2e/ingest (9+1 skip) + drawdb (6) | ✅ **Tous VERTS** au moment du diagnostic |
| Audit AST `codecheck_audit_epic17.txt` | ✅ Dette 83 violations confirmée |
| Dernier commit HEAD | `0b4dc4d` (22/09) — **intègre** |

### ⚠️ Anomalies critiques découvertes à l'ouverture
1. **Git index sabordé** : **1068/1068 fichiers HEAD staged en suppression** (`D `), index vide (`git ls-files` = 0), worktree intact (~103k fichiers dont le package vibe_check **non suivi**). Un `commit` accidentel détruirait le dépôt.
2. **Corruption `sprint_backlog.md` L1** : préfixe parasite `oui# Sprint Backlog` (injection session perdue).
3. **`agent_resilience.py`** : BOM `U+FEFF` → `RULE-AST-SYNTAX` (Python 3 le tolère en import, le linter AST non).
4. **MLOOP-170-BE** : travail livré mais statut bloqué à `READY_FOR_GROOMING`, `invest_score: 0/6`, `blocked_by: MLOOP-171` alors que le pilote est terminé.

---

## 1. Liste de priorités 1→8 — Reconstruction ancrée source

> **Provenance** : P1–P4 = §4 de l'audit 22/09 (verbatim). P5–P8 = dérivation forcée des §2B/§3 « restes incohérents » + backlog SSOT actuel. **À valider PO avant exécution.**

| # | Priorité | Source | État constaté ce jour |
|---|---|---|---|
| **1** | 🔴 **Corriger les tests FAIL** (parité CLI + E2E + ingest + drawdb) | Audit P1 | 🟢 **Quasi-gelé** : guide_parity 5/5, e2e 9/9, ingest OK, drawdb 6/6 — **à re-confirmer par run complet `pytest`** |
| **2** | 🟡 **Clôture MLOOP-170-BE** (pilote EPIC-17 `vibe_check` 880L→package) | Audit P2 + constat disque | 🟠 **Code FAIT, récit non clôturé** (statut/invest/blocked_by à aligner, preuves à sceller, commit à préparer) |
| **3** | 🟡 **Implémenter MLOOP-152-BE** (DrawDB souverain Cockpit) | Audit P3 | ⚪ `READY_FOR_DEV`, jamais démarré (EPIC-16) |
| **4** | 🟢 **RULE-AST-02 `httpx.AsyncClient` nus dans `llm_client.py`** | Audit P4 | ⚪ Confirmé L66/L81 dans l'audit AST frais |
| **5** | 🟡 **EPIC-17 suite : MLOOP-171 (cartographie 39 modules) → MLOOP-172 (pattern d'extraction)** | Audit §3 (48 modules >300L) + épopée | ⚪ Les deux récits `READY_FOR_GROOMING` / grillés, pas d'exécution |
| **6** | 🟡 **Monolithes critiques restants** : `_registry.py` 2028L · `server.py` 1632L · `svg_to_md.py` 991L · `lifecycle.py` 852L · `state.py` 770L | Audit §3 + `codecheck_audit_epic17.txt` | ⚪ Intacts, hors pilote |
| **7** | 🟢 **Résidus AST ADR-0369** : RULE-AST-03 (`subprocess` sans `timeout` : `mcp_crawler`, `plannotator`, `herdr_daemon`) · RULE-AST-02 (`sqlite3.connect` nus) · RULE-AST-04 (`struct_checker` except silencieux) · **BOM `agent_resilience.py`** | Audit §3 + codecheck | ⚪ Non traités |
| **8** | 🟡 **EPIC-18 parité EvidencePack** : MLOOP-180 (`IN_QA` BUILD vert) → 181 → 182 | Backlog SSOT (étape d'après P1–P7) | 🟠 180 en QA, 181/182 `READY_FOR_DEV` |

**Arbitrage ordre 2 vs 1** : l'audit plaçait P1 avant P2 ; l'état réel inverse partiellement (P1 probablement vert). La **re-confirmation P1 (run pytest complet)** ouvre la clôture propre de P2.

---

## 2. Actions du plan (séquence)

### A. 🔴 URGENT — Réparation Git (bloquant, Niveau 2)
1. `git reset` (mixed) pour désindexer les **1068 suppressions** et relier le worktree à HEAD — **aucun `commit`, aucun `push`**.
2. Re-vérifier : `git ls-files | Measure` = 1068, `git status` montre bien les vrais deltas (package `vibe_check/` en `??` ou `A`, shim en `M`).
3. **Ne rien committer** tant que vous n'avez pas validé le diff.

### B. 🧹 Hygiène SSOT bloquée
4. Réparer `Projects/mLoop/backlog/sprint_backlog.md` L1 : `oui# Sprint Backlog` → `# Sprint Backlog`.
5. Neutraliser le BOM de `src/pipelines/agent_resilience.py` (réécriture UTF-8 sans sig) pour effacer `RULE-AST-SYNTAX`.

### C. ✅ P1 — Re-confIRMATION tests
6. Lancer la suite complète `python -m pytest tests/ -q` (timeout borné) et consigner le vrai compteur face aux `1215/1220 PASS` de l'audit.
7. Si régressions résiduelles > 0 : correctifs ciblés (hors délégation si ≤ 2 fichiers ; sinon `worker-spawn`).

### D. ✅ P2 — Clôture MLOOP-170-BE (récit déjà grillé)
8. Mettre à jour le frontmatter : `status` → transition valide vers `DONE_TESTED` (ou `IN_DEV`→`DONE_TESTED` selon state machine), `invest_score` réévalué, retirer/assouplir `blocked_by: MLOOP-171` (OQ-170-02 a déjà autorisé le démarrage immédiat ; le pilote est livré).
9. Cohérence `sprint_backlog.md` (statut + case à cocher).
10. Sceller les critères du récit dans l'EvidencePack (modules <300L ✅, signature `run_vibe_check` ✅, 19 callers inchangés ✅, tests verts ✅) + plan d'implémentation court archivé `memory/plan/implementation_plan_MLOOP-170-BE.md` si exigé par FRAMEWORK_STATE.
11. `vibe-check` + `sync` post-maj.

### E. 📋 Suites (hors ce tour sauf feu vert)
12. **P3** MLOOP-152-BE · **P5** déclencher MLOOP-171/172 · **P4/P7** correctifs AST ciblés · **P8** EPIC-18 — chacun en respectant DELEGATION GATE et Plan-First Niveau 3 si ≥ 3 fichiers.

---

## 3. Périmètre & garde-fous

- **In** : réparation index git, réparation `sprint_backlog` L1, BOM, run de confirmation P1, clôture documentaire MLOOP-170, reconstruction validée de la liste 1→8.
- **Out** : tout `git commit/push`, démarrage DrawDB (P3), refactors des 39 modules (P5–P6), EPIC-18 sans ordre explicite.
- **Questions PO avant go** :
  1. La reconstruction P1→P8 ci-dessus correspond-elle à la liste perdue (ou faut-il réordonner) ?
  2. Autorisez-vous `git reset` immédiat (sans commit) ?
  3. MLOOP-170 → statut cible `DONE_TESTED` une fois preuves scellées, ou `IN_DEV` d'abord ?

---

## 4. Définition de fait (ce tour)

- [ ] Index git réparé (0 suppression staged, HEAD intact)
- [ ] `sprint_backlog.md` L1 réparé
- [ ] BOM `agent_resilience.py` effacé
- [ ] Compteur pytest complet consigné vs audit
- [ ] Liste 1→8 validée PO et persistée (EvidencePack / `memory/`)
- [ ] MLOOP-170-BE : statut + critères + EvidencePack alignés sur le code livré
