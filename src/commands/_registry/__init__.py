"""
Package agrégateur du registre déclaratif CLI mLoop (MLOOP-175-BE).

Agrège les 8 sous-registres par domaine en un dictionnaire `COMMANDS` unique
exposé comme point d'entrée stable du dispatcher.

Ordre de chargement (dernier gagne pour les doublons — comportement dict Python) :
  1. _reg_project        : guide, init, resume, focus, vibe-check...
  2. _reg_analysis_core  : sync, wikifix, dream[analysis], code-check...
  3. _reg_analysis_ext   : story-clean[1+2], rubber-duck, extract...
  4. _reg_pipelines_arch : ingest, dream[pipeline→gagne], crawl, grill...
  5. _reg_validate_tool  : aoep, calibrate, dashboard, drawdb[1+2→gagne], csv-*...
  6. _reg_export_skill   : jira_sync, skill-list, doctor, agent-probe...
  7. _reg_intelligence   : code-init→code-status, graph-*, gates, tree...
  8. _reg_workers        : worker-spawn→worker-janitor-watch...
  9. _reg_runtime_ops    : app-server, mcp-serve, cache-*, fact-*, review, resilience, dream-rsi...

Doublons résolus par ordre :
  - dream       : pipeline:handle_dream  (étape 4 gagne sur étape 2)
  - story-clean : handle_story_clean avec --verbose (étape 3 second = gagne)
  - drawdb      : sans --action / avec --no-open (étape 5 second = gagne)

Callers stables (zéro modification requise) :
  - src/commands/router.py L17 : from src.commands._registry import COMMANDS
  - src/commands/router.py L68 : import src.commands._registry as reg_mod
  - src/pipelines/calibrate.py L123 : from src.commands._registry import COMMANDS
  - src/pipelines/guide_generator.py L9 : from src.commands._registry import COMMANDS

ADR-0202 : chaque _reg_*.py ≤ 300L / 15Ko.
ADR-0370 : guide --sync exécuté après toute modification.
"""

from src.commands._registry._reg_project import PROJECT_COMMANDS
from src.commands._registry._reg_analysis_core import ANALYSIS_CORE_COMMANDS
from src.commands._registry._reg_analysis_ext import ANALYSIS_EXT_COMMANDS
from src.commands._registry._reg_pipelines_arch import PIPELINES_ARCH_COMMANDS
from src.commands._registry._reg_validate_tool import VALIDATE_TOOL_COMMANDS
from src.commands._registry._reg_export_skill import EXPORT_SKILL_COMMANDS
from src.commands._registry._reg_intelligence import INTELLIGENCE_COMMANDS
from src.commands._registry._reg_workers import WORKERS_COMMANDS, WORKER_KIND_HELP
from src.commands._registry._reg_runtime_ops import RUNTIME_OPS_COMMANDS
from src.commands._registry._reg_tooling_ecosystem import TOOLING_ECOSYSTEM_COMMANDS
from src.commands._registry._reg_data_hygiene import DATA_HYGIENE_COMMANDS

# Point d'entrée stable du dispatcher — nom COMMANDS conservé (Q2 grill, zéro rename).
# Fusion ordonnée : les doublons sont résolus par le dernier assigné (comportement dict Python).
COMMANDS: dict[str, dict] = {
    **PROJECT_COMMANDS,
    **ANALYSIS_CORE_COMMANDS,
    **ANALYSIS_EXT_COMMANDS,
    **PIPELINES_ARCH_COMMANDS,
    **VALIDATE_TOOL_COMMANDS,
    **EXPORT_SKILL_COMMANDS,
    **INTELLIGENCE_COMMANDS,
    **WORKERS_COMMANDS,
    **RUNTIME_OPS_COMMANDS,
    **TOOLING_ECOSYSTEM_COMMANDS,
    **DATA_HYGIENE_COMMANDS,
}

__all__ = ["COMMANDS", "WORKER_KIND_HELP"]
