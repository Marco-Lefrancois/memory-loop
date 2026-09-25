---
id: PLAN-MLOOP-270-BE
story_id: MLOOP-270-BE
status: COMPLETED # DRAFT | APPROVED | EXECUTING | COMPLETED
harness: opencode
created_at: 2026-09-25
approved_at: 2026-09-25
approved_by: Marco (session opencode)
---

# Verrou Anti-Promotion & Journal des Transitions de Statut (EPIC-27)

> **Objectif** : Répondre à l'incident du 24/09/2026 (promotion sauvage de 4 récits en `READY_FOR_DEV` sans feu vert humain) en instituant un **écrivain unique verrouillé** des transitions de statut, un **journal append-only** `Projects/<p>/memory/story_transitions.jsonl` couplé atomiquement au récit, un **contrôle rétrogradant** (jamais de suppression), et deux véhicules de signalement (check `C13` dans `struct-check` + contrôle de gouvernance **n° 14** dans `vibe-check`). Périmètre pur framework mLoop (`src/`, `tests/`) — herméticité respectée.

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes nécessitant une confirmation explicite :**
>
> 1. **CA-6 = cet approbation** : la validation de ce plan *est* le feu vert humain requis pour toucher le cœur mLoop (ADR-0376). Aucune écriture ne commencera avant votre approbation explicite.
> 2. **🔴 Blindspot #1 — Ancrages ligne périmés** : les lignes citées dans le récit (`state_machine.py` L320-325, L467-499) ont **décalé après EPIC-31**. Vérification faite par symbole : le « précédent de rétrogradation déjà codé » **n'existe pas** (0 fonction `demote/downgrade/retrograd` dans `src/`) — seul un *warning* C9 existe. **Conséquence** : `scan_and_downgrade()` sera construit à neuf, pas réutilisé. Le pattern d'exemption terminal existe réellement (`scratch_prune.py` L155 : `{DONE_TESTED, SHIPPED, DONE, ACCEPTED, QA_CERTIFIED, READY_TO_SHIP}`) et sera réutilisé.
> 3. **🔴 Blindspot #2 — La table FSM n'a pas d'arête retour** : `READY_FOR_DEV → READY_FOR_GROOMING` est **illégale** aujourd'hui (`ALLOWED_TRANSITIONS`, L115-120). La rétrogradation exigée ne peut donc pas passer par `validate_transition()`. **Arbitrage → OQ-270-1** (recommandé : chemin de sanction explicite hors table, sans élargir les transitions légales — conformément à l'Out-of-Scope « seules les transitions déjà présentes dans la table restent légales »).
> 4. **🔴 Blindspot #3 — Risque opérationnel multi-sessions** : si le contrôle 14 est `BLOCKING` d'emblée, **`vibe-check` échoue pour toutes les sessions** tant que le `story-backfill` (58 récits, 0 approuvés) n'est pas lancé. Le récit impose la graduation (legacy = `WARNING`, après backfill = `BLOCKING`) : cette gradation sera **testée explicitement** pour ne jamais bloquer le travail en cours des autres sessions.
> 5. **Extension de schéma frontmatter** : `story-approve` devient le **seul écrivain** des champs `validated_by` / `validated_at`. Vérifier que le check `C6` (frontmatter obligatoire) tolère ces champs additionnels.
> 6. **Délégation** : build délégué en worker isolé (`worker-spawn --task-type build`, portée d'écriture `src/**, tests/**, memory/**` uniquement — aucun `backlog/**`). **CA-7** : aucune écriture de statut sur les vrais récits du projet pendant le build (tous les tests sur `tmp_path`).

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-270-1 — Cible de la rétrogradation** : l'état « groomé » est hors table depuis `READY_FOR_DEV`. $ightarrow$ *Recommandation : Option B — chemin de sanction interne au module de verrou (`_apply_sanction_downgrade`) qui écrit `READY_FOR_GROOMING` sous journal `origin: sanction`, sans ajouter d'arête à `ALLOWED_TRANSITIONS`.*
> - **OQ-270-2 — Versionnage du journal** : `story_transitions.jsonl` est la preuve infalsifiable. $ightarrow$ *Recommandation : versionner (commité avec le reste du `memory/`, comme les EvidencePacks).* 
> - **OQ-270-3 — Sous-registre CLI** : `story-approve` / `story-backfill` vont dans `_reg_analysis_ext` (déjà domicilié `story-clean`) $ightarrow$ *Recommandation : `_reg_analysis_ext`.*
> - **OQ-270-4 (déjà tranchée au récit)** : exemption contrat réseau — Aucune route HTTP/REST (OQ-270 du récit).

---

## 3. Modifications Proposées (Proposed Changes)

> Audit 7 couches ADR-0376 — chaque fichier est classé `[NEW]` / `[MODIFY]` / `[DELETE]`.

### Couche 6 — Core Python & CLI (`src/`)

- #### `[NEW]` [`src/core/transition_journal.py`](file:///c:/Memory%20Loop/src/core/transition_journal.py)
  - **Intention** : Journal append-only « Zéro Rollback » — seul module autorisé à écrire/ler `Projects/<p>/memory/story_transitions.jsonl`.
  - **API** : `append_entry(project, entry) -> None` (context manager d'écriture, `flush`+`fsync`), `read_entries(project) -> list[dict]`, `last_entry_for(project, story_id) -> dict | None`.
  - **Schéma d'entrée** : `ts` (ISO-8601 UTC), `story_id`, `from_status`, `to_status`, `actor` (auteur), `source_cmd`, `origin` ∈ {`api`, `raw_edit_detected`, `backfill`, `sanction`}, `approval` (pour les entrées d'approbation).
  - **Conformité ADR-0369** : écriture sous `with`, jamais de `except: pass` (log DEBUG `exc_info=True`), échec ⇒ exception propagée (→ annulation de transition).

- #### `[NEW]` [`src/pipelines/story_status_lock.py`](file:///c:/Memory%20Loop/src/pipelines/story_status_lock.py)
  - **Intention** : Écrivain unique des transitions + scan rétrogradant (anneau 2). Le cœur du récit, opérations 1 et 4.
  - **API** :
    - `set_story_status(project, story_id, target, actor, source_cmd, timeout_s=10.0) -> dict` — (a) verrou inter-processus `InterProcessFileLock` couvrant **récit + journal** avec délai explicite, (b) `validate_transition()` systématique, (c) si cible `READY_FOR_DEV` → exiger `validated_by`/`validated_at` présents (sinon `StateTransitionError`), (d) écriture récit → append journal, (e) **échec journal ⇒ rollback récit (tout-ou-rien)**, (f) libération verrou.
    - `apply_human_approval(project, story_id, approver, timeout_s=10.0) -> dict` — **seul écrivain** de `validated_by`/`validated_at` + entrée d'approbation au journal (opération 2, sous le même verrou).
    - `scan_transitions(project) -> dict` — parcours de tous les récits : (a) ligne d'état ↔ dernière entrée du journal, (b) `READY_FOR_DEV` sans approbation ⇒ **rétrogradation** vers `READY_FOR_GROOMING` (OQ-270-1), (c) entrée `sanction` au journal, **jamais de suppression** ; échec de lecture d'un récit ⇒ `logger.debug(exc_info=True)` sans interruption.
    - `_apply_sanction_downgrade(...)` — chemin de sanction hors table FSM (OQ-270-1).
  - **Conformité** : `timeout` explicite partout, context managers, zéro silent-pass, plafond ADR-0202 (≤300 lignes / ≤15 Ko) — au-delà, extraction d'une sous-fonction dédiée.

- #### `[MODIFY]` [`src/core/gate4_validator.py`](file:///c:/Memory%20Loop/src/core/gate4_validator.py)
  - **Intention** : Réutilisation exigée de l'autorité humaine (opération 2) **sans** exiger le rapport QA.
  - **Impact** : extraction du **Contrôle 5** (L71-79) en `validate_human_authority(approver: str) -> str` (lève `ValueError` si nom vide ou machine sans `HUMAN_KEYWORDS`) ; `validate_gate4_approval()` l'appelle (comportement inchangé — **0 régression** du caller unique `approve_gate`).

- #### `[MODIFY]` [`src/pipelines/struct_checker.py`](file:///c:/Memory%20Loop/src/pipelines/struct_checker.py)
  - **Intention** : Nouveau **check C13** (opération 5a).
  - **Impact** : 1 import + 1 appel dans `check_file()` après C9 (L149) ; la logique vit dans le nouveau module ci-dessous (le fichier fait déjà 937 lignes — on n'ajoute pas 80 lignes de plus).
  - **Règles** : `READY_FOR_DEV` sans `validated_by` ⇒ `BLOCKING` (faute grave) ; écart journal ↔ ligne d'état ⇒ `WARNING` (legacy non rétro-équipé) ou `BLOCKING` si `strict=True` **et** backfill effectué.

- #### `[NEW]` [`src/pipelines/_struct_c13.py`](file:///c:/Memory%20Loop/src/pipelines/_struct_c13.py)
  - **Intention** : Corps du check C13 (cohérence journal ↔ statut + présence d'approbation), isolé pour respecter ADR-0202.

- #### `[MODIFY]` [`src/pipelines/vibe_check/_vc_governance.py`](file:///c:/Memory%20Loop/src/pipelines/vibe_check/_vc_governance.py)
  - **Intention** : Contrôle projet-wide **n° 14** (opération 5b) — signature `return {"check": msg, "status": "PASS"|"FAIL"}` identique aux contrôles 10-13.
  - **Impact** : + `check_story_state_lock(results)` : scan global, graduation legacy `WARNING` → `BLOCKING` post-backfill, et **CA-4** (revendication de contrôle sans artefact disque ⇒ « non corroborée »).

- #### `[MODIFY]` [`src/pipelines/vibe_check/__init__.py`](file:///c:/Memory%20Loop/src/pipelines/vibe_check/__init__.py)
  - **Intention** : Import + enregistrement du contrôle 14 (bloc d'imports L34).

- #### `[NEW]` [`src/commands/handlers/story_approve.py`](file:///c:/Memory%20Loop/src/commands/handlers/story_approve.py)
  - **Intention** : Handler `story-approve --project <p> --story <ID> --approver "<Nom>"` → `validate_human_authority()` puis `apply_human_approval()` (opération 2). Rejets : approbateur vide / machine / récit non éligible.

- #### `[NEW]` [`src/commands/handlers/story_backfill.py`](file:///c:/Memory%20Loop/src/commands/handlers/story_backfill.py)
  - **Intention** : Handler `story-backfill --project <p> --approver "<Nom>"` (opération 3). **Sans approbateur ⇒ zéro écriture** ; semence du journal `origin: backfill` sans reconstitution d'auteur inconnu ; stamps d'approbation sur récits **actifs non terminés uniquement** (exemption `scratch_prune.py` L155) ; bascule sévérité `WARNING` → `BLOCKING`.

- #### `[MODIFY]` [`src/commands/_registry/_reg_analysis_ext.py`](file:///c:/Memory%20Loop/src/commands/_registry/_reg_analysis_ext.py)
  - **Intention** : Enregistrement des 2 commandes (OQ-270-3). **Suite obligatoire** : `python src/swarm.py guide --sync` (ADR-0370, parité stricte du guide SSOT — le 15ᵉ contrôle Vibe-Check la vérifie).

### Couche 2 — Protocoles (SSOT)
- #### `[MODIFY]` [`standards/protocols/CLI_PIPELINE_GUIDE.md`](file:///c:/Memory%20Loop/standards/protocols/CLI_PIPELINE_GUIDE.md)
  - **Intention** : **Auto-généré** par `guide --sync` après ajout des 2 commandes (aucune édition manuelle).

### Couche 3 — Architecture (ADR)
- Aucun nouveau fichier : l'ADR de cadrage **ADR-011** existe déjà et scelle Q1-Q6 (Option A). `STORY_LIFECYCLE_PROTOCOL.md` demeure intact (Out-of-Scope).

### Couche 1 — Blueprints & Couche 4 — Directives Agents
- Aucune modification. **Vérification négative** au build : aucun blueprint/directive ne documente une écriture brute de `status:` (si découvert → remontée, pas de codage sauvage).

### Couche 5 — Skills Portables
- **Vérification négative** (`plan`, `triage`, `vibe-check`) : désalignement constaté ⇒ remontée dans le rapport, pas de modification silencieuse hors périmètre.

### Couche 7 — Tests & Parité

- #### `[NEW]` [`tests/test_transition_journal.py`](file:///c:/Memory%20Loop/tests/test_transition_journal.py)
  - Append-only (aucune réécriture/suppression), ordre chronologique, champs complets, échec d'écriture levé (Pilier 4).
- #### `[NEW]` [`tests/test_story_status_lock.py`](file:///c:/Memory%20Loop/tests/test_story_status_lock.py)
  - Nominal (Pilier 1) ; rejets métier (Pilier 2 : sans approbation, nom machine, transition hors table, verrou expiré) ; résilience (Pilier 3 : contention inter-processus avec timeout borné, **échec journal ⇒ rollback** avec monkeypatch du journal) ; façade `set_story_status` réutilisant la FSM existante.
- #### `[NEW]` [`tests/test_incident_replay_2026_09_24.py`](file:///c:/Memory%20Loop/tests/test_incident_replay_2026_09_24.py)
  - **CA-3** : rejeu déterministe — promotion brute → `scan_transitions()` détecte l'écart → rétrogradation journalisée, récit **jamais supprimé** (Failure Contract, `@pytest.mark.parametrize` + `pytest.raises`).
- #### `[NEW]` [`tests/test_story_approve_cli.py`](file:///c:/Memory%20Loop/tests/test_story_approve_cli.py)
  - Opérations 2 & 3 : `story-approve` (nominal / machine refusé / vide refusé, CA-5) ; `story-backfill` (**sans approbateur ⇒ 0 fichier touché**, exemption des terminés).
- #### `[NEW]` [`tests/test_struct_check_c13_and_governance14.py`](file:///c:/Memory%20Loop/tests/test_struct_check_c13_and_governance14.py)
  - C13 (`BLOCKING`/`WARNING`/`strict`), contrôle 14 (PASS/FAIL, graduation legacy, **CA-4** revendication non corroborée).
- **Toutes les fixtures sur `tmp_path`** — jamais les vrais récits `Projects/mLoop` (CA-7).

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| Contrôle 14 `BLOCKING` d'emblée ⇒ `vibe-check` en échec pour **toutes les sessions** (backfill non fait) | **Élevé** | Gradation stricte `WARNING` legacy avant backfill — testée en unitaire ; contrôle basculé `BLOCKING` seulement si journal d'approbation sémantiquement rempli. |
| Ancrages du récit périmés (EPIC-31) + « précédent de sanction » inexistant | Moyen | Levés en §1 (blindspots #1-#2) ; implémentation à neuf testée par le rejeu d'incident. |
| Échec d'écriture journal en cours de transition ⇒ statut fantôme | Élevé | Rollback récit ⇒ transactionnelle testé par monkeypatch (Pilier 3). |
| Contention verrou entre sessions concurrentes (réelle aujourd'hui) | Moyen | `InterProcessFileLock` + `timeout_s` explicite ⇒ `FileLockTimeoutError`, échec net **sans écriture partielle**. |
| `struct_checker.py` déjà 937 lignes (dépasse ADR-0202) | Faible | Logique C13 isolée dans `_struct_c13.py` (pas de grossissement du fichier hôte). |
| Champs `validated_by`/`validated_at` rejetés par le check C6 | Faible | Test C6 sur frontmatter enrichi ; correction tolérante si besoin. |
| Régression de `validate_gate4_approval` (1 caller) | Moyen | Extraction **sans changer le comportement** : tests Gate 4 existants + nouveau test unitaire de `validate_human_authority`. |
| **Rollback général** | — | Tous les fichiers sont `[NEW]`/`[MODIFY]` versionnés : `git revert` du commit unique de build ; aucun `backlog/**` touché pendant le build. |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [x] Suites ciblées :
  ```powershell
  python -m pytest tests/test_transition_journal.py tests/test_story_status_lock.py tests/test_incident_replay_2026_09_24.py -q
  python -m pytest tests/test_story_approve_cli.py tests/test_struct_check_c13_and_governance14.py -q
  ```
- [x] **Parité CLI (ADR-0370, non négociable)** :
  ```powershell
  python src/swarm.py guide --sync
  python -m pytest tests/test_guide_parity.py -q
  ```
- [x] Suite complète (CA-7 — 0 échec, aucun récit du projet modifié) :
  ```powershell
  python -m pytest tests/ -q
  git -C Projects/mLoop status --porcelain -- backlog/   # doit rester vide hors périmètre backfill
  ```
- [x] Contrôles : `python src/swarm.py struct-check --file MLOOP-270-BE` puis `python src/swarm.py vibe-check --project mLoop` (contrôle 14 présent, `PASS`/`WARNING` legacy — **jamais de FAIL bloquant sans backfill**).

### B. Vérifications Manuelles & Scénarios Clés
- [x] **Nominal (CA-2)** : `story-approve` (approbateur humain) → `set_story_status(→ READY_FOR_DEV)` → ligne + entrée journal atomiques, auteur/commande/origine/temps tracés.
- [x] **Exceptions (CA-1, CA-5)** : édition brute de la ligne `status:` ⇒ détectée au scan (le hash de corps seul ne l'attrape pas) ; tentative d'approbation machine (`agent`/`bot`) refusée ; transition hors table refusée **sans entrée journal**.
- [x] **Rejeu d'incident (CA-3)** : restauration puis ré-émision de la promotion ⇒ détection + rétrogradation, récit intact.
- [x] **CA-4** : revendication de contrôle sans artefact disque ⇒ signalée « non corroborée » dans le rapport de gouvernance.
- [ ] **Backfill** : sans `--approver` ⇒ 0 écriture ; avec approbateur ⇒ récits actifs équipés, terminés intacts. *(Exécution réelle sur `mLoop` : **après** validation du build, sous décision humaine explicite.)*

### C. Definition of Done (DoD)
- [x] Standards ADR-0369 respectés (timeout explicite, context managers, zéro `except: pass`, logs structurés) + ADR-0202 (plafonds de taille).
- [x] **CA-6** : ce plan approuvé avant toute écriture (aucun fichier touché avant feu vert).
- [x] **CA-7** : suite complète verte, `backlog/` du projet inchangé, aucun statut promu en sortie de build.
- [x] Parité `CLI_PIPELINE_GUIDE.md` = 100% (`guide --sync` exécuté).
- [x] Plan archivé dans `Projects/mLoop/memory/plan/implementation_plan_MLOOP-270-BE.md` (statut `APPROVED` → `COMPLETED`).
- [x] EvidencePack `MLOOP-270-BE_evidence.json` mis à jour ; frontmatter du récit **laissé en `READY_FOR_DEV`** (la promotion n'est pas l'objet de ce build).