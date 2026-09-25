---
id: PLAN-EPIC-19-CLICK-CLI-ENGINE
story_id: MLOOP-190-BE..MLOOP-194-BE
status: APPROVED
harness: opencode
created_at: 2026-09-24
approved_at: 2026-09-24
---

# Implémentation EPIC-19 — Moteur CLI Click (MLOOP-190→194)

> **Objectif** : Migrer le moteur d'exécution CLI mLoop d'argparse vers Click (lazy-loading, contexte unifié, completion shell, aide par phases, harnais CliRunner) sans régression sur les 121 commandes du registre, via flag `MLOOP_CLI_ENGINE`.

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Validé par l'humain le 2026-09-24** (plan Niveau 3 ADR-0305, archivé `.plannotator/plans/plan-dimplmentation-epic-19-cl-2026-09-24-approved.md`) :
> - **A1 — Click** : lib obligatoire (déjà 8.3.1) ; pin `click>=8.5,<9` dans `pyproject.toml` (bump requis pour completion PowerShell MLOOP-192).
> - **A2 — Migration `src/cli.py` → package `src/cli/`** : déplacer vers `src/cli/__init__.py` (44 imports stables), créer `src/cli/click_engine/`.
> - **A3 — Bascule** : flag `MLOOP_CLI_ENGINE=argparse|click` (défaut argparse), rollback = 1 variable.
> - **A4 — Surface réelle** : 121 commandes (pas 58/103) ; lazy-load sur tout le registre.
> - **A5 — Workers** : session isole ses workers ; `w1:p1`/`w1:p3C`/`w1:p3D`/`w1:p3E` intouchés.
> - **A6 — Push** : racine `main` / `Projects/mLoop` → `project-mLoop` ; **zéro Jira** (moratoire PO).

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-01** : conserver `src/commands/router.py` intact derrière le flag → **OUI** (rollback).
> - **OQ-02** : commande `completion-setup` au registre + `guide --sync` → **OUI**.
> - **OQ-03** : bench boot (`@pytest.mark.bench`) dans MLOOP-194 → **OUI**.

---

## 3. Modifications Proposées (Proposed Changes)

Ordre DAG : **Socle → 190 → 191 → (192 ∥ 193) → 194 → clôture**.

### Étape 0 — Socle
- `[MODIFY]` `pyproject.toml` : ajouter `click>=8.5,<9` + `uv sync`.
- `[MODIFY]` `src/cli.py` → `[NEW]` `src/cli/__init__.py` (contenu 170L à l'identique, 44 imports stables).
- `[NEW]` `src/cli/click_engine/__init__.py` : package d'accueil.

### Étape 1 — MLOOP-190-BE (context + gate)
- `[NEW]` `src/cli/click_engine/context.py` ≤300L : `MLoopContext`, `@pass_mloop_context`, `lifecycle_gate_guard` → `ProjectLifecycleManager.can_execute_command` / `SemanticLexiconResolver`.

### Étape 2 — MLOOP-191-BE (routeur lazy)
- `[NEW]` `src/cli/click_engine/router.py` ≤300L : `MLoopMultiCommand`, `ArgsShim`, `cli`.
- `[MODIFY]` `src/swarm.py` : `main()` lit `MLOOP_CLI_ENGINE` (défaut argparse → `execute_cli()` intact ; click → `cli.main`).
- `[KEEP]` `src/commands/router.py` : chemin legacy préservé.

### Étape 3a — MLOOP-192-BE (completion)
- `[NEW]` `src/cli/click_engine/completion.py` ≤300L : `complete_projects/stories/task_types`, `completion-setup`.
- `[MODIFY]` registre sous-registre runtime : déclarer `completion-setup` + `guide --sync` obligatoire.

### Étape 3b — MLOOP-193-BE (aide phases) — parallèle à 192
- `[NEW]` `src/cli/click_engine/formatter.py` ≤300L : `PhaseHelpFormatter`, `path_exists`, `dir_exists`, `choice_param`.
- `[MODIFY]` branchement `format_help` sur `click_engine/router.py`.

### Étape 4 — MLOOP-194-BE (harnais)
- `[NEW]` `tests/test_click_cli_engine.py` ≤300L : CliRunner in-process, 6 vitales, codes 0/1/2/130, bench. Zéro `subprocess.run`.

### Étape 5 — Clôture
- Frontmatter 5 récits → `DONE` + EvidencePacks enrichis.
- `sprint_backlog.md` EPIC-19 → `[DONE]` 5/5 ; épopée → `DONE`.
- Git (A6) uniquement si DoD verte.

---

## 4. Gestion des Risques & Rollback

| Risque | Impact | Atténuation / Rollback |
| :--- | :---: | :--- |
| Click 8.5 casse un transitif | Moyen | Pin `<9` ; `uv sync` + tests ; rollback = retirer dep |
| Migration `cli.py` casse 44 imports | Élevé | Déplacement à l'identique + smoke import ; pattern `_registry` |
| Bascule click = régression | Élevé | Flag défaut `argparse` jusqu'au vert 194 |
| ArgsShim tronque un type | Moyen | Tests unit 194 + 6 vitales |
| Worker hors session fermé | Élevé | Teardown stricte : close uniquement workers session |
| Écriture Jira accidentelle | Élevé | Zéro `jira_sync` |
| Module >300L (RULE-AST-01) | Moyen | `struct-check` + split immédiat |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] `struct-check` sur `src/cli/click_engine/*.py` + test (≤300L).
- [ ] `python -m pytest tests/test_click_cli_engine.py -q` → 100% vert, <2.0s.
- [ ] Non-régression : `tests/test_cli_logging.py`, `test_project_lifecycle.py`, `test_worker_spawn_lifecycle_gating.py`.
- [ ] `python src/swarm.py guide --sync` après `completion-setup`.
- [ ] Smoke argparse + smoke click (`MLOOP_CLI_ENGINE=click`) sur `lifecycle-status --project mLoop`.
- [ ] `python src/swarm.py vibe-check --project mLoop` ≥22 PASS / 0 FAIL.
- [ ] Bench boot argparse vs click (CA-5 ÷≥2, DoD ÷≥3).

### B. Vérifications Manuelles & Scénarios Clés
- [ ] Nominal click → exit 0, contexte injecté.
- [ ] Gate violation → `[LIFECYCLE GATE VIOLATION]` + exit 1, handler non appelé.
- [ ] Projet manquant → liste `Projects/`, exit 1, pas de traceback.
- [ ] Commande inconnue → exit 2 + did-you-mean.
- [ ] Ctrl+C → exit 130.
- [ ] `--help` phases + transverses.
- [ ] Completion TAB pwsh/bash.
- [ ] Rollback : unset flag → argparse identique.
- [ ] Workers : seuls workers session fermés ; `w1:p1/p3C/p3D/p3E` vivants.

### C. Definition of Done (DoD)
- [ ] 5 récits `DONE`, EvidencePacks enrichis, CA cochés.
- [ ] `sprint_backlog` EPIC-19 `[DONE]` 5/5 + épopée `DONE`.
- [ ] Modules ≤300L (RULE-AST-01).
- [ ] Zéro Jira ; Git A6 si avalisé.
- [ ] Teardown workers session ; `w1:p1` intact.
- [ ] ADR-0376 : couvert par ce plan zéro-blindspot.

---

## Orchestration (Delegation Gate 4/4 OUI)

| Ordre | Story | Worker | task-type | Dépend |
| :---: | :--- | :--- | :--- | :--- |
| 0+1 | Socle + MLOOP-190 | W-EPIC19-190 | build | — |
| 2 | MLOOP-191 | W-EPIC19-191 | build | 190 |
| 3a | MLOOP-192 | W-EPIC19-192 | build | 191 |
| 3b | MLOOP-193 | W-EPIC19-193 | build | 191 (∥ 192) |
| 4 | MLOOP-194 | W-EPIC19-194 | validation | 190+191 |
| 5 | Clôture backlog | orchestrateur (w1:p1) | — | DoD |

Séquence : `worker-spawn` → WORKING → `worker-harvest` → `worker-close` uniquement pour ces IDs.
