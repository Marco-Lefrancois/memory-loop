# 🎯 Brief de Conversion Palier 2 — `MLOOP-270-BE` (EPIC-27)

**Émetteur** : Orchestrateur session Grill — 2026-09-24
**Feu vert humain** : OBTENU (« je te donne le feu vert », mandat session « toujours l'Option A recommandée ») → statut cible **`READY_FOR_DEV`** direct.
**Modèle worker** : `opencode/mimo-v2.6-flash-free` (task-type `build`)

---

## 1. Objectif (dans cet ordre)

1. **Rubber Duck** : `python src/swarm.py rubber-duck --project mloop --file Projects/mLoop/backlog/stories/MLOOP-270-BE.md` → doit être **APPROUVÉ, 0 problème bloquant**. Si rejet → corriger le récit puis relancer jusqu'à vert.
2. **Conversion** du récit `Projects/mLoop/backlog/stories/MLOOP-270-BE.md` du **Palier 1 → Palier 2** selon `standards/blueprints/story_template.md` (GABARIT UNIQUE — ADR-0375).
3. **Mise à jour `Projects/mLoop/backlog/sprint_backlog.md`** : ligne `MLOOP-270-BE` → Grill-me `✅ DONE`, Statut `🟢 READY_FOR_DEV`, Responsable `👤 Humain (feu vert 2026-09-24, Grill EPIC-21/27)`.
4. **Sync** : `python src/swarm.py sync --project mloop`.

## 2. Frontmatter Palier 2 (cible)

`status: READY_FOR_DEV` · `grill_me: DONE` · `invest_score: 6/6` · `id: MLOOP-270-BE` · `jira_key: MLOOP-270-BE` · `epic_key: EPIC-27-LIFECYCLE-STATE-LOCK` · `type: FEATURE` · `layer: PLATFORM` · titre métier pur (H1 sans clé Jira) · autres champs du gabarit repris tels quels.

## 3. Contenu obligatoire (4 Piliers Gherkin — le récit se termine STRICTEMENT après `## Scénarios de test`)

Le récit est un verrou **100% backend/gouvernance** (zéro UI). Ancrages **véridiques uniquement** (aucune API fictive) :

**Décisions du grill (toutes Option A, scellées ADR-011)** :
- **Q1** : Hybride deux anneaux — `set_story_status()` unique (appelle `validate_transition()` systématique, mutex `file_lock.py`/`InterProcessFileLock` avec `timeout` ADR-0369) + scan rétrogradant ; `claim_lease` (gates.py) **hors périmètre**.
- **Q2** : `story-approve --approver "<Nom>"` réutilise `validate_gate4_approval()` (rejet `BOT_DISALLOWED_NAMES`, `HUMAN_KEYWORDS`), seul écrivain de `validated_by`/`validated_at` ; entrée d'approbation infalsifiable (pattern `_lc_models.py:162`). Limite admise : forgeabilité locale.
- **Q3** : journal `Projects/<p>/memory/story_transitions.jsonl` dédié, append-only « Zéro Rollback » (pattern `skill_impact_tracker.py`), écriture **couplée récit+journal sous `InterProcessFileLock` — échec journal ⇒ transition annulée** ; champs `{ts, story_id, from, to, actor, writer_path: api|raw_edit_detected|backfill, validated_by, validated_at, pid, source_cmd}`.
- **Q4** : feu vert **strictement → `READY_FOR_DEV`** (STORY_LIFECYCLE_PROTOCOL L33 « Humain uniquement », L101 « faute grave ») ; journal de **toute** transition ; double scan (cohérence journal↔frontmatter + `validated_by`) ; **zéro empilement** sur les `gated_statuses` C9.
- **Q5** : double véhicule — **`struct-check` C13** par-récit (BLOCKING sur faute grave, WARNING/STRICT legacy) + **contrôle vibe-check gouvernance** projet-wide (≥ check 14, `{check, status}` PASS/FAIL, pattern `check_13`) ; sanction = **rétrogradation auto → `READY_FOR_GROOMING`** (précédent `state_machine.py:496`), **jamais de suppression** (Zéro Rollback).
- **Q6** : `story-backfill --approver` sous feu vert (`writer_path: backfill`, **zéro fabrication** sans approver nommé) ; exemptions `DONE`/`DONE_TESTED` (26 récits, pattern C9 L320-325) ; graduation WARNING legacy → BLOCKING post-backfill. Chiffres : 58 récits (DRAFT 21, DONE 16, DONE_TESTED 10, RFD 10, IN_DEV 1), 0 `validated_by`.

**Ancrages code à citer en toute vérité** : `src/pipelines/state_machine.py` (ALLOWED_TRANSITIONS L46-164, validate_transition L190, validate_single_in_analyze L205, validate_content_integrity L467, auto-rétrogradation L496, gated_statuses C9 L340) · `src/utils/file_lock.py` (InterProcessFileLock L97) · `src/core/gates.py` claim_lease L561 (hors périmètre) · `src/core/gate4_validator.py` L72-78 · `src/utils/event_logger.py` L94-99 (best-effort, rejeté) · `src/pipelines/vibe_check/_vc_governance.py` checks 10-13 · `src/pipelines/struct_checker.py` C1-C12.

**Faits d'incident à conserver** : réécriture 13:49:04 → restauration 13:50:18 → re-jeu 13:54:28 ; « struct-check ×4 » sans artefact ; arbitrage A → rétrogradation → promotions une à une.

**Preuves** : `memory/evidence/MLOOP-270-BE_fact_dossier.md` (VALIDATED, 15 faits) — lien dans `## Références` + EvidencePack `memory/evidence/MLOOP-270-BE_evidence.json`.

## 4. Interdits

- Jamais de `C:\...` ni clé temporaire dans le corps (liens `file:///` uniquement, réf inter-récits par clé Jira).
- Aucun JSON/route API inventé (tout est CLI locale réelle).
- Le récit finit à `## Scénarios de test` (zéro métadonnée IA dans le `.md`).
- **Ne pas** stamp manuellement `validated_by` (la commande `story-approve` n'existe pas encore — c'est le périmètre de build de ce récit) ; le feu vert est consigné dans `sprint_backlog` (colonne Responsable).
- Zéro `&&` sous PowerShell ; `sync` est obligatoire en dernier.

## 5. Rapport attendu

Statut final du récit, verdict Rubber Duck (confiance/0 bloquant), lignes `sprint_backlog` modifiées, résultat `sync`, éventuels imprévus.
