---
created: 2026-09-24T14:49:40.260Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, epic-19-click-cli-engine]
---

[[Plannotator Plans]]

# Plan d'Implémentation — EPIC-19-CLICK-CLI-ENGINE (MLOOP-190→194)

> **Niveau** : 3 — Critique / Architecture (ADR-0305) · **Statut** : `DRAFT` (bloquant, feu vert humain requis)
> **Cadre** : auto-développement framework `C:\Memory Loop\src` uniquement · **Jira** : moratoire PO (zéro write/push)
> **FRAMEWORK_STATE** lu (2026-09-22) — checklist ADR-0352 : status source `READY_FOR_DEV` ✓ · certificat NLI : AUCUN pour ces récits (rubber-duck 5/5 APPROUVÉ) → pas d'invalidation · `verification_harness` non vide 5/5 ✓ · `struct-check` inclus §5A ✓ · transitions d'état valides (READY_FOR_DEV → IN_ANALYZE → DONE)

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> Décisions structurantes nécessitant ton **feu vert explicite** :
>
> - **A1 — Click : obligatoire comme lib, install déjà fait, upgrade ciblé 192** :
>   1. **Le package Click est requis par les 5 récits** (context `click.Context`, `click.MultiCommand`, `CliRunner`, `HelpFormatter`) — sans lui, EPIC-19 n'existe pas. Ce n'est pas un optional.
>   2. **Aucun install neuf n'est nécessaire pour démarrer** : `click **8.3.1**` est déjà importable dans l'environnement runtime actuel — 190 / 191 / 193 / 194 peuvent s'implémenter dessus dès aujourd'hui.
>   3. **Déclarer `click>=8.5,<9` dans `pyproject.toml` reste à faire** : aujourd'hui Click n'est qu'une dep **transitif** (lock 8.4.2, aucune ligne dans `[project.dependencies]`) → pin pour build hermétique + compat future.
>   4. **Le seuil ≥ 8.5 n'est critique QUE pour MLOOP-192-BE** (completion PowerShell native `powershell_source`, feature Click 8.5+). Sans bump : 4 récits sur 5 livrables en 8.3.1, mais **CA-1 de 192 non conforme** (bash/zsh seuls).
>   *Recommandation : pin `click>=8.5,<9` + `uv sync` (couvre 192 sans dette). *Alternative refus bump* : livrer 190/191/193/194 en 8.3.1 et marquer 192 `ON_HOLD` completion PowerShell — à trancher explicitement.*
> - **A2 — Migration `src/cli.py` → package `src/cli/`** : le récit impose `src/cli/click_engine/…` mais `src/cli.py` existe (170L, `ZeroFluffConsole`, **44 importateurs**). *Recommandation : déplacer le contenu dans `src/cli/__init__.py` (API `from src.cli import ZeroFluffConsole` **stabile**, zéro rewrite des 44 callers), puis créer `src/cli/click_engine/`.*
> - **A3 — Stratégie de bascule (zéro régression)** : drapeau d'environnement `MLOOP_CLI_ENGINE=argparse|click` (défaut **argparse** à l'arrivée de 191, bascule **click** après vert de 194 + mesure boot). *Recommandation : flag + ArgsShim → rollback = 1 variable, sans revert Git.*
> - **A4 — Chiffre commandes** : l'épopée cite « 58 commandes » ; le registre réel expose **121**. Les CA des récits parlent de 58. *Recommandation : traiter 121 comme surface réelle, ajuster les CA textuels sans changer le sens (lazy-load sur TOUTES les commandes du registre).*
> - **A5 — Orchestration Workers** : workers créés par CETTE session uniquement (DAG ci-dessous). `w1:p1` jamais fermé · `w1:p3C`/`w1:p3D` intouchés (WORKING, hors session).
> - **A6 — Push final** : après DoD epic verte uniquement → racine = `main` ; `Projects/mLoop` = `git push origin HEAD:project-mLoop`. **Zéro push Jira.**

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-01** : Conserver `src/commands/router.py` argparse intact derrière le flag, ou le marquer `DEPRECATED` dès la bascule click ? → *Recommandation : conserver intact (rollback), documenter dans le docstring.*
> - **OQ-02** : Ajouter la commande `completion-setup` dans le registre (nécessite `guide --sync` ADR-0370) ? → *Recommandation : oui, `no_project: true`, + `python src/swarm.py guide --sync` immédiat.*
> - **OQ-03** : Mesure « boot ÷ ≥3 » (DoD epic) : baseline argparse aujourd'hui vs click après 191 — accepter un bench script `tests/bench_cli_boot.py` ou mesure manuelle ? → *Recommandation : petit bench pytest marqué `@pytest.mark.bench` (hors CI stricte), inclus dans 194.*

---

## 3. Modifications Proposées (Proposed Changes)

Ordre DAG strict : **Socle → 190 → 191 → (192 ∥ 193) → 194**.

### Étape 0 — Socle préalable (non story, bloquant)

- #### `[MODIFY]` [`pyproject.toml`](file:///c:/Memory%20Loop/pyproject.toml)
  - **Intention** : déclarer `click>=8.5,<9` dans `dependencies` (A1).
  - **Impact** : `[project.dependencies]` ; `uv lock`/`uv sync` à exécuter.

- #### `[MODIFY]` [`src/cli.py`](file:///c:/Memory%20Loop/src/cli.py) → `[NEW]` [`src/cli/__init__.py`](file:///c:/Memory%20Loop/src/cli/__init__.py)
  - **Intention** : migration module → package sans rupture d'import (A2). Contenu 170L déplacé à l'identique.
  - **Impact** : 44 call sites `from src.cli import …` inchangés.
  - **Note** : suppression du fichier `src/cli.py` après vérification que le package prime (PEP 328, même pattern que `_registry`).

- #### `[NEW]` [`src/cli/click_engine/__init__.py`](file:///c:/Memory%20Loop/src/cli/click_engine/__init__.py)
  - **Intention** : package vide + docstring EPIC-19 ; point d'ancrage des 4 modules stories.

### Étape 1 — MLOOP-190-BE : Contexte & Lifecycle Middleware

- #### `[NEW]` [`src/cli/click_engine/context.py`](file:///c:/Memory%20Loop/src/cli/click_engine/context.py) (≤300L RULE-AST-01)
  - **Intention** : `MLoopContext` (`project_name`, `project_path`, `state`, `timing_start`, `command`), décorateur `@pass_mloop_context`, middleware `lifecycle_gate_guard(ctx, cmd_name)` → `ProjectLifecycleManager.can_execute_command` / `get_project_context` / `SemanticLexiconResolver` (via `resolve_project_name`).
  - **CA** : CA-1…CA-6 (exit 1 + logs structurés `command/project/phase/reason/exit_code`, `no_project=True` exempt, ZeroFluffConsole sur projet manquant, alias sémantique).

### Étape 2 — MLOOP-191-BE : Routeur Lazy + ArgsShim + Entrée unifiée

- #### `[NEW]` [`src/cli/click_engine/router.py`](file:///c:/Memory%20Loop/src/cli/click_engine/router.py) (≤300L)
  - **Intention** : `MLoopMultiCommand(click.MultiCommand)` — `list_commands` depuis `COMMANDS` (sans import handlers), `get_command` lazy via `_resolve_handler` réutilisé ; `ArgsShim(argparse.Namespace)` conversion flags/int/str/list ; `cli` groupe racine branché sur `MLoopContext` + gate.

- #### `[MODIFY]` [`src/swarm.py`](file:///c:/Memory%20Loop/src/swarm.py)
  - **Intention** : `main()` lit `MLOOP_CLI_ENGINE` (défaut `argparse`) ; si `click` → `cli.main(...)` avec capture KeyboardInterrupt (130) / SystemExit / exceptions structurées conservant l'instrumentation actuelle ; si `argparse` → `execute_cli()` **inchangé** (rollback).
  - **Impact** : `main()` uniquement — `resolve_project_name` / `get_project_context` intacts (réutilisés par 190).

- #### `[KEEP]` [`src/commands/router.py`](file:///c:/Memory%20Loop/src/commands/router.py)
  - **Intention** : chemin legacy préservé (A3/OQ-01). Aucune suppression.

### Étape 3a — MLOOP-192-BE : Complétion Shell

- #### `[NEW]` [`src/cli/click_engine/completion.py`](file:///c:/Memory%20Loop/src/cli/click_engine/completion.py) (≤300L)
  - **Intention** : `complete_projects` / `complete_stories` / `complete_task_types` (shell_complete, I/O sécurisées DEBUG, <15ms) ; commande `completion-setup` (`no_project: true`) détectant pwsh/bash/zsh.

- #### `[MODIFY]` [`src/commands/_registry/_reg_runtime_ops.py`](file:///c:/Memory%20Loop/src/commands/_registry/_reg_runtime_ops.py) (ou sous-registre approprié)
  - **Intention** : déclarer `completion-setup` → handler dédié léger.
  - **Impact** : **obligatoire** `python src/swarm.py guide --sync` (ADR-0370) juste après.

### Étape 3b — MLOOP-193-BE : Aide par Phases & Path Typé

- #### `[NEW]` [`src/cli/click_engine/formatter.py`](file:///c:/Memory%20Loop/src/cli/click_engine/formatter.py) (≤300L)
  - **Intention** : `PhaseHelpFormatter` + matrice 6 phases + `Utilitaires transverses` (fallback) ; helpers `path_exists()` / `dir_exists()` / `choice_param()`.
  - **Branchement** : format_help du groupe racine dans `click_engine/router.py` (petit diff, pas de logique dispatch).

### Étape 4 — MLOOP-194-BE : Harnais CliRunner

- #### `[NEW]` [`tests/test_click_cli_engine.py`](file:///c:/Memory%20Loop/tests/test_click_cli_engine.py) (≤300L)
  - **Intention** : CliRunner in-process — lazy load, MLoopContext, gate hit/miss, 6 commandes vitales (`vibe-check`, `gate-approve`, `sync`, `crawl`, `lifecycle-status`, `worker-spawn`), ArgsShim unit, codes 0/1/2/130, bench in-process vs subprocess. **Zéro `subprocess.run` dans le fichier de test cible.**
  - **Note** : commandes vitales testées en mode lecture/dry-run ou mock léger là où l'effet de bord est dangereux (pas de push, pas de Jira).

### Étape 5 — Clôture épopée (post-DoD)

- #### `[MODIFY]` [`Projects/mLoop/backlog/sprint_backlog.md`](file:///c:/Memory%20Loop/Projects/mLoop/backlog/sprint_backlog.md)
  - **Intention** : 5 lignes → `[x]` / `DONE` + résumé QA ; header épopée `[DONE]`.
- #### `[MODIFY]` [`Projects/mLoop/backlog/epics/epic_click_cli_engine.md`](file:///c:/Memory%20Loop/Projects/mLoop/backlog/epics/epic_click_cli_engine.md)
  - **Intention** : statut épopée `DONE` + note DoD (boot mesuré, 121 commandes, flag).
- #### `[MODIFY]` frontmatter des 5 récits → `status: DONE` + EvidencePacks enrichis (impl traces).
- #### Git (si feu vert A6) : racine `main` ; `Projects/mLoop` → `HEAD:project-mLoop`. **Aucun `jira_sync`.**

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact | Atténuation / Rollback |
| :--- | :---: | :--- |
| Click 8.5 casse un transitif (rich, etc.) | Moyen | Pin `click>=8.5,<9` ; `uv sync` + suite tests existante ; rollback = retirer la dep |
| Migration `cli.py`→package casse les 44 imports | Élevé | Déplacement à l'identique + pytest import smoke ; pattern éprouvé `_registry` |
| Bascule click = régression 121 commandes | Élevé | Flag `MLOOP_CLI_ENGINE` défaut argparse jusqu'au vert 194 |
| ArgsShim tronque un type (list/bool) | Moyen | Tests unit 194 + parcours vital 6 commandes |
| `completion-setup` non sync guide CLI | Faible | `guide --sync` obligatoire dans le worker 192 (checklist DoD) |
| Worker hors session fermé par erreur | Élevé | Teardown Gate stricte : close uniquement workers spawnés ici |
| Écriture Jira accidentelle | Élevé | Zéro appel `jira_sync` ; moratoire PO non négociable |
| Fichiers click_engine >300L | Moyen | `struct-check` + ruff ; split immédiat si >300 |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] `struct-check` sur `src/cli/click_engine/*.py` + `tests/test_click_cli_engine.py` (**Gate C12 — obligatoire**) : chaque fichier ≤ 300 lignes.
- [ ] `python -m pytest tests/test_click_cli_engine.py -q` → 100% vert, < 2.0s.
- [ ] `python -m pytest tests/test_cli_logging.py tests/test_project_lifecycle.py tests/test_worker_spawn_lifecycle_gating.py -q` (non-régression voisine).
- [ ] `python src/swarm.py guide --sync` après ajout `completion-setup` (parité 121+1 commandes).
- [ ] Smoke argparse : `python src/swarm.py lifecycle-status --project mLoop` exit 0 (flag défaut).
- [ ] Smoke click : `$env:MLOOP_CLI_ENGINE='click'; python src/swarm.py lifecycle-status --project mLoop` exit 0.
- [ ] `python src/swarm.py vibe-check --project mLoop` → ≥ 22 PASS / 0 FAIL.
- [ ] Bench boot argparse vs click (DoD epic : objectif ÷ ≥ 2 en CA-5 / ÷ ≥ 3 en DoD).
- [ ] `python src/swarm.py struct-check` / ruff sur les fichiers touchés (zéro lint error).

### B. Vérifications Manuelles & Scénarios Clés
- [ ] **Nominal click** : commande vitale avec `--project mLoop` → 0, contexte injecté.
- [ ] **Gate violation** : commande interdite en phase → `[LIFECYCLE GATE VIOLATION]` + exit 1, handler non appelé.
- [ ] **Projet manquant** : erreur claire + liste `Projects/`, exit 1, pas de traceback.
- [ ] **Commande inconnue** : exit 2 + did-you-mean.
- [ ] **Ctrl+C** : exit 130 propre.
- [ ] **Help phases** : `loop --help` (click) affiche Phase 0→5 + transverses.
- [ ] **Completion** : `_LOOP_COMPLETE=powershell_source` + TAB sur `--project` (pwsh) ; bash_source équivalent.
- [ ] **Rollback** : unset flag → comportement argparse identique au pré-chantier.
- [ ] **Workers** : `worker-status` → seuls workers session fermés à la fin ; `w1:p1/p3C/p3D` vivants.

### C. Definition of Done (DoD)
- [ ] 5 récits exécutés, CA cochés, frontmatter `DONE`, EvidencePacks enrichis.
- [ ] `sprint_backlog` EPIC-19 `[DONE]` 5/5 + épopée `DONE`.
- [ ] Chaque module click_engine ≤ 300L (RULE-AST-01).
- [ ] Zéro écriture Jira · Git : racine `main` / `Projects/mLoop` → `project-mLoop` (si A6 avalisé).
- [ ] Plans archivés : `Projects/mLoop/memory/plan/implementation_plan_MLOOP-19{0..4}-BE.md` (après APPROVED).
- [ ] Teardown : workers de session fermés ; `w1:p1` intact.
- [ ] ADR-0376 : changements cœur moteur couverts par ce plan zéro-blindspot (blueprints intacts, protocols inchangés sauf guide --sync, tests 7ᵉ couche).

---

## Orchestration (post-approval) — Delegation Gate 4/4 OUI

| Ordre | Story | Worker (session) | task-type | Dépend |
| :---: | :--- | :--- | :--- | :--- |
| 0 | Socle (pyproject + cli package) | W-EPIC19-S0 | `build` | — |
| 1 | MLOOP-190-BE | W-EPIC19-190 | `build` | S0 |
| 2 | MLOOP-191-BE | W-EPIC19-191 | `build` | 190 |
| 3a | MLOOP-192-BE | W-EPIC19-192 | `build` | 191 |
| 3b | MLOOP-193-BE | W-EPIC19-193 | `build` | 191 (∥ 192) |
| 4 | MLOOP-194-BE | W-EPIC19-194 | `validation` | 190+191 |
| 5 | Clôture backlog + gates | orchestrateur (w1:p1) | — | DoD |

Séquence stricte : `worker-spawn` → attendre WORKING → `worker-harvest` → `worker-close` **uniquement** pour ces IDs. Jamais `w1:p1` / `w1:p3C` / `w1:p3D`.

**Estimation** : S0+190+191 critiques (séquentiels) ; 192∥193 parallèles ; 194 final.
