"""
src.cli.click_engine — Moteur d'exécution CLI Click de mLoop (EPIC-19).

Modernisation du moteur d'exécution CLI mLoop d'argparse vers Click
(lazy-loading, contexte unifié, completion shell, aide par phases,
harnais CliRunner) sans régression sur les 121 commandes du registre,
via flag ``MLOOP_CLI_ENGINE`` (défaut ``argparse`` — A3).

Stories EPIC-19 :
  - MLOOP-190-BE : ``context.py`` — MLoopContext, @pass_mloop_context,
    lifecycle_gate_guard (Quality Gate Enforcement — ADR-0339).
  - MLOOP-191-BE : ``router.py`` — MLoopMultiCommand, ArgsShim, cli.
  - MLOOP-192-BE : ``completion.py`` — compléteurs shell dynamiques.
  - MLOOP-193-BE : ``formatter.py`` — PhaseHelpFormatter (--help par phases).
  - MLOOP-194-BE : harnais de tests CliRunner in-process.

Ce package est inert tant que ``MLOOP_CLI_ENGINE != "click"`` : le chemin
legacy ``src/commands/router.py`` (argparse) reste intact (rollback A3/OQ-01).
"""

__all__: list = []
