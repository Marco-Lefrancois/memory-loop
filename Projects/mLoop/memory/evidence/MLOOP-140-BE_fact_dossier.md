# Dossier de Preuves Documentaires — MLOOP-140-BE

> Instrumentation Logging Point d'Entrée CLI (`swarm.py`, `router.py`, `cli.py`)
> Phase : BUILD | Ancrage épistémique ADR-0361 / ADR-0369

---

## 1. Sources SSOT & Notes d'Atelier

- Récit cible : [MLOOP-140-BE.md (Lignes 1-62)](file:///c:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-140-BE.md)
- Moteur logging existant (MLOOP-110-BE) : [logger.py (Lignes 1-195)](file:///c:/Memory%20Loop/src/utils/logger.py)
- Tests de référence logging : [test_logger_rotating.py (Lignes 1-204)](file:///c:/Memory%20Loop/tests/test_logger_rotating.py)

---

## 2. Matrice de résolution des conflits (Spec vs Code Réel)

| # | Affirmation de la Spec | Fait établi (Code Réel) | Résolution retenue |
|---|---|---|---|
| C1 | « `cli.py` : Étendre `get_logger("cli")` **existant** » | `cli.py` n'a **aucun** `get_logger` ; il utilise `rich.Console` uniquement | **CRÉATION** du logger `cli` + adapter `LoggingConsole` (pas d'extension d'un existant inexistant) |
| C2 | « `main()` doit tracer durée + exit_code » | `main()` (swarm.py L154-160) délègue à `execute_cli()` qui appelle `sys.exit()` en interne | Le tracing durée/exit_code s'ancre dans `execute_cli()` (router.py) qui possède l'exit_code ; `main()` capture l'exception résiduelle |
| C3 | « Toute exception non gérée écrit dans errors.log » | `safe_run_entrypoint` (safe_exec.py L33-48) **avale toutes les exceptions** et force `sys.exit(0)` | Injection de `logger.error(exc_info=True)` **dans** `safe_run_entrypoint` AVANT la conversion en exit 0, sinon errors.log resterait vide |

---

## 3. Extraits verbatim sourcés

**Extrait 1 — Moteur logging (get_logger) (Lignes 147-193) :**
« `def get_logger(name: str = "mloop", **context_kwargs) -> logging.Logger:` [...] `if context_kwargs: return MLoopLoggerAdapter(logger, context_kwargs)` »
➔ Fait établi : `get_logger` accepte des kwargs contextuels et retourne un `MLoopLoggerAdapter` fusionnant `extra`. Pattern à réutiliser tel quel.

**Extrait 2 — Handlers rotatifs (Lignes 105, 134) :**
« `error_log_path = log_dir / "errors.log"` » et « `info_log_path = log_dir / "mloop.log"` »
➔ Fait établi : `errors.log` (niveau ERROR) et `mloop.log` (niveau INFO) sont les cibles physiques déjà configurées. Aucune création de handler à refaire.

**Extrait 3 — main() actuel (swarm.py Lignes 154-160) :**
« `def main(): from src.commands.router import execute_cli; try: execute_cli() except KeyboardInterrupt: ZeroFluffConsole.error(...); sys.exit(130)` »
➔ Fait établi : `main()` ne capture QUE `KeyboardInterrupt`. Aucune capture d'exception générique ➔ point d'injection `logger.error`.

**Extrait 4 — execute_cli() dispatch (router.py Lignes 64-105) :**
« `def execute_cli() -> None: [...] exit_code = handler(args, state, project_path); sys.exit(exit_code or 0)` »
➔ Fait établi : `execute_cli()` détient la commande, le projet et l'exit_code final ➔ point d'ancrage du tracing INFO complet (commande, projet, durée, exit_code) et de la capture d'erreur ERROR.

**Extrait 5 — safe_run_entrypoint absorption (safe_exec.py Lignes 33-48) :**
« `except Exception as e: [...] print(...); sys.exit(0)` »
➔ Fait établi : le garde d'exécution avale silencieusement toute exception (sans log fichier) ➔ instrumentation `logger.error(exc_info=True)` obligatoire ici pour respecter le critère « toute exception non gérée écrit dans errors.log ».

**Extrait 6 — ZeroFluffConsole.error (cli.py Lignes 49-51) :**
« `@staticmethod def error(msg: str) -> None: console.print(...)` »
➔ Fait établi : les erreurs affichées à l'utilisateur transitent par `ZeroFluffConsole.error` sans persistance. Un wrapper `LoggingConsole.error` doit doubler l'affichage d'un `logger.error`.

---

## 4. Contrats déclaratifs cibles

- **Contexte `extra` normalisé** : `{ "command": str, "project": str, "phase": str, "story_id": str|None, "exit_code": int (final) }`
- **Convention de niveaux** :
  - `mloop.log` (INFO) : début d'exécution (commande, projet), fin d'exécution (exit_code, durée_ms).
  - `errors.log` (ERROR) : exceptions non gérées avec `exc_info=True`.
  - `KeyboardInterrupt` : WARNING (interruption utilisateur, non-erreur).
  - `exit_code != 0` : ERROR ; `exit_code == 0` : INFO.

---

## 5. Frontière active & Admission of Limits

- **In-scope** : `swarm.py`, `router.py`, `cli.py`, `safe_exec.py` (nécessaire au critère errors.log), tests.
- **Out-of-scope** : handlers CLI unitaires (MLOOP-142-BE), pipelines internes (MLOOP-141/143-BE).
- **Limite assumée** : le tracing INFO de `mloop.log` n'est visible que si `MLOOP_LOG_LEVEL=INFO` (défaut runtime = WARNING). Documenté comme comportement attendu, contrôlable par variable d'environnement.
