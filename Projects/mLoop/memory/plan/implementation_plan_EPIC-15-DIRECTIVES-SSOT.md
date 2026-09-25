---
id: PLAN-EPIC-15
story_id: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
status: DRAFT
harness: opencode
created_at: 2026-09-22
---

# Plan d'Implémentation Zéro Blindspot — EPIC-15 Application du Chargement des Directives Projet & Ancrage SSOT

> **Objectif** : Combler le gap de gouvernance qui a permis qu'un audit soit conduit sur des sources non autoritaires (incident BoireFrere_Segment2). Le plan couvre 6 récits (`MLOOP-160` à `MLOOP-165-BE`) à travers les 7 couches de l'écosystème mLoop (ADR-0376), avec un design conditionnel strictement non-régressif pour les 7 projets dépourvus de répertoire `directives/`.

---

## 0. Conformité Prérequis FRAMEWORK_STATE (ADR-0352)

- [x] **Status source vérifié** : les 6 récits sont en `IN_ANALYZE` (frontmatter lu, non supposé).
- [x] **Certificat NLI daté** : aucun certificat NLI préexistant pour ces récits (créés le 2026-09-22, postérieurs au dernier commit FRAMEWORK_STATE du 2026-09-21) → aucune régénération requise.
- [x] **struct-check inclus dans §5A** : oui (déjà exécuté, 6/6 conformes ; ré-exécution en recette).
- [x] **verification_harness** : défini en §5 (tests pytest + struct-check + rubber-duck + vibe-check auto-appliqué).
- [x] **Transition d'état valide** : `IN_ANALYZE` → `READY_FOR_DEV` sur approbation humaine, puis `IN_DEV` à l'exécution.

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes actées au Grill 22/09 — confirmation d'exécution requise :**
> - **Changement de sémantique du verdict Vibe-Check pour TOUS les projets** (D1) : le calcul `is_valid` passe de binaire (`passed == total`) à tri-état (PASS/WARNING/FAIL). Les scores de tous les projets seront recalculés au fil de l'eau. **Impact transverse assumé.**
> - **Modification de la charte racine `AGENTS.md`** (récit 161) : ajout d'une clause en §4.1, propagée aux miroirs GEMINI.md/CLAUDE.md par l'auto-sync du Check 1.
> - **Correction de `Projects/BoireFrere_Segment2/AGENTS.md`** : un fichier de projet client est touché — mais uniquement sa charte d'instructions (gouvernance), jamais son code. À valider vis-à-vis de l'herméticité.
> - **Deux nouveaux contrôles dans le guardrail de pré-vol** (Check directives + Check ancrage visuel), tous deux WARNING non bloquants.

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-01** : Numérotation ADR — `0384` est la référence de travail. → *Recommandation : reconfirmer `Get-ChildItem standards/adr-system/0*.md` au moment de créer le fichier (récit 161) et re-numéroter si collision.*
> - **OQ-02** : Le correctif `is_valid` touche le Check 17 (QA) existant qui émet déjà des WARNING. → *Recommandation : vérifier qu'aucun test n'assertait un FAIL global sur un scénario Check 17 WARNING ; réaligner si besoin (récit 164).*
> - **OQ-03** : La correction de la charte du projet Boire est-elle dans le périmètre de cette epic framework, ou à traiter dans la reprise Boire distincte (D6) ? → *Recommandation : la garder ici (c'est une correction de gouvernance, pas du code Boire), mais la signaler explicitement à l'humain.*

---

## 3. Modifications Proposées (Proposed Changes)

Groupées par couche ADR-0376, ordonnées par dépendance (`160 → 161 → 162 ∥ 163 → 164 ∥ 165`).

### Couche 2 — Protocoles (récit MLOOP-160-BE)

- #### `[NEW]` [`standards/protocols/PROJECT_DIRECTIVES_SSOT_PROTOCOL.md`](file:///c:/Memory%20Loop/standards/protocols/PROJECT_DIRECTIVES_SSOT_PROTOCOL.md)
  - **Intention** : Protocole autonome court (~40 lignes) : hiérarchie SSOT à 3 niveaux, obligation de localisation avant délégation, catalogue des directives impératives, distinction des 2 mécanismes de gouvernance.

### Couche 3 — Architecture ADR (récit MLOOP-161-BE)

- #### `[NEW]` [`standards/adr-system/0384-project-directives-ssot-boot-enforcement.md`](file:///c:/Memory%20Loop/standards/adr-system/0384-project-directives-ssot-boot-enforcement.md)
  - **Intention** : ADR Type 1 additif consignant la décision, la hiérarchie SSOT, le caractère conditionnel/non-bloquant. Garde de re-numérotation au build.
- #### `[MODIFY]` [`standards/adr-system/README.md`](file:///c:/Memory%20Loop/standards/adr-system/README.md)
  - **Intention** : Indexer l'ADR-0384 par thème.

### Couche 4 — Directives & Chartes (récit MLOOP-161-BE)

- #### `[MODIFY]` [`AGENTS.md`](file:///c:/Memory%20Loop/AGENTS.md)
  - **Intention** : Ajouter en §4.1 « Always do » la clause « Chargement des Directives Projet & SSOT Canonique » (lecture directives + identification SSOT en Phase ≥ 2).
  - **Impact** : Miroirs `GEMINI.md` + `CLAUDE.md` auto-synchronisés par le Check 1 du vibe-check.
- #### `[MODIFY]` [`Projects/BoireFrere_Segment2/AGENTS.md`](file:///c:/Memory%20Loop/Projects/BoireFrere_Segment2/AGENTS.md)
  - **Intention** : Lister `directives/` dans la structure projet et déclarer `docs/03-models/` comme SSOT autoritaire (au lieu de `reference/`). *(Voir OQ-03.)*

### Couche 5 — Skills (récit MLOOP-162-BE)

- #### `[MODIFY]` [`.agents/skills/grill/SKILL.md`](file:///c:/Memory%20Loop/.agents/skills/grill/SKILL.md)
  - **Intention** : Enrichir l'Étape 0 « Search-Before-Ask » : ordre de recherche imposé (directives en tête), interdiction de brief non sourcé, citation SSOT dans le dossier de preuves.

### Couche 6 — Core Python (récits MLOOP-163-BE & MLOOP-165-BE)

- #### `[MODIFY]` [`src/pipelines/vibe_check.py`](file:///c:/Memory%20Loop/src/pipelines/vibe_check.py)
  - **Intention (163)** : Ajouter le contrôle « Intégrité Directives Projet & SSOT » après le Check 19 (L~710) ; corriger le calcul `is_valid` en sémantique tri-état (L712-723).
  - **Intention (165)** : Étendre la logique du Check 10 pour vérifier l'ancrage visuel des récits `layer: frontend`/`fullstack`.
  - **Impact** : `run_vibe_check` (L129) — 34 callers (`project_core.py`), 10 fichiers de tests (réalignés couche 7). Signature de sortie `dict` inchangée.
  - **Robustesse ADR-0369** : lectures fichiers en `try/except` + `logger.error(exc_info=True, extra={...})`, encoding explicite, aucune ressource hors `with`.

### Couche 7 — Tests (récit MLOOP-164-BE)

- #### `[NEW]` [`tests/test_vibe_check_directives_ssot.py`](file:///c:/Memory%20Loop/tests/test_vibe_check_directives_ssot.py)
  - **Intention** : 5 cas `parametrize` (conforme→PASS, absent→PASS, SSOT non déclaré→WARNING, tech.md vide→WARNING, WARNING n'invalide pas le verdict).
- #### `[MODIFY]` `tests/test_vibe_check_*.py` (10 fichiers, périmètre figé au build)
  - **Intention** : Réaligner les assertions encodant l'ancienne sémantique binaire sur la règle tri-état.

### Couche 1 — Blueprints
- **`[NO-OP]`** : Aucun gabarit créé/modifié/rendu caduc. Confirmé.

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **Correctif `is_valid` casse des tests existants** | Moyen | Réalignement volontaire (récit 164) ; `uv run pytest` vert obligatoire avant clôture ; rollback = revert du bloc calcul. |
| **Le Check directives bloque un projet sans `directives/`** | Élevé | Conditionnalité stricte : absence → PASS immédiat. Test dédié (cas 2) verrouille ce comportement. |
| **Auto-sync miroirs corrompt GEMINI/CLAUDE.md** | Moyen | Le Check 1 écrit depuis AGENTS.md (source unique) ; vérifier parité post-édition. |
| **Modification charte projet Boire viole l'herméticité** | Faible | Seule la charte de gouvernance est touchée, jamais le code Boire. Signalé en OQ-03 pour validation humaine. |
| **Numérotation ADR en collision** | Faible | Garde de re-numérotation au build (OQ-01). |
| **Faux positifs du Check ancrage visuel sur récits framework** | Faible | Cible restreinte à `layer: frontend`/`fullstack` ; `backend` exclu (RM-001 récit 165). |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] Commandes à exécuter :
  ```powershell
  uv run pytest tests/ -q
  python src/swarm.py struct-check --project mLoop
  python src/swarm.py vibe-check --project mLoop
  python src/swarm.py vibe-check --project Metro_FOOD   # non-régression : score inchangé hors nouveaux checks
  python src/swarm.py code-check --all                  # conformité AST ADR-0369
  ```

### B. Vérifications Manuelles & Scénarios Clés
- [ ] **Scénario Nominal** : `vibe-check --project BoireFrere_Segment2` → nouveau check directives PASS, verdict global valide.
- [ ] **Scénario Non-Régression** : `vibe-check --project Metro_FOOD` (sans `directives/`) → nouveau check PASS « non applicable », comportement inchangé.
- [ ] **Scénario Tri-État** : un projet avec directives incomplètes → WARNING, verdict global reste valide.
- [ ] **Scénario Ancrage Visuel** : un récit `frontend` sans maquette → WARNING listant le récit ; un récit `backend` → ignoré.
- [ ] **Parité Miroir** : `AGENTS.md` == `GEMINI.md` == `CLAUDE.md` après amendement.

### C. Definition of Done (DoD)
- [ ] `uv run pytest` 100% vert (incluant réalignement des tests existants).
- [ ] `code-check --all` sans nouvelle violation AST introduite par les modifications.
- [ ] `struct-check` 6/6 conformes + `rubber-duck` 0 rejet bloquant (déjà atteint au cadrage, à re-confirmer post-code).
- [ ] ADR-0384 indexé dans README ; clause racine présente dans les 3 miroirs.
- [ ] `guide --sync` non requis (aucune commande CLI ajoutée — à confirmer).
- [ ] Walkthrough de conformité rédigé.
- [ ] Ce plan archivé sous `Projects/mLoop/memory/plan/`.

---

## 6. Séquence d'Exécution Atomique (Couche par Couche)

1. **Couche 2** (récit 160) → protocole normatif.
2. **Couche 3** (récit 161) → ADR-0384 + index (garde de re-numérotation).
3. **Couche 4** (récit 161) → clause AGENTS.md racine + correction charte Boire.
4. **Couche 5** (récit 162) → skill grill.
5. **Couche 6** (récit 163) → Check directives + correctif tri-état `is_valid`.
6. **Couche 6** (récit 165) → Check ancrage visuel (dépend de la sémantique tri-état du 163).
7. **Couche 7** (récit 164) → tests neufs + réalignement.
8. **Certification** : Triple Gate §5 intégralement vert + walkthrough.

> **Interdiction formelle de coder avant approbation humaine explicite (ADR-0376).**
