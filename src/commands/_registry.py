"""
Shim de ré-export — rétrocompatibilité ADR-0202 (MLOOP-175-BE).

Ce fichier est maintenu pour la rétrocompatibilité.
Les symboles sont définis dans le package src/commands/_registry/.

NOTE : En Python, le package _registry/ prend la priorité sur ce fichier .py.
Ce shim documente l'intention architecturale et sert de repère pour les outils
d'analyse statique qui pourraient lister les deux artefacts.

Callers préservés sans modification :
  - src/commands/router.py     : from src.commands._registry import COMMANDS
  - src/pipelines/calibrate.py : from src.commands._registry import COMMANDS
  - src/pipelines/guide_generator.py : from src.commands._registry import COMMANDS
"""

# Le package src/commands/_registry/__init__.py prend automatiquement la priorité
# sur ce fichier .py (comportement standard Python — PEP 328).
# Les imports ci-dessous ne sont jamais exécutés mais documentent la surface publique.
from src.commands._registry import COMMANDS, WORKER_KIND_HELP  # noqa: F401
