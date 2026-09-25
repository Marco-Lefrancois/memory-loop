---
created: 2026-09-24T19:33:49.834Z
source: plannotator
tags: [plannotator, memory-loop, correctifs, done_tested, absent]
---

[[Plannotator Plans]]

# Plan — Correctifs C1 (`DONE_TESTED` absent de l'enum) + C2 (faux succès `mark_story_grilled`)

## 1. Constats sourcés (Fact-Search)

**C1 — Dérive doc/code sur le statut `DONE_TESTED`**
- `standards/protocols/STORY_LIFECYCLE_PROTOCOL.md` L16/L35/L63-70 : chaîne canonique `DRAFT → … → IN_DEV → DONE_TESTED → SHIPPED`, statut auto-positionnable par l'IA quand tests + revue passent ; `CHANGELOG.md` L40 (« 8 statuts unifiés ») ; `standards/adr-system/0381-…` (verrou Gate 3 *sur* `DONE_TESTED`) ; `_sync_backlog_parser.py` L22 et `wikifix_core.py` L202 connaissent déjà le mot ; `tests/test_sync_sprint_backlog.py` L88-105 teste le round-trip `DONE_TESTED`.
- **Mais** `StoryStatus` (`src/state/_state_core.py` L82-117) ne contient pas `DONE_TESTED` → `from_raw("DONE_TESTED")` → **`OPEN`**. Conséquences réelles : `SprintBacklogItem.status` corrompu en `OPEN`, `grilled`/`jira_sync_eligible` = `False` (LE récit ne serait jamais poussé vers Jira), et toute validation FSM sur un récit `DONE_TESTED` est biaisée.
- Le backlog `sprint_backlog.md` et les frontmatters mLoop utilisent déjà `DONE_TESTED` (MLOOP-210-BE depuis ce tour) → le bug est **actif**.

**C2 — `mark_story_grilled` ne met jamais le backlog à jour (faux succès)**
- `src/pipelines/grill_engine.py` L287 : regex `([A-Z_]+)` attend une cellule de statut ** nue** (`READY_FOR_GROOMING` sans décor), or le format réel des colonnes Statut est `` ✅ `DONE` `` / `` 🟣 `DONE_TESTED` `` (emoji + backticks) → **0 substitution**, alors que le frontmatter, lui, est bien passé à `READY_FOR_GROOMING` (L274-281) et la fonction retourne `True`.
- `sync` (backlog = SSOT) réaligne alors le récit **en arrière** sur l'ancien statut du backlog → « succès » puis annulation silencieuse. C'est ce mécanisme constaté sur les micro-grills EPIC-21.
- DANGER additionnel identifié : le même regex peut matcher n'importe quelle cellule `[A-Z_]+` après l'ID (ex. une cellule Taille `S`/`M`/`L`) → **corruption possible de colonnes non-cibles**.

## 2. Corrections (3 fichiers code)

**C1a. `src/state/_state_core.py`** `[MODIFY]`
- Ajouter `DONE_TESTED = "DONE_TESTED"` dans `StoryStatus` (section CLIENT, après `IN_DEV`).
- Mettre à jour la docstring de l'enum avec la chaîne unifiée du protocole.
- Ajouter `"DONE_TESTED"` au frozenset `_GRILLED_STATUSES` (L150-160) → `grilled` et `jira_sync_eligible` = `True` (cohérent avec la note de migration L111 du protocole).

**C1b. `src/pipelines/state_machine.py`** `[MODIFY]` — uniquement `ALLOWED_TRANSITIONS` :
- `IN_DEV` : + `StoryStatus.DONE_TESTED` (protocole §E).
- Nouvelle clé `StoryStatus.DONE_TESTED` : `[SHIPPED, IN_REVIEW, IN_DEV, ON_HOLD, ERROR]` (§F `→ SHIPPED`, §3.2 rétrogradation `→ IN_REVIEW`, re-progression `→ IN_DEV`).
- Aucun accès direct `IN_REVIEW → DONE_TESTED` (le protocole impose le passage par `IN_DEV`).
- Zéro changement sur les autres listes.

**C2. `src/pipelines/grill_engine.py`** `[MODIFY]` — **uniquement la méthode `mark_story_grilled` (L199-~300)** :
- ⚠️ Le fichier contient des changements **non committés d'une autre session** (bloc ADR-0389 ajouté en fin de fichier, L292+) → interdiction formelle d'y toucher, pas de `git checkout/restore/stash`.
- Remplacer le regex naïf (L287) par une réécriture **colonne-aware** :
  1. localiser l'index de la colonne `Statut` via l'en-tête du tableau (réutiliser `_find_statut_col_index` + `STATUS_VOCAB_RE` importés depuis `src/pipelines/sync/_sync_backlog_parser.py`, SSOT du parser) ;
  2. identifier la ligne cible par la cellule d'identité (`**<story_id>**`), remplacer le jeton de statut **dans la seule cellule Statut** (préserver emoji/backticks) ;
  3. si ligne ou colonne introuvable : `logger.warning` contextuel (`extra={...}`, ADR-0369) + aucun remplacement hasardeux.
- Le retour reflète la cohérence story↔backlog : plus de `True` quand le backlog n'a pas bougé.

## 3. Tests (TDD : Red → Green)

- `tests/test_story_status.py` `[MODIFY]` :
  - `from_raw("DONE_TESTED" / "done_tested" / "done tested" / "DONE-TESTED")` → `DONE_TESTED` (échoue aujourd'hui : attendu `OPEN`).
  - Transitions : `IN_DEV→DONE_TESTED` ✓, `DONE_TESTED→SHIPPED` ✓, `DONE_TESTED→IN_REVIEW` ✓ ; `DRAFT→DONE_TESTED` lève `StateTransitionError`.
  - `grilled` et `jira_sync_eligible` = `True` pour `DONE_TESTED`.
  - `test_all_statuses_parseable` (L73) couvre naturellement le nouveau membre.
- `tests/test_grill_engine.py` `[MODIFY]` :
  - Nouveau test au **format backlog réel** (colonne `Statut` = `` 🟢 `READY_FOR_DEV` ``, avec colonnes Taille `S`/`M`/`L`) : `mark_story_grilled` → cellule Statut = `READY_FOR_GROOMING`, **taille/titre intacts**, retour `True` (échoue aujourd'hui).
  - Nouveau test ligne absente → pas de corruption, retour/avertissement explicite.
  - Les tests existants (`US-01`, `US-05-FOOD`) doivent rester verts.

## 4. Vérifications finales (Gate de sortie)

1. `python -m pytest tests/test_story_status.py tests/test_grill_engine.py tests/test_sync_sprint_backlog.py tests/test_in_review_lifecycle.py tests/test_focus_persistence.py tests/test_jira_sync_safe.py -q` → 0 échec.
2. Suite complète : `python -m pytest tests/ -q --ignore=tests/test_click_cli_engine.py` → vert (l'erreur `click` est celle d'une autre session, **non touchée**).
3. `python src/swarm.py code-check` sur les 3 fichiers modifiés → 0 violation.
4. AUCUN `git add/commit/restore/stash` ; arbre partagé respecté.

## 5. Non-périmètre

- `STORY_LIFECYCLE_PROTOCOL.md` (déjà canonique), backlog/récits (déjà alignés), migration globale `DONE → DONE_TESTED` (note de migration du protocole, hors-UCE).
- Le bloc ADR-0389 de l'autre session dans `grill_engine.py` ; `tests/test_click_cli_engine.py` ; les OQ du récit 210.

## 6. Exécution (DELEGATION GATE)

Volume ≥ 3 fichiers + durée > 5 min → **délégation obligatoire** : spawn d'un worker Herdr isolé (`--task-type build`) avec brief strict (périmètre ci-dessus, interdits §2/§4), puis `worker-harvest` → vérifications Gate → `worker-close` dans le même tour.

## 7. Impact attendu

- Un récit `DONE_TESTED` n'est plus jamais relu comme `OPEN` (FSM, Jira sync, grilled).
- `grill` devient fiable de bout en bout (frontmatter **et** backlog cohérents) → plus de réversion silencieuse par `sync`.
- Risque résiduel maîtrisé : changement de comportement de `from_raw` (c'est la correction voulue) — couvert par les tests d'impact listés (focus, serializer, jira, sync).