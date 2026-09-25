---
created: 2026-09-21T20:53:29.296Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, mloop-142-be]
---

[[Plannotator Plans]]

# Plan d'Implémentation — MLOOP-142-BE [BUILD]
## Instrumentation Logging des 5 Handlers CLI Principaux (ADR-0369 / ADR-0376)

---

## 0. Contexte Vérifié (Faits établis, pas d'hypothèse)

- **Récit source** : `status: IN_DEV`, `grill_me: DONE`, `invest_score: 6/6`, `blocked_by: MLOOP-140-BE`.
- **Prérequis MLOOP-140-BE** : `LoggingConsole` **existe et est `DONE_TESTED`** dans `src/cli.py` (L117-170). Signature confirmée :
  `LoggingConsole.error(msg, command=None, project=None, phase=None, exc_info=False, **extra)` → double l'affichage `ZeroFluffConsole.error(msg)` + `logger.error(msg, extra={command,project,phase,**extra}, exc_info=exc_info)`.
- **Sink `errors.log`** : `src/utils/logger.py` `_setup_rotating_error_handler` → `RotatingFileHandler(errors.log, level=ERROR)`. Tout `logger.error(..., exc_info=True)` y est capté. `MLoopFormatter` sérialise `extra={...}` en `clé=valeur`.
- **Chiffres RÉELS confirmés par comptage AST** (décision Grill-Me « coder sur le réel ») :

| Fichier | ZFC.error | except Exception | except: nus |
|---|---|---|---|
| code_intelligence.py | 16 | 6 (L69,172,210,244,270,287) | 0 |
| build_harness.py | 12 | 2 (L141,227) | 0 |
| analysis_audit.py | 9 | 1 (L150) | 0 |
| tooling.py | 9 | 0 | 0 |
| export_story.py | 6 | 5 (L123,160,184,287,296) | 0 |
| **TOTAL** | **52** | **14** | **0** |

- **Nuance ADR-0369 (à signaler, anti-sycophancy)** : la mission mentionne « corriger `except:` nus ». **Il n'y en a AUCUN** dans ces 5 fichiers (0 occurrence réelle). En revanche il existe **6 `except Exception:` SANS binding ni logging** (silence nu = violation Zero-Silent-Pass) : `code_intelligence.py:L69`, `export_story.py:L123,L160,L184,L287,L296`. Ce sont EUX la vraie cible de la correction ADR-0369. Je les traiterai (binding `as e` + `logger.debug(..., exc_info=True, extra=...)` car ils sont non-bloquants par conception).

---

## 1. Stratégie de Refactoring (déterministe, iso-comportement console)

### Règle A — Import
Dans chaque handler : `from src.cli import ZeroFluffConsole` → `from src.cli import ZeroFluffConsole, LoggingConsole`.
(`ZeroFluffConsole` reste importé : `.info/.success/.warning/.step_s1/.step_s2/.section` restent inchangés — hors périmètre du récit qui cible UNIQUEMENT `.error` + `except`.)

### Règle B — Remplacement des 52 `ZeroFluffConsole.error(msg)` → `LoggingConsole.error(msg, command=..., project=..., ...)`
- **Affichage console strictement identique** (LoggingConsole appelle ZeroFluffConsole.error en interne).
- Contexte `extra` standardisé, rempli avec les valeurs RÉELLES disponibles dans chaque handler (jamais inventées) parmi : `command`, `project`, `story_id`, `target_keys`, `dry_run`, `apply_mode`, `subcommand`, `phase`.
- `command` = nom canonique de la sous-commande (ex: `code-explore`, `graph-query`, `tdd-enforce`, `code-tournament`, `code-check`, `rubber-duck`, `struct-check`, `jira_sync`, `archify`, `csv-validate`...).
- `project` = `getattr(args,'project',None)` ou `state.project_name` selon disponibilité réelle dans le handler.
- `exc_info=True` UNIQUEMENT sur les `.error` situés dans un bloc `except` (une exception vive existe) ; `exc_info` omis (défaut False) sur les `.error` de validation d'arguments (pas d'exception).

### Règle C — Instrumentation des 14 `except Exception` (Zero-Silent-Pass ADR-0369)
- **8 blocs `except Exception as e:` déjà bindés** qui appellent `ZFC.error(f"...: {e}")` : le `.error` devient `LoggingConsole.error(..., exc_info=True, ...)` → la trace part dans errors.log. (code_intelligence L172/210/244/270/287 ; build_harness L141/227 ; analysis_audit L150).
- **6 blocs `except Exception:` NUS silencieux** (non-bloquants par design) → passer à `except Exception as e:` + ajouter `logger.debug("<contexte non-bloquant>", exc_info=True, extra={...})` SANS changer le flux de contrôle (garde le `pass`/`continue`/fallback existant). Fichiers : code_intelligence.py:L69 (résolution projet actif), export_story.py:L123 (init client httpx Jira), L160 (probe statut Jira), L184 (close client), L287 (manifeste corrompu), L296 (écriture manifeste).
  - Import requis dans ces 2 fichiers : `from src.utils.logger import get_logger` + `logger = get_logger("<name>")` au niveau module.

### Règle D — Aucune modification hors périmètre
- Zéro changement de logique métier, de valeur de retour, ou de signature de handler.
- Zéro `# TODO`/troncature (Full-Output Enforcement).

---

## 2. Fichiers modifiés (7 couches ADR-0376)

### Couche 6 — Core Python & CLI (les 5 handlers) — `[MODIFY]`
1. `src/commands/handlers/code_intelligence.py` — 16 ZFC.error→LoggingConsole.error ; L69 except nu→instrumenté ; 5 except bindés→exc_info=True. `command` dérivé par handler (code-init/explore/impact/affected/status).
2. `src/commands/handlers/build_harness.py` — 12 ZFC.error→LoggingConsole.error ; L141/L227 except→exc_info=True. `command`=code-check/code-tournament/tdd-enforce ; extra `story_id`, `phase` (red/green/verify).
3. `src/commands/handlers/analysis_audit.py` — 9 ZFC.error→LoggingConsole.error ; L150 except (ttl_err) déjà bindé→exc_info=True. `command`=struct-check/rubber-duck/eval-harvest/dossier-init ; `project`=args.project.
4. `src/commands/handlers/tooling.py` — 9 ZFC.error→LoggingConsole.error ; 0 except. `command`=archify/csv-validate/csv-normalize/csv-anonymize/csv-diff.
5. `src/commands/handlers/export_story.py` — 6 ZFC.error→LoggingConsole.error ; 5 except nus→instrumentés (logger.debug non-bloquant). `command`=jira_sync ; extra `target_keys`, `dry_run`, `apply_mode`, `project`=state.project_name.

### Couche 7 — Tests & Parité — `[NEW]`
6. `tests/test_handlers_logging_mloop_142.py` — suite calquée sur `tests/test_cli_logging.py` (fixture `fresh_*_logger` + injection d'erreurs simulées). Couvre :
   - Chaque handler : patch `LoggingConsole.error` → assert appelé avec `command`/`project`/`extra` corrects sur chemin d'erreur (args manquants + exception injectée).
   - Contrat errors.log : exception injectée dans un handler (via mock d'un moteur levant une exception) → trace + `exc_info` présents.
   - Zero-Silent-Pass : les 6 ex-`except` nus loggent en DEBUG avec `exc_info=True` sans casser le flux (fallback préservé).

### Couche 1-5 — Blueprints/Protocoles/ADR/Directives/Skills
- **Aucun impact** : le récit consomme une brique existante (LoggingConsole), n'introduit ni gabarit, ni protocole, ni ADR, ni skill. Le pattern d'instrumentation est déjà normé par ADR-0369 et livré par MLOOP-140-BE. Aucune commande CLI ajoutée → pas de `guide --sync` requis (registre `_registry.py` intouché).

---

## 3. Vérification (verification_harness)

1. `python -m pytest tests/test_handlers_logging_mloop_142.py -v` → 100% vert.
2. `python -m pytest tests/test_cli_logging.py tests/test_logger_rotating.py -q` → non-régression MLOOP-140.
3. `python src/swarm.py code-check --file src/commands/handlers/code_intelligence.py` (×5 fichiers) → 0 violation RULE-AST + conformité ADR-0369 (Zero-Silent-Pass levé).
4. Test manuel d'intégration errors.log : provoquer une erreur réelle (`code-explore` sans `--query`) → vérifier ligne `command=code-explore ... project=...` dans `memory/logs/errors.log`.
5. `python src/swarm.py vibe-check --project mLoop` → 20/20 (contrôle ADR-0369 maintenu PASS).

---

## 4. Hors périmètre (respecté)
- Handlers secondaires (MLOOP-145-BE), point d'entrée CLI (MLOOP-140-BE, déjà fait), pipelines cœur (MLOOP-141-BE), pipeline Jira interne `sync_engine` (MLOOP-144-BE déjà fait — je n'instrumente QUE le handler `export_story.py`, pas le moteur `jira/sync_engine.py`).
- Transition d'état / promotion `DONE_TESTED` : hors mission BUILD (relève de la QA + approbation humaine).

---

## 5. Confirmation demandée
Validez ce plan pour que je procède à l'implémentation des 5 handlers + la suite de tests, puis à l'exécution du verification_harness.