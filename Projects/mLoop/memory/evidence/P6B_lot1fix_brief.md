# Brief Mission P6-B2 — Création des 2 ébauches DRAFT Lot 1 manquantes (db.py + sync.py)

> **Worker** : worker_p6b_lot1fix · **Story ID** : P6B-LOT1FIX · **Task type** : BUILD
> **Contexte** : Grill macro EPIC-17, Option A validée par l'humain — compléter le Lot 1 Beachhead (OQ-171-05 Top 5) avec les 2 fichiers absents des 5 DRAFTs P6-A.
> **Date** : 2026-09-23

---

## 1. Mission (périmètre strict)

Créer **exactement 2 ébauches** au gabarit Palier 1 + mettre à jour 2 artefacts de suivi. **Aucune autre modification.**

### 1.1 Stories à créer

| ID cible | Composant | Lignes | Ko | BR | Lot | Cas protocole | blocked_by |
|:---------|:----------|-------:|---:|---:|:---:|:--------------|:-----------|
| **MLOOP-178-BE** | `src/loop_mem/db.py` | 956 | 36.6 | **20** | Lot 1 | Cas général §2 (famille DB/SQLite) + ADR-0369 context managers | `["MLOOP-172-BE"]` |
| **MLOOP-179-BE** | `src/pipelines/sync.py` | 542 | 22.7 | **10** | Lot 1 | Cas général §2 (famille Sync/Jira/Git) + ADR-0369 timeouts | `["MLOOP-172-BE"]` |

**Vérification préalable obligatoire** : `Test-Path` sur les 2 IDs — s'ils existent déjà, STOP et rapporter (ne pas écraser).

### 1.2 Gabarit & frontmatter obligatoires

- Fichier : `Projects/mLoop/backlog/stories/<ID>.md`
- Gabarit SSOT : `standards/blueprints/story_draft_template.md` (ADR-0375 — aucun autre template)
- Frontmatter exigé :
  - `id: MLOOP-17X-BE`
  - `jira_key: ""`
  - `epic_key: EPIC-17-MODULAR-REFACTORING`
  - `type: refactor`
  - `title: "<Titre métier pur — pas de clé Jira dans le H1>"` (H1 = titre pur identique)
  - `origin: "SPEC_SLICING"`
  - `source_ref: "EPIC-17 · epic17_prioritization_matrix.md · Rang #N BR · OQ-171-05 Lot 1 Top 5"`
  - `macro_size: "M"` (178) / `"S"` (179)
  - `status: DRAFT`
  - `grill_me: PENDING`
  - `invest_score: 0/6`
  - `layer: backend`
  - `blocked_by: ["MLOOP-172-BE"]`
  - `created_at: "2026-09-23"`

### 1.3 Structure des 2 récits (calquer sur MLOOP-173-BE.md comme référence P6-A)

Sections séparées par `---` :
1. **Intention Métier** (En tant que / je veux / afin de) — citer lignes, BR, plafond 300L, non-régression callers.
2. **Origine & Cadrage** — matrice (rang #2 pour db, #3 pour sync), `MODULAR_EXTRACTION_PROTOCOL.md` §2 cas général, hypothèse de découpe réaliste.
3. **Périmètre Sommaire** — In-Scope (cartographie, package + sous-modules ≤300L, shim ré-export, smoke check, tests, plan) / Out-of-Scope (modif callers, refactoring fonctionnel, autres récits EPIC-17).
4. **Critères de Succès Préliminaires** — checkboxes : code-check ≤300L/15Ko, shim import OK, import_smoke_check vert, pytest N_après ≥ N_avant 0 FAIL, plan archivé `memory/plan/implementation_plan_<ID>.md`.
5. **§5 Questions Grill-Me 1:1** — **5 questions atomiques minimum** chacune, adaptées au module :
   - **178 db.py** : frontière connection pool vs queries ; effets de bord import (connexions globales ?) ; rollback BR=20 ; séquençage vs state.py ; ADR-0369 `with` sur 100% des accès SQLite.
   - **179 sync.py** : famille Git vs Jira vs hypergraphe ; timeouts réseau obligatoires ; rollback BR=10 ; séquençage vs db.py ; dépendances sur state/lifecycle.

Citer dans §2 le lien texte : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` + le cas applicable.

### 1.4 Artefacts de suivi à MAJ (sans écraser l'existant)

1. **`Projects/mLoop/backlog/sprint_backlog.md`** — ajouter **2 lignes** `[ ]` juste après MLOOP-177-BE (même format de colonnes que 173-177) :
   - `| [ ] | **MLOOP-178-BE** | - | LoopMem/DB | Extraction Modulaire de src/loop_mem/db.py — Couche SQLite (BR=20) | \`DRAFT\` | ⚪ Grill-Me PENDING |`
   - `| [ ] | **MLOOP-179-BE** | - | Pipelines/Sync | Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10) | \`DRAFT\` | ⚪ Grill-Me PENDING |`
2. **`Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md`** :
   - Registre : réaffecter les lignes résiduelles — remplacer la mention `db.py, sync.py` dans la ligne `9+ (a decouper)` par deux entrées DRAFT **avant** la ligne résiduelle, OU ajouter les 2 lignes dans la matrice de traçabilité + 2 sections détaillées §9-§10 (calque §4-§8), en **conservant intactes** toutes les lignes `DONE`/`DONE_TESTED` (170, 171, 172) et les DRAFT 173-177.
   - Ne PAS supprimer la ligne résiduelle 9+ : la réécrire si besoin pour ne plus lister db/sync (ex: `32 fichiers BR 2-7 restants` sans db/sync).
3. **`Projects/mLoop/memory/evidence/P6B_lot1fix_report.md`** — rapport court : table des 2 IDs, tailles/BR match matrice, contraintes respectées, **dernière ligne exacte `STATUS: DONE`**.

### 1.5 Données matrice (vérité — epic17_prioritization_matrix.md)

- Rang #2 : `src/loop_mem/db.py` | 956 | 36.6 | BR 20 | Lot 1 | coeur
- Rang #3 : `src/pipelines/sync.py` | 542 | 22.7 | BR 10 | Lot 1 | coeur

---

## 2. Interdictions (Bornes)

- **Zéro** `git commit` / `git push`
- **Zéro** modification des stories 170-177, du protocole, des ADR, de `ast_checker.py`
- **Zéro** promotion `READY_FOR_DEV` / exécution `grill-me` / attribution INVEST > 0
- **Zéro** toucher MLOOP-180/181/182 (EPIC-18)
- **Zéro** chemin local `C:\...` dans le corps des récits (liens relatifs ou HTTPS)
- **Zéro** titre H1 avec clé Jira entre parenthèses
- **Zéro** JSON fictif / fausse route API
- Si une write opencode bloque (`Preparing write…`) : annuler et relancer write par write ; si persiste après 2 nudges, rapporter BLOCKED sans inventer de contenu partiel.
- ADR-0369 : pas de `except pass` nu si tu ajoutes le moindre code Python (norme : tu n'écris que du Markdown ici).
- Respect UTF-8 ; après write, vérifier `Get-Content -Tail 1` du rapport = `STATUS: DONE`.

---

## 3. Livrables d'acceptation (orchestrateur vérifiera)

- [ ] `Projects/mLoop/backlog/stories/MLOOP-178-BE.md` existe · DRAFT/PENDING/0/6 · 5 questions §5
- [ ] `Projects/mLoop/backlog/stories/MLOOP-179-BE.md` existe · DRAFT/PENDING/0/6 · 5 questions §5
- [ ] `sprint_backlog.md` : 2 nouvelles lignes DRAFT (7 DRAFTs EPIC-17 visibles : 173-179)
- [ ] `epic_modular_refactoring_ast_debt.md` : 2 entrées + sections, DONE préservés
- [ ] `memory/evidence/P6B_lot1fix_report.md` · dernière ligne `STATUS: DONE`
- [ ] Aucun autre fichier modifié

**Ordre d'exécution recommandé** : Test-Path → 178 → 179 → sprint → épopée → rapport → message final `P6-B2 STATUS: DONE`.
