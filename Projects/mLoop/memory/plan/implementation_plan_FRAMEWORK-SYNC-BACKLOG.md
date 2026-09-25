---
id: PLAN-SYNC-SSOT-ALIGN
story_id: FRAMEWORK-SELFDEV-SYNC-BACKLOG
status: DRAFT # DRAFT | APPROVED | EXECUTING | COMPLETED
harness: opencode
created_at: 2026-09-24
---

# Réalignement SSOT du sprint backlog : parsing colonne-aware, vocabulaire complet et purge du monolithe mort

> **Objectif** : Corriger le défaut de synchronisation `sync_sprint_backlog` qui aligne les frontmatter des récits sur `sprint_backlog.md` — le regex actuel cherche le premier jeton de statut **sur toute la ligne** (ordre des colonnes non respecté, faux positifs depuis le titre) et ignore les vocabulaires réellement présents (`DONE_TESTED`, `FAIT`, `PENDING`, `TOMBSTONE`, `DRAFT`) — puis supprimer le monolithe orphelin `src/pipelines/sync.py` (542 L) entièrement masqué par le package `sync/` depuis la migration MLOOP-179-BE, et corriger les cibles de mock des tests qui patchent le mauvais namespace (les mocks sont inertes aujourd'hui ; les tests ne passent que parce que la vraie fonction est no-op sur des répertoires vides).

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes ou impacts majeurs nécessitant une confirmation explicite de l'utilisateur :**
> - **Suppression de `src/pipelines/sync.py` (542 L)** : le package `src/pipelines/sync/` masque entièrement le module (vérifié : `import src.pipelines.sync` → `__init__.py`, zéro importer ne peut atteindre `sync.py`). Aucune rupture d'import possible. Fichier déjà référencé comme obsolète dans `PHASE_FILES_AND_TEST_PLAN.md`.
> - **Changement de comportement de `sync_sprint_backlog`** : après fix, les récits `DRAFT`/`DONE_TESTED`/`FAIT`/`PENDING`/`TOMBSTONE` du backlog seront **réalignés** sur leur frontmatter (aujourd'hui ignorés silencieusement). Risque : une ligne dont le titre contient un mot-clé de statut (ex. « Fix READY_FOR_DEV handling ») ne sera plus faussement appariée — c'est la correction voulue.
> - **Correction des mocks de tests** : `patch("src.pipelines.sync.sync_sprint_backlog")` est **inerte** (le nom est lié dans `_sync_run.py` via import direct, pas résolu dynamiquement). Les tests passent par accident (no-op sur `tmp_path` vide). Correction requise pour rendre les tests honnêtes — impact : les tests devront réellement intercepter, comportement attendu identique.
> - **Portée ≠ MLOOP-205-BE** : ce plan ne touche **aucun** dépôt Metro, **aucun** index ADR, **aucun** récit — MLOOP-205-BE (normalisation colonnes Metro + réparation index 0342) reste un chantier documentaire séparé, déjà READY_FOR_DEV. La renumérotation 0342 reste dette hors périmètre (explicite dans MLOOP-205-BE).
> - **Exécution différée** : ce plan est soumis pour approbation ; l'exécution code sera déléguée (`worker-spawn`, task-type `build`) car ≥ 3 fichiers touchés — jamais sur le thread principal.

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> **Questions de clarification ou arbitrages restants :**
> - **OQ-01** : Faut-il conserver `FAIT` comme jeton de statut canonique (français) ou le traduire en `DONE` à l'écriture ? → *Recommandation : conserver tel quel — le backlog utilise `FAIT` ; le fix doit refléter la réalité du SSOT, pas la normaliser unilatéralement.*
> - **OQ-02** : La colonne exacte du « statut » dans le backlog mLoop est-elle bien l'index déterminé par l'en-tête (`Statut`) ou y a-t-il une colonne intermédiaire (ex. Grill-me) ? → *Recommandation : parser l'en-tête pour localiser dynamiquement la colonne `Statut`, robuste à tout réordonnancement futur.*

---

## 3. Modifications Proposées (Proposed Changes)

Inventaire Zéro Blindspot ADR-0376 — 7 couches balayées (cold scan terminé, hashes baseline capturés).

### Couche 6 — Core Python & CLI (`src/`)
*Correction du parsing SSOT et purge du monolithe mort.*

- #### `[MODIFY]` [`src/pipelines/sync/_sync_docs.py`](file:///c:/Memory%20Loop/src/pipelines/sync/_sync_docs.py)
  - **Intention** : Rendre `sync_sprint_backlog` colonne-aware et compléter le vocabulaire de statuts.
  - **Impact** : `sync_sprint_backlog` (L217-298) uniquement ; `load_sync_cache`/`save_sync_cache`/`sync_project_directives`/`sync_open_questions` intacts.
  - **Changements détaillés** :
    1. **Parser l'en-tête** de chaque tableau pour localiser l'index de la colonne `Statut` (détection dynamique, robuste au réordonnancement) ; extraire le statut **uniquement** depuis cette cellule, plus `re.search` sur toute la ligne.
    2. **Étendre le vocabulaire** reconnu : `DRAFT`, `DONE_TESTED`, `FAIT`, `PENDING`, `TOMBSTONE` (présents dans le backlog mLoop) en plus de la liste actuelle (`ACCEPTED|DONE|IN_QA|IN_DEV|READY_FOR_DEV|READY_FOR_GROOMING|IN_REVIEW|IN_VALIDATE|IN_PLAN|IN_ANALYZE|OPEN|ON_HOLD|CLOSED|BACKLOG`).
    3. **Normalisation** : uppercase + tirets→underscores conservés ; `DONE_TESTED` ne doit pas être tronqué en `DONE` (word-boundary actuel le rate déjà — correctif inclus).
    4. **Préserver** le contrat existant : ID extrait du frontmatter `id:` ou nom de fichier ; fallback `direct_id_status_map` → `status_map[(cat, id)]` → `direct_id_status_map[stem]` ; écriture YAML inconditionnelle si delta ; message console inchangé.
    5. **Respect ADR-0369** : pas d'appel réseau ; `with`/context managers si accès FS supplémentaire ; logging `extra={...}` ; zéro `except: pass`.
    6. **Respect ADR-0202** : module ≤ 300 L / 15 Ko (actuellement 298 L — le fix ne doit pas faire dépasser ; si risque, extraire le parser de tableau dans une helper privée `_parse_backlog_status columnHeader` dans le même fichier ou un sous-module `_sync_backlog_parser.py` `[NEW]` optionnel).

- #### `[DELETE]` [`src/pipelines/sync.py`](file:///c:/Memory%20Loop/src/pipelines/sync.py)
  - **Intention** : Supprimer le monolithe orphelin de 542 lignes entièrement masqué par le package `src/pipelines/sync/` (vérifié : `import src.pipelines.sync` → `sync/__init__.py` ; zéro `ImportFrom` ne peut résoudre `src.pipelines.sync` vers le `.py` — le package gagne toujours dans le système d'import Python).
  - **Impact** : aucun importeur fonctionnel ; seule référence documentaire vivante : `PHASE_FILES_AND_TEST_PLAN.md` L215 (mise à jour Couche 4).
  - **Contenu mort confirmé** : contient un doublon `sync_sprint_backlog` (L179-265) avec le même bug, plus d'autres doublons de fonctions déjà migrées vers `_sync_docs.py`/`_sync_graph.py` par MLOOP-179-BE.

### Couche 7 — Tests & Parité (`tests/`)
*Correction des mocks inertes + couverture du nouveau parsing.*

- #### `[MODIFY]` [`tests/test_sync_resilience.py`](file:///c:/Memory%20Loop/tests/test_sync_resilience.py)
  - **Intention** : Corriger les 5 cibles `patch("src.pipelines.sync.<fn>")` (inertes) vers `patch("src.pipelines.sync._sync_run.<fn>")` — `run_sync` lie les noms par import direct dans `_sync_run.py`, le patch sur le re-export `__init__.py` n'intercepte rien.
  - **Impact** : L29-33, L49-53 (`sync_live_reference_wikis`, `sync_project_directives`, `sync_sprint_backlog`, `sync_open_questions`, `sync_hypergraph`). Les mocks `WikiFixAgent.execute`/`GraphifyAgent.execute` restent valides (patch de méthode sur la classe partagée).
  - **Attendu** : tests verts identiques (la vraie fonction était no-op sur `tmp_path` vide ; après correction le mock intercepte réellement).

- #### `[MODIFY]` [`tests/test_sync_logging.py`](file:///c:/Memory%20Loop/tests/test_sync_logging.py)
  - **Intention** : Même correction des cibles de mock (L49-53, L80-84) vers `_sync_run.<fn>`.
  - **Impact** : assertions `logger.error` inchangées ; docstring L4 mise à jour (référence plus au « src/pipelines/sync.py » monolithique).

- #### `[NEW]` [`tests/test_sync_sprint_backlog.py`](file:///c:/Memory%20Loop/tests/test_sync_sprint_backlog.py)
  - **Intention** : Couvrir spécifiquement le parsing corrigé (aucun test dédié n'existe aujourd'hui — `⚠️ no covering tests found`).
  - **Scénarios de test (Failure Contract ADR-0369)** :
    1. **Nominal** : ligne avec titre contenant « READY_FOR_DEV » + colonne Statut = `DRAFT` → frontmatter reçoit `DRAFT` (pas `READY_FOR_DEV`) — prouve le fix colonne-aware.
    2. **Nominal** : statut `DONE_TESTED` dans la colonne Statut → frontmatter = `DONE_TESTED` (pas tronqué en `DONE`).
    3. **Nominal** : statut `FAIT`, `PENDING`, `TOMBSTONE` reconnus.
    4. **Exception** : colonne `Statut` absente de l'en-tête → retour anticipé / aucun alignement (pas de devinette).
    5. **Exception** : ligne sans ID détectable → ignorée proprement.
    6. **Résilience** : `sprint_backlog.md` absent → retour silencieux inchangé (contrat existant).
    7. **Persistance** : récit déjà aligné → zéro écriture (`updated_files == 0`).
  - **Style** : `@pytest.mark.parametrize` + `pytest.raises` where applicable ; `tmp_path` fixtures ; UTF-8 ; zéro dépendance réseau.

### Couche 4 — Documentation & Protocoles (`standards/`)
*Mise à jour des références au fichier supprimé.*

- #### `[MODIFY]` [`standards/protocols/PHASE_FILES_AND_TEST_PLAN.md`](file:///c:/Memory%20Loop/standards/protocols/PHASE_FILES_AND_TEST_PLAN.md)
  - **Intention** : L215 pointe encore vers `src/pipelines/sync.py` (monolithe supprimé) → repointer vers le package `src/pipelines/sync/` (ou `_sync_run.py` comme entry point `run_sync`).
  - **Impact** : une ligne de tableau ; zéro autre section.

### Couches 1/2/3/5 — Blueprints, ADR, Directives, Skills
*Audit fait, zéro modification requise.*

- **Blueprints** : aucun gabarit ne référence `sync_sprint_backlog` ni `sync.py`.
- **ADR** : ADR-0376 governs this plan ; ADR-0369/0202/0370 constraints respected ; no new ADR needed (bug fix, not architecture decision). Collision 0342 = dette MLOOP-205-BE, hors périmètre.
- **Directives `.agents/`** : aucune directive ne référence le chemin monolithique.
- **Skills** : aucun skill impacté (`sync` est une commande CLI, pas un skill).

### Hors périmètre explicite (Admission of Limits)
- Aucun dépôt client/Metro touché (herméticité).
- Aucun récit `backlog/stories/*` modifié (ce plan n'est pas un récit INVEST ; c'est un chantier framework auto-développé).
- Renumérotation ADR-0342 : **dette reportée** (MLOOP-205-BE out-of-scope, gap 0356/0357/0358/0359/0388/0389 disponible plus tard).
- Exécution MLOOP-205-BE (normalisation Metro) : story séparée, non couverte ici.
- Aucun `git commit`/`push` (feu vert distinct requis, ADR-0386).

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **Le fix colonne-aware apparie un statut différent qu'avant sur une ligne existante** | Moyen | Baseline avant exécution : `Get-FileHash` des frontmatter des 32 récits mLoop ; comparer après ; rollback = restaurer les frontmatter depuis git (`git checkout -- Projects/mLoop/backlog/stories/`). |
| **Vocabulaire étendu écrit `DONE_TESTED` là où `DONE` était attendu** | Moyen | C'est le comportement voulu (SSOT = backlog) ; vérifier que la state machine `StoryStatus` accepte ces valeurs ou les mappe — si rejet, adapter la table de mapping côté écriture uniquement. |
| **Suppression de `sync.py` casse un import non détecté** | Faible | Cold scan AST confirmé zéro `ImportFrom` résolvable vers le `.py` (package gagne) ; vérification post-suppression : `python -c "import src.pipelines.sync"` + suite complète. |
| **Mocks corrigés révèlent un échec latent des tests existants** | Faible | Exécuter les 2 fichiers de tests avant ET après ; si échec post-correction, le test était en train de masquer un bug — investiguer avant de forcer le vert. |
| **Dépassement ADR-0202 (300 L) sur `_sync_docs.py`** | Faible | Ligne actuelle 298 ; le fix ajoute ~20-40 L → extraire `_parse_backlog_status_column()` dans `_sync_docs.py` en helper compact ou créer `_sync_backlog_parser.py` si > 300. |
| **Régression du pipeline `run_sync` complet** | Moyen | `run_sync` appelle `sync_sprint_backlog` en étape [3] ; si la nouvelle version lève, l'étape [4] OQ et suivantes sont impactées — inclure test d'intégration `run_sync` sur `tmp_path` avec backlog valide. |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] **Baseline avant** : `python -m pytest tests/test_sync_resilience.py tests/test_sync_logging.py -q` → 10 passed (état actuel confirmé).
- [ ] **Nouveaux tests** : `python -m pytest tests/test_sync_sprint_backlog.py -q` → tous verts (7+ scénarios).
- [ ] **Tests corrigés** : `python -m pytest tests/test_sync_resilience.py tests/test_sync_logging.py -q` → toujours 10 passed **avec mocks réellement interceptants**.
- [ ] **Suite large** : `python -m pytest tests/ -q -x --tb=short` → zéro échec (ou échec documenté comme préexistant non lié).
- [ ] **Lint/structure** : `python src/swarm.py code-check --all` ou équivalent AST → `_sync_docs.py` conforme ADR-0202 (≤ 300 L) et ADR-0369 (pas de nouveau pattern interdit).
- [ ] **Import smoke** : `python -c "import src.pipelines.sync; assert src.pipelines.sync.run_sync"` → OK après suppression `sync.py`.
- [ ] **`struct-check`** (Gate C12) : `python src/swarm.py struct-check --file Projects/mLoop/backlog/stories/MLOOP-205-BE.md` → conservé 🟢 (non régression du récit voisin).

### B. Vérifications Manuelles & Scénarios Clés
- [ ] **Scénario Nominal (colonne-aware)** : dans un `tmp_path`, créer `sprint_backlog.md` avec ligne titre contenant « READY_FOR_DEV » et colonne Statut = `DRAFT` ; appeler `sync_sprint_backlog` ; vérifier que le frontmatter récit = `DRAFT` (pas `READY_FOR_DEV`).
- [ ] **Scénario Nominal (vocabulaire)** : ligne Statut = `DONE_TESTED` → frontmatter = `DONE_TESTED` complet.
- [ ] **Scénario d'Exception (en-tête sans Statut)** : backlog sans colonne `Statut` → zéro écriture, pas de crash.
- [ ] **Scénario Réel (mLoop)** : après fix, exécuter `python src/swarm.py sync --project mLoop` en mode dry/simulation si disponible, OU appeler `sync_sprint_backlog` sur une copie de `Projects/mLoop` et compter les récits réalignés — s'attendre à ce que les 6 récits `DRAFT` (MLOOP-210→214+) et éventuellement `DONE_TESTED`/`FAIT` soient détectés (alignement frontmatter = backlog).
- [ ] **Contrôle anti-régression Metro** : `sync_sprint_backlog` n'est appelé que pour le projet courant ; vérifier qu'aucun fichier sous `Projects/Metro_*` n'est touché par les tests (tests utilisent `tmp_path`).
- [ ] **Hashes baseline** : comparer les 32 frontmatter mLoop avant/après sur une copie ; toute différence inattendue = rollback immédiat.

### C. Definition of Done (DoD)
- [ ] Tous les fichiers modifiés respectent ADR-0369 (typing, context managers si FS, timeout si réseau — réseau absent ici, observabilité `extra={...}`, zéro `except: pass`).
- [ ] `_sync_docs.py` ≤ 300 lignes (ADR-0202) OU refactor en sous-module autorisé et documenté.
- [ ] Suite de tests complète à zéro échec (ou échec préexistant tracé séparément, jamais masqué).
- [ ] `src/pipelines/sync.py` supprimé ; `import src.pipelines.sync` résout le package ; zéro fichier de test/docs ne référence encore l'ancien chemin (grep de confirmation).
- [ ] `graphify update .` exécuté (AST-only, fraîcheur du graphe).
- [ ] Preuves archivées : EvidencePack `memory/evidence/FRAMEWORK-SYNC-BACKLOG_evidence.json` (concept évidence mis de l'avant : `fact_search_proofs` hashés, `verification_harness` VERIFIED par scénario, `implementation_decisions`, `conflict_matrix`) + `fact_dossier` correspondant.
- [ ] Plan archivé dans `Projects/mLoop/memory/plan/implementation_plan_FRAMEWORK-SYNC-BACKLOG.md` (ADR-0307).
- [ ] **Exécution déléguée** : `worker-spawn` (task-type `build`) pour l'implémentation — jamais sur le thread principal (DELEGATION GATE : ≥ 3 fichiers).
- [ ] **Aucun commit/push** sans feu vert humain distinct (ADR-0386).

---

## 6. Audit 7 Couches ADR-0376 — Récapitulatif

| Couche | Fichiers inspectés | Statut |
| :--- | :--- | :--- |
| 1. Blueprints | `standards/blueprints/*` | ✅ Aucun impact |
| 2. Protocoles | `PHASE_FILES_AND_TEST_PLAN.md` L215 | 🔧 `[MODIFY]` 1 ligne |
| 3. ADR | `standards/adr-system/` (0342 collision = dette MLOOP-205) | ✅ Aucun impact (hors périmètre) |
| 4. Code Core | `src/pipelines/sync.py`, `sync/_sync_docs.py`, `sync/_sync_run.py`, `sync/__init__.py` | 🔧 `[MODIFY]` `_sync_docs.py`, `[DELETE]` `sync.py` |
| 5. Tests | `test_sync_resilience.py`, `test_sync_logging.py`, (nouveau `test_sync_sprint_backlog.py`) | 🔧 `[MODIFY]` ×2, `[NEW]` ×1 |
| 6. Docs/Standards | `PHASE_FILES_AND_TEST_PLAN.md` | 🔧 (même fichier que couche 2) |
| 7. Directives/Skills | `.agents/agents/`, `.agents/skills/` | ✅ Aucun impact |

**Baseline hashes (SHA-256 tronqués) avant exécution :**
- `src/pipelines/sync.py` → `634a937f3edb347c` (542 L) — **à supprimer**
- `src/pipelines/sync/_sync_docs.py` → `492b47760d0d5096` (298 L)
- `src/pipelines/sync/_sync_run.py` → `72405ae80174e4f1` (213 L)
- `src/pipelines/sync/__init__.py` → `8c7e7880c8f46563` (63 L)
- `tests/test_sync_resilience.py` + `tests/test_sync_logging.py` → 10 tests verts
- Vocabulaire backlog constaté (37 lignes) : `DONE_TESTED`×9, `FAIT`×8, `READY_FOR_DEV`×6, `PENDING`×6, `TOMBSTONE`×5, `DONE`×3

**FRAMEWORK_STATE (ADR-0352) checklist :**
- [x] Status source vérifié : N/A (pas de récit ; chantier framework auto-développé, statut = ce plan `DRAFT`→`APPROVED`)
- [x] Certificat NLI : FRAMEWORK_STATE `last_updated: 2026-09-22` ; aucun commit framework depuis (baseline hashes ci-dessus) — plan valide
- [x] `struct-check` inclus dans §5A
- [x] `verification_harness` non vide : 7+ scénarios pytest listés §5A/§5B
- [x] Transition d'état : N/A story — plan `DRAFT` → `APPROVED` (après humain) → `EXECUTING` (après worker-spawn) → `COMPLETED` (après DoD)
