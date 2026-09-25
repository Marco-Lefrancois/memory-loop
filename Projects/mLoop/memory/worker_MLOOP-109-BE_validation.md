# Worker Validation — MLOOP-109-BE « Runtimes Workers Multi-CLI » (Cline / glm-5.3-flash)

**Mission source** : `Projects/mLoop/memory/worker_mloop_109_be_mission.md`
**Type** : VALIDATION (lecture seule — aucune modification de code, aucun commit)
**Date d'exécution** : 2026-09-20
**Répertoire de travail** : `C:\Memory Loop`
**État testé (HEAD)** : `9248b11` (branche `main`) — arbre de travail **sale** (voir ANOMALIE A4)
**Interpréteur** : Python 3.11.15 (MSC v.1944 64-bit, Windows)

---

## VERDICT

**PASS_WITH_RESERVES**

Précision d'attribution (anti-sycophancy) : les **3 vérifications demandées sont 100 % PASS** et reproduisent exactement les sorties attendues par la mission (44/44 tests, 3/3 conformité AST, contrat de flags identique au caractère près). Les réserves **ne concernent aucune des 3 vérifications** : elles portent sur des écarts documentaires et sur une hypothèse E2E non testable par ces 3 commandes (route modèle LiteLLM) — détails en ANOMALIES.

| # | Vérification | Résultat |
| :- | :--- | :--- |
| 1 | Non-régression pytest (4 fichiers) | **PASS** — `44 passed in 3.30s` / `44 passed in 3.28s` (2 exécutions concordantes) |
| 2 | Conformité AST déterministe (3 fichiers) | **PASS** — 3/3 `[PASS]`, `0 violation(s)` |
| 3 | Contrat de flags par runtime | **PASS** — sorties identiques à l'attendu de la mission |

---

## EVIDENCE

### E0 — Reconnaissance (read-only, préalable)

Commande : `git -C "C:\Memory Loop" --no-pager log --oneline -6`
```
9248b11 fix(worker,herdr): court-circuit pane-run deterministe pour shims npm (echec Herdr asynchrone = worker fantome)
6ca81d0 fix(worker): resolution binaire npm dual-topologie (exe natif + shim .cmd) - debloque le spawn Cline reel
aba3d7a feat(worker,herdr): routage declaratif multi-runtimes via registre + borne daemon (ADR-0346/0369)
b2830bd feat(worker): registre SSOT multi-runtimes Herdr (ADR-0346) - Cline 3.x integre + OpenCode preserve, profil sonde (v2.33.0)
043e8ae refactor(utils,MLOOP-101-BE): packages lexicon/ + token_ledger/, 6 audits ADR-0369, fix sqlite L143, harnais perf 15 tests
bc9a5c6 feat-hooks-MLOOP-105-BE-garde-fou-pre-commit-deterministe
```

Commande : `git -C "C:\Memory Loop" --no-pager log --oneline -1 --format='%H %ci %s' <ref>`
```
b2830bd85cea1d6060d725c555089d201251d73a 2026-09-20 10:57:19 -0400 feat(worker): registre SSOT multi-runtimes Herdr (ADR-0346) - Cline 3.x integre + OpenCode preserve, profil sonde (v2.33.0)
aba3d7ae703d3d8e5f4000e9e73255e03345eff5 2026-09-20 10:57:31 -0400 feat(worker,herdr): routage declaratif multi-runtimes via registre + borne daemon (ADR-0346/0369)
9248b111255ebd696c5a6bed3a31c8b6b1c9d3d1 2026-09-20 11:02:27 -0400 fix(worker,herdr): court-circuit pane-run deterministe pour shims npm (echec Herdr asynchrone = worker fantome)
```
➔ Les deux commits cités par la mission existent bien et sont les ancêtres directs de HEAD.

Commande : `python -c "import sys; print(sys.version)"`
```
3.11.15 (main, May 10 2026, 19:31:25) [MSC v.1944 64 bit (AMD64)]
```

### E1 — Non-régression des tests (Vérification 1)

Commande exacte : `python -m pytest tests/test_worker_runtimes.py tests/test_cline_adapter.py tests/test_herdr_adapter.py tests/test_ast_checker.py -q`
```
............................................                             [100%]
44 passed in 3.30s
```

Re-exécution de contrôle (même commande, cache pytest désactivé pour ne rien écrire sur disque) :
```
............................................                             [100%]
44 passed in 3.28s
```

Décomposition par fichier (contrôle de l'arithmétique test-par-test) :
```
python -m pytest tests/test_worker_runtimes.py -q  ->  ..................  [100%]  18 passed in 0.07s
python -m pytest tests/test_cline_adapter.py   -q  ->  ......              [100%]   6 passed in 0.06s
python -m pytest tests/test_herdr_adapter.py   -q  ->  ...........         [100%]  11 passed in 3.17s
python -m pytest tests/test_ast_checker.py     -q  ->  .........           [100%]   9 passed in 0.06s
```
➔ 18 + 6 + 11 + 9 = **44** : aucune divergence, aucun `skip`/`xfail` masqué, zéro échec, zéro erreur.

### E2 — Conformité AST déterministe (Vérification 2)

`python src/swarm.py code-check --file src/core/worker_runtimes.py`
```
=== MEMORY LOOP - FRAMEWORK BACKEND CLI ===
(i) [PASS] src/core/worker_runtimes.py (144 lignes, 1.7ms)
  * [S1] Bilan code-check AST: 1/1 conformes | 0 violation(s)
```

`python src/swarm.py code-check --file src/core/cline_adapter.py`
```
=== MEMORY LOOP - FRAMEWORK BACKEND CLI ===
(i) [PASS] src/core/cline_adapter.py (53 lignes, 0.8ms)
  * [S1] Bilan code-check AST: 1/1 conformes | 0 violation(s)
```

`python src/swarm.py code-check --file src/core/agent_probe.py`
```
=== MEMORY LOOP - FRAMEWORK BACKEND CLI ===
(i) [PASS] src/core/agent_probe.py (287 lignes, 3.0ms)
  * [S1] Bilan code-check AST: 1/1 conformes | 0 violation(s)
```
➔ 3/3 conformes, 0 violation. Aucun code de sortie non nul, aucune commande en échec.

### E3 — Contrat de flags par runtime (Vérification 3)

Commande : `python -c "from src.core.worker_runtimes import WORKER_RUNTIMES as W; [print(k, '| one_shot=', v.one_shot_flags, '| model=', v.default_model) for k, v in sorted(W.items())]"`
```
cline | one_shot= [] | model= nmedia_cloud/glm-5.3-flash
omp | one_shot= ['--dangerously-skip-permissions'] | model= None
opencode | one_shot= ['--yolo'] | model= None
pi | one_shot= ['--dangerously-skip-permissions'] | model= None
```

Commande : `python -c "from src.core.worker_runtimes import get_worker_runtime as g; print(g('cline').build_flags(model=g('cline').default_model)); print(g('opencode').build_flags(model='nmedia_cloud/claude-opus-4.8'))"`
```
['--model', 'nmedia_cloud/glm-5.3-flash']
['--yolo', '--model', 'nmedia_cloud/claude-opus-4.8']
```

**Confrontation à l'attendu de la mission §2.3 :**
- Attendu `cline` → `['--model', 'nmedia_cloud/glm-5.3-flash']` ➔ **obtenu à l'identique** ✔
- Attendu `opencode` → `['--yolo', '--model', 'nmedia_cloud/claude-opus-4.8']` (sémantique historique préservée) ➔ **obtenu à l'identique** ✔
- `opencode.default_model = None` (sélection pilotée par `TASK_MODEL_MAP`) ➔ conforme à la doctrine « sémantique historique intangible » ✔
- `pi` / `omp` conservent `['--dangerously-skip-permissions']` ✔ ; `cline.one_shot_flags = []` (auto-approbation native Cline 3.x, aucun `--yolo`) ✔

### E4 — Preuves de câblage aval (contrôle du routage déclaratif, lecture seule)

- `src/core/cline_adapter.py` L39 : `return get_worker_runtime("cline").build_flags(model=model, extra_args=extra_args)` — façade déléguante, aucune duplication de flags (API publique `build_cline_flags` / `resolve_cline_binary` / `DEFAULT_CLINE_MODEL` conservée).
- `src/core/herdr_adapter.py` L745-746 : `if runtime_spec is not None and runtime_spec.default_model and not model:` ➔ `target_model = runtime_spec.default_model` — le défaut Cline prime sur `TASK_MODEL_MAP`, sauf `--model` explicite.
- `src/core/herdr_adapter.py` L769-770 : `flags = runtime_spec.build_flags(model=target_model, extra_args=extra_args)` ; les littéraux `--yolo` / `--dangerously-skip-permissions` ont disparu du chemin nominal (il n'en subsiste que dans des `else` de repli hérité, L771-774).
- `src/core/herdr_adapter.py` L312 + L358-371 : `_runtime_needs_pane_run(kind)` délègue à `needs_pane_run_fallback()` du registre — zéro branche conditionnelle par runtime dans l'adaptateur, conforme à la cible déclarative annoncée.
- Sonde réelle : `python src/swarm.py agent-probe`
```
Herdr PTY Orchestrato herdr       ● DISPONIBLE   0.8.0        PTY Worker Isolation (ADR-0346)
OpenCode              opencode    ● DISPONIBLE   1.18.30      Universal Code Generator (ADR-0375)
Claude Code           claude      ● DISPONIBLE   2.1.267      Deep Refactoring & Spike
Cline CLI             cline       ● DISPONIBLE   3.0.62       Build Worker Délégué (ADR-0346)
Aider                 aider       ○ INTROUVABLE  -            Pair Programming CLI
Cursor CLI            cursor      ○ INTROUVABLE  -            IDE Headless Agent
```
➔ Cline détecté en **3.0.62**, exactement la *ground truth* citée en en-tête de `cline_adapter.py`/`worker_runtimes.py` : l'entrée sonde de `agent_probe.py` (L86-94, `min_version="3.0.0"`, `critical_in_stages=("STAGE_BUILD",)`) est fonctionnelle et cohérente avec le registre.

---

## ANOMALIES

**A1 — Incohérence documentaire interne au CHANGELOG (mineure, non bloquante).**
`CHANGELOG.md` L13 affirme « `src/core/cline_adapter.py` : … (API publique conservée — **5 tests** au vert) », alors que l'exécution réelle donne **6 passed** (`tests/test_cline_adapter.py`). La L22 du même bloc annonce « 17 tests d'intégration Cline/Herdr » = 6 + 11 (vérifié, cohérent) ; la L13 est la seule désynchronisée (5 + 11 = 16 ≠ 17). Écart de rédaction, **aucun impact code**.

**A2 — `--kind agy` annoncé mais absent du registre (pré-existant, révélé par le routage déclaratif).**
L'aide CLI (`python src/swarm.py worker-spawn --help`) affiche `--kind KIND   Type d'agent (opencode, cline, pi, omp, agy)` (`src/commands/_registry.py` L1444). Or `agy` n'est pas une entrée de `WORKER_RUNTIMES` :
```
python -c "from src.core.worker_runtimes import get_worker_runtime as g; print(g('agy'))"
[Command exited with code 1]
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "C:\Memory Loop\src\core\worker_runtimes.py", line 140, in get_worker_runtime
    raise KeyError(
KeyError: "Runtime worker inconnu : 'agy'. Runtimes enregistrés : ['cline', 'omp', 'opencode', 'pi']"
```
**Attribution vérifiée** : l'anomalie est **antérieure à ce chantier** — la chaîne était déjà présente avant `b2830bd` :
`git --no-pager show 043e8ae:src/commands/_registry.py | Select-String "agy"` ➔ `"help": "Type d'agent (opencode, pi, omp, agy)"`.
Conséquence actuelle : `--kind agy` ne produit pas d'erreur utilisateur explicite ; `herdr_adapter` capture le `KeyError` (L738-744), applique le repli hérité (`--dangerously-skip-permissions`) et tente le binaire brut `agy`. **Pas de régression**, mais drift CLI/registre désormais structurel (l'aide CLI est un argument déclaratif du SSOT — ADR-0370).

**A3 — Périmètre de traçabilité de la mission incomplet.**
La mission §1 énonce « **Deux** commits locaux portent ce chantier ». En réalité le chantier s'étale sur **4 commits** : `b2830bd` ➔ `aba3d7a` ➔ `6ca81d0` (résolution binaire npm dual-topologie) ➔ `9248b11` (court-circuit `pane run` déterministe). L'état effectivement testé est **HEAD = `9248b11`**, pas `aba3d7a`. Écart de cadrage, non bloquant : les 44 tests couvrent le comportement de HEAD, y compris `needs_pane_run_fallback`.

**A4 — Arbre de travail sale pendant la validation (réserve de reproductibilité).**
`git status --porcelain` (22 entrées) :
```
 M src/bridges/mcp_loop_mem.py
 M src/pipelines/grill_engine.py
 M src/pipelines/jira/md_cleaner.py
 M src/pipelines/resilience/__init__.py
 M src/pipelines/wikifix.py
 M src/pipelines/wikifix_auditors.py
 M src/pipelines/wikifix_core.py
 M standards/blueprints/git_pre_commit_hook.sh
?? src/bridges/mcp_resources.py
?? src/bridges/mcp_tools.py
?? src/converters/markitdown_converter.py
?? src/loop_mem/hybrid_search.py
?? src/pipelines/jira/adf_inline.py
?? src/pipelines/okf_compiler.py
?? tests/test_hybrid_search.py
?? tests/test_markitdown_pipeline.py
?? tests/test_mcp_loop_mem.py
?? tests/test_okf_compiler.py
?? tests/test_story_guard.py
?? tests/test_wayfinder.py
?? tests/test_wikifix.py
?? vibe_err.txt
```
**Aucun** de ces fichiers n'appartient au périmètre testé : `src/core/worker_runtimes.py`, `src/core/cline_adapter.py`, `src/core/herdr_adapter.py`, `src/core/agent_probe.py`, `tests/test_worker_runtimes.py`, `tests/test_cline_adapter.py`, `tests/test_herdr_adapter.py`, `tests/test_ast_checker.py` sont tous **absents** de cette liste (donc non modifiés). Les résultats E1-E3 sont attribuables à HEAD, mais ne constituent pas une preuve sur un arbre propre reproductible à l'identique.

**A5 — Hypothèse E2E non couverte par les 3 vérifications : existence de la route modèle LiteLLM.**
La Vérification 3 prouve la **construction des flags**, pas la **résolution du modèle par le proxy**. Le code porte lui-même cet aveu (`src/core/worker_runtimes.py` L30-33) : « *Identifiant demandé explicitement par l'humain ; à confirmer à l'E2E (proxy injoignable 429 lors de l'audit : `GET /v1/models` en échec temporaire).* » Cet écart n'invalide pas la Vérification 3 (attendu de la mission satisfait au caractère près) : c'est une **frontière active** explicitement admise — le proxy n'a **pas** été sondé, la mission bornant strictement les vérifications à 3.

**Synthèse** : aucune anomalie bloquante ; aucune violation AST, aucun test rouge, aucun écart sur le contrat de flags.

---

## RECOMMANDATIONS

**R1 — Aligner le CHANGELOG (réf. A1).** Corriger `CHANGELOG.md` L13 : « 5 tests au vert » ➔ « 6 tests au vert », pour cohérence avec la L22 (17 = 6 + 11). Correction purement documentaire.

**R2 — Trancher le sort de `agy` (réf. A2).** Deux options exclusives :
1. *Soit* ajouter une entrée `WorkerRuntimeSpec(kind="agy", …)` dans `WORKER_RUNTIMES` avec ses flags/binaire réels ;
2. *Soit* retirer `agy` de l'aide `--kind` (`src/commands/_registry.py` L1444) — au mieux en dérivant la chaîne de `sorted(WORKER_RUNTIMES)` pour rendre le drift impossible par construction.
Dans les deux cas, exécuter impérativement `python src/swarm.py guide --sync` immédiatement après (ADR-0370 Zero-CLI-Drift), puis rejouer les 3 vérifications de cette mission. Recommandation complémentaire : faire échouer explicitement un `--kind` inconnu (fail-fast) plutôt que de retomber silencieusement sur le repli hérité.

**R3 — Valider la route `nmedia_cloud/glm-5.3-flash` (réf. A5).** Lors du prochain spawn réel `worker-spawn --story <ID> --kind cline`, confirmer que le proxy LiteLLM accepte l'identifiant (`GET /v1/models`) **avant** de considérer le chantier clos en E2E. Si la route est absente, le worker Cline échouera au runtime sur un modèle inconnu malgré des flags corrects. Lever ensuite la note d'incertitude de `worker_runtimes.py` L30-33.

**R4 — Rejouer la validation sur arbre propre (réf. A4).** Committer (ou écarter via `git stash`) les 7 fichiers modifiés et les 9 fichiers non suivis avant l'E2E, afin que le verdict porte sur un état commité exact et reproductible.

**R5 — Compléter la traçabilité du chantier MLOOP-109 (réf. A3).** Mettre à jour le contexte du récit/dette MLOOP-109-BE pour référencer les **4** commits (`b2830bd`, `aba3d7a`, `6ca81d0`, `9248b11`) et préciser que la validation a porté sur HEAD = `9248b11`.

**R6 — Sidecar de statut non produit (contrainte respectée).** Conformément à « Livrable unique », aucun fichier `worker_MLOOP-109-BE.status` n'a été écrit. L'orchestrateur doit le générer au harvest, selon la convention observée sur `Projects/mLoop/memory/worker_MLOOP-101-BE.status` (`STATUS` / `STORY_ID` / `COMPLETED_AT` / `AGENT` / `SUMMARY` / `GATES`).

**R7 — Sanctuariser le socle de non-régression.** Les 44 tests et les 3 `code-check` constituent un socle vert à intégrer comme commande de garde du chantier multi-CLI avant toute extension du registre (nouveau CLI = simple entrée `WorkerRuntimeSpec`, conformément à la cible « zéro branche par runtime »).

---

**Contraintes de mission** : mission exécutée en **lecture seule** — aucune création/modification/suppression dans `src/`, `tests/`, `standards/` ; **aucun** `git add`/`commit`/`push` ; aucun fait rapporté qui ne provienne d'une commande réellement exécutée ci-dessus.

STATUS: COMPLETED
