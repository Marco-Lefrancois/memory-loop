---
id: PLAN-MLOOP-180-BE
story_id: MLOOP-180-BE
status: COMPLETED
harness: opencode
created_at: "2026-09-22"
---

# Extension du Schema EvidencePackEngine — 5 Champs de Parité Phase 2

> **Objectif** : Étendre `EvidencePackEngine.extract_evidence` avec les 5 champs Optionals de richesse épistémique (`verbatim_extracts`, `implementation_decisions`, `declarative_contracts`, `epistemic_audit` riche, `conflict_matrix`) + multiplicateur de confiance (décision 5), sans casser les 71 packs legacy ni les 9 callers existants.

---

## 0. Pré-requis FRAMEWORK_STATE (ADR-0352) — ✅ CHECKLIST

- [x] **Status source vérifié** : frontmatter lu — `status: READY_FOR_DEV`, `grill_me: DONE`, hash `a7d2aff6082bfc4e`.
- [x] **Certificat NLI daté** : aucun certificat NLI attaché à `evidence_pack.py` ; dernier changement framework (FRAMEWORK_STATE 2026-09-21) concerne `src/utils/` + handlers CLI — **non obsolète** pour ce composant.
- [x] **`struct-check` inclus dans §5A** : commande exécutée en recette (Gate C12).
- [x] **`verification_harness` non vide** : récit porte 4 piliers Gherkin (regex `Scénario:` OK).
- [x] **Transition d'état valide** : `READY_FOR_DEV` → exécution BUILD autorisée.

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes (6/6 actées Grill 1:1, 22/09) — déjà approuvées PO :**
> - **Déc.1** : citations granularité **hybride D** — 1/fichier modifié + 1/décision.
> - **Déc.3** : `implementation_decisions` dans le pack JSON ; `verbatim_extracts` dual-écriture (pack + fact_dossier).
> - **Déc.4** : Gate 5 **blocking new only** — legacy exempté (warning).
> - **Déc.5** : `confidence_score × (0.7 + 0.3 × min(1, richesse/max))` + `richness_penalty` dans `epistemic_audit`.
> - **Déc.6** : EPIC 1-9 strictement exclus du périmètre de rétroactivité.
> - **Rétrocompatibilité** : les 5 champs sont `Optional` — absence = liste vide / None, **jamais** d' KeyError sur les 71 packs existants.

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-001** : route HTTP inconnue éventuelle $\rightarrow$ *Recommandation : `[API de soumission à définir]` + consigne dans `docs/04-transverse/00-questions-ouvertes.md` (Zéro Fausse Route).* — **déjà couverte par l'exemption ADR-0319 du récit** (composant 100% interne).
> - **OQ-002** : borne max `implementation_decisions` (surcharge pack) $\rightarrow$ *Recommandation : borne douce 50, troncature documentée dans `epistemic_audit` si dépassée (décision reportée à MLOOP-181-BE si nécessaire).*

---

## 3. Modifications Proposées (Proposed Changes)

### Couche A — Schema & Extraction (cœur)

- #### `[MODIFY]` [`src/pipelines/evidence_pack.py`](file:///c:/Memory%20Loop/src/pipelines/evidence_pack.py)
  - **Intention** : Ajouter les TypedDict/structure de champs + injection dans le dict retourné par `extract_evidence` (l.611-633).
  - **Impact** :
    1. Nouveaux types : `VerbatimExtract`, `ImplementationDecision`, `DeclarativeContract`, `ConflictResolution` (TypedDict total=False).
    2. Champs Optionals injectés dans `evidence_pack` : `verbatim_extracts`, `implementation_decisions`, `declarative_contracts`, `conflict_matrix`.
    3. Enrichissement `epistemic_audit` : `what_it_actually_proves` / `what_it_does_not_prove` (listes non vides exigées pour `VALIDATED`), + `richness_penalty: {score, richness, multiplier, reason}`.
    4. Calcul déc.5 : multiplicateur sur `root_score` **après** le calcul existant, **avant** le return ; `root_confidence` dégradé HIGH→MEDIUM si multiplicateur < 0.85.
    5. Catégories fermées `implementation_decisions.category` : `{architecture, pattern, refactoring, performance, security, tooling, testing}` — rejet hors liste → `ValueError` contextualisé (pas de swallow).
    6. Lecture rétrocompatible : `existing_data.get("implementation_decisions", [])` etc. lors de la merge de `preserved_*` (aucun `.get` sans défaut sur les 5 champs).
  - **Impact blast radius** : 9 callers (`wikifix_auditors.py`, `certificate.py`, `_sync_evidence_pack_sidecar`, `persist_to_evidence_pack`) — signature inchangée (`Dict[str, Any]`), **aucun caller ne doit être modifié**.

### Couche B — Tests (Failure Contract ADR-0369)

- #### `[MODIFY]` [`tests/test_evidence_pack.py`](file:///c:/Memory%20Loop/tests/test_evidence_pack.py)
  - **Intention** : Couvrir CA-1→CA-6 + standards ADR-0369 (parametrize + pytest.raises).
  - **Nouveaux tests** (minima) :
    1. `test_extract_evidence_includes_5_parity_fields_by_default` — pack neuf sans données source → 5 champs présents (listes vides / dicts vides).
    2. `test_verbatim_extracts_requires_nonempty_quote_and_lines` — `@pytest.mark.parametrize` sur quote vide / lines invalides → `ValueError`.
    3. `test_implementation_decision_category_closed_list` — `@pytest.mark.parametrize` sur les 7 catégories valides + `pytest.raises(ValueError)` pour `category="invalid"`.
    4. `test_epistemic_audit_what_it_does_not_prove_nonempty_for_validated` — pack `VALIDATED` avec `what_it_does_not_prove == []` → rejet documenté (délégué à validateur ou assertion d'auto-correction).
    5. `test_richness_multiplier_applied_to_confidence_score` — richesse=0 → multiplicateur 0.7 ; richesse=max → 1.0 (formule déc.5).
    6. `test_legacy_pack_without_5_fields_still_parses` — fixture JSON legacy (aucun des 5 champs) → `extract_evidence` + rechargement sans KeyError (CA-5).
    7. `test_conflict_matrix_and_declarative_contracts_optional_backcompat` — pack existant avec les champs absents → `.get(..., [])` OK.
  - **Impact** : aucun test existant supprimé ; tests existants (ex: `test_evidence_pack_extraction`, `test_evidence_pack_no_hardcoded_high_confidence_without_code_proof`) doivent rester VERTS.

### Couche C — Aucun autre fichier

- Pas de modification de `story_template.md`, de `_registry.py`, de `sync.py`, ni de `state_machine.py` (hors périmètre MLOOP-181-BE pour l'intégration harnais).

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| Rupture de rétrocompat (71 packs legacy sans les 5 champs) | **Élevé** | Champs `Optional` + `.get(..., [])` partout + test CA-5 obligatoire ; rollback = `git checkout src/pipelines/evidence_pack.py tests/test_evidence_pack.py` |
| Régression confidence_score (multiplicateur mal calé) | Moyen | Multiplicateur borné `[0.7, 1.0]` ; test `test_richness_multiplier` verrouille la formule ; `root_confidence` inchangé si multiplicateur ≥ 0.85 |
| Performance (parsing fact_dossier double) | Faible | Aucun nouvel accès disque par pack — les champs dérivent des structures déjà extraites (`dossier_data`, `content`) |
| Collision avec worker `cline` (EPIC-17, pane w8:p1) | Faible | Périmètres disjoints : `cline` touche `MLOOP-171-BE` / backlog EPIC-17 ; ce worker touche **uniquement** `src/pipelines/evidence_pack.py` + `tests/test_evidence_pack.py` |
| `except Exception` silencieux violant ADR-0369 | Moyen | Interdiction de `pass` nu — tout catch doit logger `logger.debug(..., exc_info=True, extra={...})` (pattern existant du fichier conservé) |

**Rollback global** : `git stash` / `git checkout -- src/pipelines/evidence_pack.py tests/test_evidence_pack.py` puis `python -m pytest tests/test_evidence_pack.py`.

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [x] `python -m pytest tests/test_evidence_pack.py -v` → **0 failure**, nouveaux tests inclus. (28/28 PASS)
- [x] `python -m pytest tests/test_evidence_pack.py tests/test_grill_engine.py -v` → régression croisée callers. (35/35 PASS)
- [x] `python src/swarm.py struct-check --project mLoop` → Gate C12 sans nouveau bloquant. (tous conformes)
- [x] `python src/swarm.py code-check --file src/pipelines/evidence_pack.py` → zéro nouvelle violation RULE-AST. (2 préexistantes RULE-AST-01 hors périmètre)
- [x] `python src/swarm.py guide --sync` **non requis** (aucune modification `_registry.py`).

### B. Vérifications Manuelles & Scénarios Clés
- [x] **Scénario Nominal (Gherkin Pilier 1)** : récit avec 2 décisions + 3 citations + 1 contrat → pack contient les 5 champs peuplés. (test_nominal)
- [x] **Scénario d'Exception (Pilier 2)** : `category` hors liste fermée → `ValueError` propagée (pas de swallow).
- [x] **Scénario Rétrocompat (CA-5)** : recharger un legacy sans les 5 champs → aucune KeyError, 5 champs defaultés.
- [x] **Scénario Confiance (Déc.5)** : pack vide → `confidence_score` multiplié par 0.7, `richness_penalty` présent dans `epistemic_audit`.

### C. Definition of Done (DoD)
- [x] Tous les fichiers modifiés : zéro lint error, ADR-0369 respecté (timeout sur I/O si ajouté, context managers, logging structuré).
- [x] Plan archivé : `Projects/mLoop/memory/plan/implementation_plan_MLOOP-180-BE.md` (ce fichier).
- [x] Statut récit mis à jour en fin de BUILD : `READY_FOR_DEV` → `IN_QA` (via `IN_DEV`, FSM l.115-130) + `stamp_content_hash` ré-exécuté (hash inchangé `a7d2aff6082bfc4e` — corps non modifié).
- [x] `python src/swarm.py sync --project mLoop` VERT (0 erreur bloquante). (2ᵉ passage vert après ré-estampage anti-tampering MLOOP-171-BE)
- [x] FRAMEWORK_STATE.md mis à jour (entrée datée 2026-09-22 — extension schema).

---

## 6. Exécution Déléguée (Delegation Gate)

- **Critères remplis** : Durée >5min (schema + 7+ tests) + Type `build` multi-fichiers → **2/4 OUI**.
- **Canal** : `python src/swarm.py worker-spawn --project mLoop --story MLOOP-180-BE --task-type build`.
- **Isolation** : worker ne touche **que** `src/pipelines/evidence_pack.py` + `tests/test_evidence_pack.py` ; ne pas éditer le récit, le backlog, ni FRAMEWORK_STATE (l'orchestrateur le fera au harvest).
- **Séquence Teardown** : spawn → wait WORKING → harvest → close (Zéro Session Zombie).
