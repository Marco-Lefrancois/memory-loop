"""Point d'entrée du moteur CLI Click (MLOOP-191-BE / EPIC-19-CLICK-CLI-ENGINE).

Extraction du branch Click de ``src/swarm.py:main()`` pour respecter RULE-AST-01
(ADR-0202 : modules ≤ 300 lignes) sans altérer le contrat d'entrée :
- mêmes codes de sortie (Abort/KI → 130, ClickException → exc.exit_code,
  SystemExit propagé, entier retourné → exit 0),
- mêmes journaux structurés (duration_ms + exit_code en ``finally``),
- rollback argparse intégral via ``MLOOP_CLI_ENGINE`` (A3/OQ-01, défaut argparse),
- stdout protégé pendant la complétion shell (MLOOP-192-BE, garde ``_LOOP_COMPLETE``).
"""

import os
import sys
import time

from click.exceptions import Abort, ClickException

from src.cli import ZeroFluffConsole
from src.cli.click_engine.router import cli
from src.utils.logger import get_logger

logger = get_logger("cli")


def run_click_cli() -> None:
    """Exécute la branche Click de l'entrée CLI puis termine le processus.

    Ne retourne jamais : ``sys.exit(...)`` est appelé sur tous les chemins
    (l'exception ``SystemExit`` des gates/handlers est propagée telle quelle).
    """
    # MLOOP-192-BE : stdout strictement réservé au protocole de complétion Click
    # (triplets type/valeur/aide parsés par les scripts shell) — sans ce garde,
    # le banner est consommé comme candidat et désaligne la boucle PowerShell (i += 3).
    if not os.environ.get("_LOOP_COMPLETE"):
        ZeroFluffConsole.section("Memory Loop - Framework Backend CLI")
    command = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    project = os.environ.get("MLOOP_ACTIVE_PROJECT")
    start_time = time.perf_counter()
    exit_code = 0
    try:
        logger.info(
            "Démarrage de l'exécution CLI.",
            extra={"command": command, "project": project, "phase": "run", "story_id": None},
        )
        rv = cli.main(sys.argv[1:], standalone_mode=False)
        exit_code = rv if isinstance(rv, int) else 0
    except Abort:
        exit_code = 130
        logger.warning(
            "Exécution CLI interrompue par l'utilisateur (Abort).",
            extra={"command": command, "project": project, "phase": "run", "exit_code": 130},
        )
        ZeroFluffConsole.error("\nExécution interrompue par l'utilisateur.")
        sys.exit(130)
    except KeyboardInterrupt:
        exit_code = 130
        logger.warning(
            "Exécution CLI interrompue par l'utilisateur (KeyboardInterrupt).",
            extra={"command": command, "project": project, "phase": "run", "exit_code": 130},
        )
        ZeroFluffConsole.error("\nExécution interrompue par l'utilisateur.")
        sys.exit(130)
    except ClickException as exc:
        # UsageError (exit 2, did-you-mean) et ClickException (exit 1) — édition stderr.
        exit_code = exc.exit_code
        logger.error(
            "Erreur Click durant l'exécution CLI.",
            extra={
                "command": command,
                "project": os.environ.get("MLOOP_ACTIVE_PROJECT", project),
                "phase": "run",
                "reason": str(exc),
                "exit_code": exit_code,
            },
        )
        exc.show()
        sys.exit(exit_code)
    except SystemExit as se:
        # Gates / handlers : propager le code réel (parité execute_cli).
        exit_code = se.code if isinstance(se.code, int) else (0 if se.code is None else 1)
        raise
    except Exception:
        exit_code = 1
        logger.error(
            "Exception non gérée remontée au point d'entrée CLI main().",
            extra={
                "command": command,
                "project": os.environ.get("MLOOP_ACTIVE_PROJECT", project),
                "phase": "run",
                "story_id": None,
                "exit_code": 1,
            },
            exc_info=True,
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log_level = logger.info if exit_code == 0 else logger.error
        log_level(
            "Fin de l'exécution CLI.",
            extra={
                "command": command,
                "project": os.environ.get("MLOOP_ACTIVE_PROJECT", project),
                "phase": "run",
                "duration_ms": duration_ms,
                "exit_code": exit_code,
            },
        )
    sys.exit(exit_code)
