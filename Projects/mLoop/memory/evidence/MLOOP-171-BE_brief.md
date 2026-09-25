# Brief Worker — MLOOP-171-BE (P5-1)

> **Story** : `Projects/mLoop/backlog/stories/MLOOP-171-BE.md`  
> **Statut** : `IN_ANALYZE` · `grill_me: DONE` · INVEST 6/6 · EPIC-17  
> **Périmètre** : ANALYSE + garde-fou anti-aggravation (OQ-171-02). **Aucun refactoring des 39 fichiers** (hors scope).

---

## 1. Mission

Produire l’inventaire priorisé des fichiers `src/` en dépassement `RULE-AST-01` (plafond 300L / 15 Ko), avec blast radius, matrice Beachhead, **et** implémenter le contrôle anti-aggravation bloquant (delta taille) sur le hook pre-commit + audit `MLOOP_SKIP_HOOKS`.

---

## 2. Livrables (critères d’acceptation du récit)

### A. Inventaire factuel (zéro extrapolation)
1. Exécuter `python src/swarm.py code-check --all` et archiver la sortie sous  
   `Projects/mLoop/memory/evidence/codecheck_audit_epic17.txt`.
2. Extraire **uniquement** les violations `RULE-AST-01` → liste des fichiers uniques avec :
   - chemin relatif `src/...`
   - taille exacte (lignes)
   - taille en Ko (si disponible via le rapport)
3. Compter le total. S’attendre à **~39 fichiers uniques** (audit 2026-09-23 ; si différent, noter l’écart vs 39).
4. **Blast radius par fichier** (nombre de callers / modules qui l’importent) :
   - **Préféré** : `python src/swarm.py graph-query --project mLoop --query "<module>"` ou l’outil CodeGraph/blast-radius si dispo.
   - **Fallback AST déterministe** : compter les imports du module dans `src/` (grep/AST) — **annoter la méthode** (`codegraph` vs `ast_import_count`) dans la matrice (Pilier 3 du récit).

### B. Matrice de priorisation & séquence
- Trier par **blast radius décroissant** (OQ-171-01).
- Colonnes : `fichier | lignes | blast_radius | méthode_br | criticité (cœur/outil) | lot Beachhead`.
- **Séquence Beachhead** (OQ-171-05) en tête de rapport :
  - **Lot 0 — Pilote** : `vibe_check.py` (déjà `DONE_TESTED` via MLOOP-170-BE) → marquer comme fait.
  - **Lot 1 — Top 5 critiques** en récits unitaires (ex. `state.py`, `lifecycle.py`, `_registry.py`, `server.py`, `db.py` selon BR réel).
  - **Lot 2+ — Résidus** en lots adaptatifs.
- Inclure explicitement dans la file (OQ-171-03) :
  - `src/.../archify.py` (~463L, créé hors plafond)
  - `src/.../dashboard/server.py` (~1632L)
- **Zéro dérogation** (OQ-171-04) : plafond 300L strict, `_registry.py` inclus.
- Écrire la matrice dans :
  1. `Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md` (humain-lisible)
  2. Mettre à jour la section Registre / séquence de `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` (ordre de traitement + compte 39).

### C. Garde-fou anti-aggravation (OQ-171-02) — LIVRABLE CODE
**Règle** : rejeter tout commit qui **agrandit** un fichier **déjà** > 300L (ou > 15 Ko). Autoriser les commits neutres ou réducteurs sur un fichier déjà en dette. Bloquer aussi la création d’un nouveau fichier déjà > 300L.

**Points d’intégration existants (ne rien réinventer)** :
1. **Hook template** : `standards/blueprints/git_pre_commit_hook.sh`  
   - Aujourd’hui : `python swarm.py code-check --file` échoue sur RULE-AST-01 si le fichier staged reste >300L → **impossible d’améliorer progressivement** sans `MLOOP_SKIP_HOOKS`.  
   - **Changement** : pour un fichier staged dont la **version HEAD (ou pré-commit)** est **déjà** en dépassement RULE-AST-01, accepter si `nouvelles_lignes <= anciennes_lignes` (et même pour Ko). Rejeter si `nouvelles > anciennes`. Pour un fichier **conforme** à HEAD, conserver le comportement actuel (rejet si passage en dépassement).
2. **Re-render du hook** : `python src/swarm.py install-hooks` (handler `handle_install_hooks` dans `src/commands/handlers/project_core.py` — re-render BlueprintLoader).
3. **Audit `MLOOP_SKIP_HOOKS`** : à chaque bypass, **append** une ligne horodatée dans  
   `Projects/mLoop/memory/evidence/mloop_skip_hooks_audit.log`  
   format ISO-8601 UTC + user + raison si fournie env `MLOOP_SKIP_HOOKS_REASON` (optionnel).  
   Implémenter côté script hook (sh) **et**/ou côté logger Python si le bypass passe par Python.
4. **Vibe-Check** : ajouter/étendre un contrôle `RULE-AST-01-DELTA` (ou équivalent) dans le package `src/pipelines/vibe_check/` qui détecte les fichiers en dépassement ayant grossi entre HEAD et working tree (quand dispo), **en complément** du hook. Si le delta git est trop lourd, limiter à un check documenté + tests.

**Tests obligatoires** (dossier `tests/` existant, style pytest) :
- Fixture fichier >300L qui **grossit** → hook / logique delta → **FAIL**.
- Fichier >300L qui **rétrécit** ou reste identique → **PASS** (ou non-blocage delta).
- Fichier conforme qui devient >300L → **FAIL**.
- Bypass `MLOOP_SKIP_HOOKS=1` → exit 0 **+ ligne d’audit écrite**.
- Couvrir le module Python delta si extrait (`@pytest.mark.parametrize` ADR-0369).

### D. Non-régression
- `python src/swarm.py code-check --all` : **ne doit pas** introduire de nouvelles violations RULE-AST-02/03/04 (P7 vient d’être assaini : 0 sur ces règles).
- Suite ciblée : `pytest tests/test_ast_checker.py tests/test_vibe_check*.py tests/test_*hook*` (adapter aux noms réels) + tout test touchant le nouveau delta → **verts**.
- `python src/swarm.py guide --sync` **si** vous ajoutez/modifiez une commande dans `src/commands/_registry.py` (ADR-0370). Sinon skip.

---

## 3. Contraintes strictes (AGENTS.md / ADR)

| Contrainte | Détail |
|:---|:---|
| **Timeouts** | Tout `subprocess.run`/`Popen`/appel réseau synchrone → `timeout=` **explicite** (ADR-0369). |
| **Context managers** | SQLite/HTTP/sockets en `with` uniquement. |
| **Logging** | Jamais `except: pass` nu → minimum `logger.debug(..., exc_info=True, extra={...})`. |
| **Typage** | `typing.Protocol` pour injection collaborateurs lourds si nouveau module. |
| **Git** | **Aucun `git commit` / `git push`** — le HARVEST n’écrase pas le dépôt, mais ne commitez pas. Laisser les diffs working-tree. |
| **Hors scope** | Ne refactorer AUCUN des 39 fichiers oversized. Ne pas toucher `src/core/ast_checker.py` sans justification ADR-0376 (éviter : implémenter le delta **hors** ast_checker si possible, ou toucher ast_checker uniquement pour un flag delta documenté). |
| **Chemins** | Écrire les artefacts sous `Projects/mLoop/memory/evidence/` (gitignored, OK). |
| **Statut story** | Ne pas changer le frontmatter `status:` de la story (l’orchestrateur gère). |
| **Working dir** | `C:\Memory Loop` (framework root). |

---

## 4. Méthode de fin (DONE)

1. Rapport final écrit : `Projects/mLoop/memory/evidence/MLOOP-171-BE_report.md`  
   sections : Inventaire (N fichiers) · Matrice (tableau) · Séquence Beachhead · Garde-fou (fichiers modifiés, tests) · Méthodes BR · Écarts vs 39 · Risques.
2. Ligne de statut exacte en **dernière ligne** du rapport :  
   `STATUS: DONE` ou `STATUS: BLOCKED — <raison>` .
3. Tous les tests ciblés verts ; `code-check --all` sans nouvelle règle 02/03/04.
4. Ne fermez pas le worker — l’orchestrateur harvestera.

---

## 5. Contexte utile

- Pilote MLOOP-170-BE : `vibe_check.py` déjà découpé (`src/pipelines/vibe_check/`) — DONE_TESTED 2026-09-23.
- Épique : `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md`.
- Hook : `standards/blueprints/git_pre_commit_hook.sh` + install via `install-hooks` (`project_core.py`).
- Code-check handler : `src/commands/handlers/build_harness.py::handle_code_check`.
- ADR : 0202 (≤300L), 0369 (Python senior), 0376 (audit 7 couches si cœur touché), 0370 (guide sync si registry).
- Priorités session : `Projects/mLoop/memory/evidence/priorities_1_8_2026-09-23.md`.
