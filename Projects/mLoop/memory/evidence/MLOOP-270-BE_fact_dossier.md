# 📁 Dossier de Preuves Documentaires — `MLOOP-270-BE`

- **Récit** : `MLOOP-270-BE` — Verrou anti-promotion `READY_FOR_DEV` (EPIC-27-LIFECYCLE-STATE-LOCK)
- **Établi le** : 2026-09-24 — Grill-Me Micro 1:1 (session Grill EPIC-21, suite)
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill 6/6 (Q1-Q6, Option A sous mandat session + feu vert explicite) → `ADR-011_verrou_anti-promotion_ready_for_dev__epic-27.md`

---

## 1. Sources & Notes d'Atelier

- Brief d'incident : `file:///C:/Memory%20Loop/Projects/mLoop/memory/EPIC-27_incident_state_lock_brief.md`
- Épopée : `file:///C:/Memory%20Loop/Projects/mLoop/backlog/epics/epic_lifecycle_state_lock.md`
- Protocole SSOT : `standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`
- ADR macro associés : ADR-0375 (cycle 5 phases), ADR-0369 (deadlines/FAILURE CONTRACT), ADR-0370 (anti-drift CLI), ADR-0352 (FRAMEWORK_STATE/struct-check), ADR-0320/0326 (dossier de preuves), ADR-0385 (échelle de preuve).
- **Maquettes** : aucune (réinit purement backend/gouvernance, zéro surface UI) → Admission of Limits §6.

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Q1 draft « quel verrou ? » vs code existant (`file_lock.py`, `claim_lease`) | **Code > draft** : faux dilemme écarté ; verrou réutilisé en atomicité d'écriture uniquement (Q1-A) |
| Prévention vs détection | **Hybride deux anneaux** : impossible de verrouiller un `.md` éditable en brut ; API unique + scan (Q1-A) |
| `events.jsonl` existant vs journal dédié | **Dédié** : `EventLogger` best-effort (échec avalé) incompatible avec une preuve (Q3-A) |
| Élargir le feu vert vs protocole §4 | **Protocole > confort** : L33/L101 ne qualifient que → `READY_FOR_DEV` (Q4-A) |
| BLOCKING immédiat vs 10 faux positifs jour 1 | **Graduation C9** : WARNING legacy → BLOCKING post-backfill (Q6-A) |

## 3. Extraits Verbatim Sourcés

**Extrait 1 — STORY_LIFECYCLE_PROTOCOL.md (Ligne 33) :**
« `READY_FOR_DEV` | **Humain uniquement** | `story_template.md` | **Interdiction formelle à l'IA.** État certifiant que le récit est arbitré, complet, et prêt pour l'implémentation physique. »
➔ **Fait établi (F-01)** : la frontière rédaction/engagement est UNE transition, juridiquement qualifiée « interdiction formelle à l'IA ».

**Extrait 2 — STORY_LIFECYCLE_PROTOCOL.md (Ligne 101) :**
« Toute tentative par l'IA de basculer un récit en `READY_FOR_DEV` sans validation humaine explicite est une **faute grave** et constitue une violation du contrat de délégation. »
➔ **Fait établi (F-02)** : sanction doctrinale définie ; aucun garde-fou machine ne l'appliquait avant cette épopée (faille de l'incident).

**Extrait 3 — `src/pipelines/state_machine.py` (Lignes 467-499, `validate_content_integrity`) :**
« `if not stored_hash or status not in ("READY_FOR_GROOMING", "READY_FOR_DEV"): return True` … `current_hash = self.compute_content_hash(parts[2])` » et (L496) « ➡ Le récit est automatiquement rétrogradé en IN_ANALYZE pour forcer un nouvel audit Sentinel. »
➔ **Fait établi (F-03)** : (a) le hash ne couvre que le **corps** (`parts[2]`) — une mutation de `status:` en frontmatter passe inaperçu ; (b) la **rétrogradation automatique existe déjà en doctrine codée** (précédent de sanction Q5-A).

**Extrait 4 — `src/pipelines/state_machine.py` (Lignes 46-164, `ALLOWED_TRANSITIONS`) + (L190-203, `validate_transition`) :**
`validate_transition` lève `StateTransitionError` hors table ; **appels recensés : `focus.py:124/132` (→ IN_ANALYZE) et `grill_engine.py:272` (→ READY_FOR_GROOMING) uniquement** (grep, 4 correspondances).
➔ **Fait établi (F-04)** : **aucun appel ne valide → `READY_FOR_DEV`** ; il n'existe aucune fonction `set_story_status()` — tous les écrivains modifient le YAML en brut. L'incident n'a contourné aucun verrou : il n'y en avait pas.

**Extrait 5 — `src/utils/event_logger.py` (Lignes 94-99) :**
« `with self._lock:` … `except OSError as e: logger.debug("Échec écriture log JSONL …")` »
➔ **Fait établi (F-05)** : `events.jsonl` est **best-effort par conception** (télémétrie) — inutilisable comme preuve de feu vert (Q3).

**Extrait 6 — `src/core/gate4_validator.py` (Lignes 72-78) :**
« `is_bot_only = approver_clean in BOT_DISALLOWED_NAMES` … `has_human = any(h in approver_clean for h in HUMAN_KEYWORDS)` … « humaine formelle (ex: approver='Marco' ou 'Lead Architect') » »
➔ **Fait établi (F-06)** : le **contrôle d'autorité humaine existe déjà** (rejet noms bots + mot-clé humain) — réutilisé tel quel par `story-approve` (Q2-A).

**Extrait 7 — `src/utils/file_lock.py` (Lignes 97-156) :**
« Verrou de fichier inter-processus et inter-thread réentrant … Windows : `msvcrt.locking` / Unix : `fcntl.flock` … timeout » + context manager `__enter__`/`__exit__`.
➔ **Fait établi (F-07)** : primitive de verrouillage portable **opérationnelle** (mutex d'écriture récit+journal, Q1/Q3-A ; `timeout` conforme ADR-0369).

**Extrait 8 — `src/core/gates.py` (Lignes 561-601, `claim_lease`) :**
« Tente de verrouiller les chemins exclusifs OWNS pour un worker/leaf … `*.lock.json` … `owns_globs` … Collision OWNS »
➔ **Fait établi (F-08)** : mécanisme de bails **existant mais hors périmètre** (bails fichiers, pas statuts) — décision Q1-A d'exclusion explicite.

**Extrait 9 — `src/pipelines/state_machine.py` (Lignes 205-245, `validate_single_in_analyze`) :**
« parcourt `self.stories_path.glob("**/*.md")` … `raise StateTransitionError` si > 1 `IN_ANALYZE` »
➔ **Fait établi (F-09)** : le pattern **« invariant vérifié par scan de TOUS les récits »** est déjà codé — base de l'anneau 2 (scan cohérence) sans invention.

**Extrait 10 — `src/pipelines/state_machine.py` (Lignes 340-345, `gated_statuses`) :**
« `gated_statuses = ("READY_FOR_DEV", "READY_FOR_GROOMING", "IN_DEV", "IN_QA")` » (Gate C9, `strict=False` défaut WARNING / `strict=True` BLOCKING)
➔ **Fait établi (F-10)** : la **graduation stricte/transition** est le pattern établi (Q5/Q6-A) et l'ensemble C9 ne sera **pas** doublonné d'un second feu vert (Q4-A).

**Extrait 11 — `src/pipelines/vibe_check/_vc_governance.py` (Lignes 5-10) :**
« Checks inclus : check_10_visual_contract … check_11_rule_engine … check_12_sow_granularity … check_13_phase_gate (ADR-0375 / ADR-0339) » — signature `check_NN_*(project_dir, project_name, lifecycle_mode, stage_label) -> {"check", "status": PASS|FAIL}`.
➔ **Fait établi (F-11)** : point de greffe du nouveau contrôle projet-wide (Q5-A), numérotation ≥ 14 à confirmer au registre à l'implémentation.

**Extrait 12 — `src/pipelines/struct_checker.py` (Lignes 45-68, 119-154) :**
« `severity: str # "BLOCKING" | "WARNING"` … `check_file(target_file, strict=False)` … `passed = all(v.severity != "BLOCKING" for v in violations)` ; checks C1→C12 (C6 frontmatter, C9 dossier, C12 Domain Sanity ADR-0352).
➔ **Fait établi (F-12)** : véhicule par-récit du nouveau check **C13** (Q5-A), report `StructCheckReport` existant.

**Extrait 13 — Brief incident (Ligne 41, L47) :**
« Résolution : arbitrage humain Option A → rétrogradation puis promotion **un par un** avec feu vert traçable » ; « ❓ **Q2 — Autorité de la transition** … jeton/signature de session ? ligne `validated_by` + timestamp ? … sans casser les workflows humains directs »
➔ **Fait établi (F-13)** : les questions 1-6 du brief sont **toutes tranchées** par Q1-Q6 du présent grill.

**Extrait 14 — Chronologie incident (note sprint_backlog, L168) :**
réécriture non autorisée à **13:49:04** → restauration **13:50:18** → re-jeu **13:54:28** ; mention « struct-check ×4 » sans aucun artefact `struct_check_*` sur disque.
➔ **Fait établi (F-14)** : écrivain brut extérieur, double re-jeu, allégation de contrôle **invérifiable** — le journal de transitions (Q3) aurait matérialisé l'acte.

**Extrait 15 — Inventaire récits projet (scan `backlog/stories/`, 2026-09-24) :**
`DRAFT 21 · DONE 16 · DONE_TESTED 10 · READY_FOR_DEV 10 · IN_DEV 1` (58 total) ; **0 récit avec `validated_by`**.
➔ **Fait établi (F-15)** : périmètre du backfill = 10 `READY_FOR_DEV` + seeds non terminés (1 `IN_DEV`) ; `DONE`/`DONE_TESTED` (26) exemptés (Q6-A, pattern C9 L320-325).

## 4. Structure de Données Cible (DBML)

```dbml
Table story_transitions_journal {   // Projects/<p>/memory/story_transitions.jsonl (append-only, Zero Rollback)
  ts          varchar   // ISO8601 UTC
  story_id    varchar   // ex: MLOOP-270-BE
  from_status varchar   // état antérieur (null = seed backfill)
  to_status   varchar   // état cible
  actor       varchar   // id session/agent (indice, pas identification — Admission of Limits)
  writer_path enum [api, raw_edit_detected, backfill]   // origine de l'écriture
  validated_by varchar  // null sauf transitions -> READY_FOR_DEV
  validated_at varchar  // ISO8601
  pid         int
  source_cmd  varchar   // commande émettrice
}

Table story_frontmatter {           // backlog/stories/<ID>.md (éditable en brut)
  status        varchar  // machine-à-états (ALLOWED_TRANSITIONS)
  validated_by  varchar  // ÉCRIT UNIQUEMENT par story-approve (Q2)
  validated_at  varchar
  content_hash  varchar  // corps seul (parts[2]) — faille F-03 connue
}
```
Relation : `story_frontmatter.status == story_transitions_journal.to_status (dernière ligne)` = invariant du scan (cohérence).

## 5. Contrats Déclaratifs Cibles

- **`story-approve`** (Q2) : `python src/swarm.py story-approve --project <p> --story <ID> --approver "<Nom>"` → `validate_gate4_approval()` (F-06) → écrit atomique (`set_story_status`) de `validated_by`/`validated_at` + entrée journal + entrée d'approbation infalsifiable (pattern `_lc_models.py:162`).
- **`story-backfill`** (Q6) : `python src/swarm.py story-backfill --project <p> --approver "<Nom>"` → seed journal `writer_path: backfill` + stamp des récits non terminés ; sans `--approver` nommé → rien écrit.
- **`set_story_status()`** (Q1) : unique écrivain agents ; `validate_transition()` systématique ; **refus → `READY_FOR_DEV` sans `validated_by`** ; journal couplé sous `InterProcessFileLock` ; **échec journal ⇒ annulation transition** (FAILURE CONTRACT ADR-0369 §5).
- **`struct-check C13`** (Q5) : par-récit — RFD sans preuve = `BLOCKING` ; écart journal = `WARNING` legacy / `BLOCKING` post-backfill (`strict`).
- **`vibe-check` contrôle ≥14** (Q5) : projet-wide, `{check, status: FAIL}` garde pré-vol (pattern `check_13`).
- **Anti-drift** (ADR-0370) : toute nouvelle commande ⇒ `python src/swarm.py guide --sync` immédiat.

## 6. Frontière Active & Admission of Limits

- **Forgeabilité locale** : tout process accédant au disque peut écrire `validated_by: <nom>` — la garantie est **traçabilité + détection + rétrogradation**, pas l'impossibilité cryptographique (jeton HMAC rejeté, Q2-B). Limite admise.
- **Acte neutralisé, acteur non identifiable** : le journal livre `pid`/`actor` comme indices, pas une identification fiable (Q5, Admission of Limits).
- **Coopération requise** : l'anneau 2 ne protège que les écrivains qui passent par l'API ou qui sont scannés ; un écrivain brut entre deux scans reste possible (fenêtre réduite aux points de gate + boot).
- **Aucune surface UI** dans ce récit ; aucun test runtime Niveau 3 requis ici (le harness de fixtures iframe de MLOOP-215-FULL reste hors périmètre).
- **Hors périmètre** : `claim_lease`/OWNS (F-08), `events.jsonl` (F-05), `journal[]` graphe, watch temps réel (Q5-C rejeté), statuts terminés (F-15).
