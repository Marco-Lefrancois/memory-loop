# -*- coding: utf-8 -*-
"""
rules_mirror.py - Générateur de Parité .clinerules pour Cline.

Conforme à ADR-0202 (<=300L), ADR-0376 (Rigueur 360°) et EPIC-26 (MLOOP-261-BE).
Projette de façon déterministe les garde-fous constitutionnels de mLoop dans
le fichier `.clinerules/mloop.md` afin que tout agent Cline opérant sur le projet
respecte nos invariants sans dérive comportementale.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mloop.bridges.cline.rules_mirror")

CLINERULES_DIR_NAME = ".clinerules"
MLOOP_RULES_FILE_NAME = "mloop.md"


class ClineRulesMirror:
    """Générateur de règles .clinerules/mloop.md depuis les invariants mLoop."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.root = workspace_root or Path.cwd()
        self.rules_dir = self.root / CLINERULES_DIR_NAME
        self.target_file = self.rules_dir / MLOOP_RULES_FILE_NAME

    def ensure_rules_dir(self) -> Path:
        """Assure l'existence du dossier .clinerules/."""
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        return self.rules_dir

    def build_rules_content(self) -> str:
        """Assemble les directives constitutionnelles mLoop pour Cline."""
        return (
            "# 🛡️ Directives Constitutionnelles mLoop pour Cline\n\n"
            "> Ce fichier est généré automatiquement par `mloop sync`. Ne pas modifier manuellement.\n"
            "> Réf : ADR-0376 (Rigueur 360° Zéro Blindspot) · ADR-0202 (Plafond 300L) · ADR-0375 (5 Phases).\n\n"
            "## 1. Interdiction Absolue de Saut de Phase (ADR-0339 / ADR-0375)\n"
            "- En **Phase 2 (PLAN & ANALYSE)**, l'agent doit impérativement opérer en mode `--plan`.\n"
            "- Il est **strictement interdit** d'écrire ou de modifier du code source avant que la story "
            "ne soit validée au statut `READY_FOR_DEV` (Grill-Me 1:1 complété, DoR 6/6).\n\n"
            "## 2. Plafond Modulaire Strict <= 300 Lignes (ADR-0202)\n"
            "- Aucun fichier source Python (`src/`, `tests/`) ne doit excéder **300 lignes effectives**.\n"
            "- Tout composant qui dépasse cette limite doit être immédiatement découpé en sous-modules "
            "hautement cohésifs avec délégation explicite.\n\n"
            "## 3. Préservation Intangible du Code & Zéro Régression\n"
            "- Il est **formellement interdit de supprimer du code ou des tests existants** sous prétexte "
            "de simplification sans justification explicite et approbation.\n"
            "- Conserver systématiquement les docstrings, annotations de types et gestion d'erreurs.\n\n"
            "## 4. Rigueur d'Audit en 7 Couches (ADR-0376)\n"
            "Toute évolution touchant le cœur de mLoop doit inspecter et maintenir la cohérence de :\n"
            "1. Blueprints (`standards/blueprints/`)\n"
            "2. Protocoles (`standards/protocols/`)\n"
            "3. ADR System (`standards/adr-system/`)\n"
            "4. Directives Agents (`.agents/agents/`)\n"
            "5. Skills Portables (`.agents/skills/`)\n"
            "6. Moteur Core Python (`src/core/`, `src/bridges/`, `src/commands/`)\n"
            "7. Suites de Tests & Guides CLI (`tests/`, `CLI_PIPELINE_GUIDE.md`)\n\n"
            "## 5. Commandes de Validation Déterministes\n"
            "Après toute modification, exécuter impérativement :\n"
            "```powershell\n"
            "pytest tests/ -v\n"
            "python src/swarm.py vibe-check --project mLoop\n"
            "```\n"
        )

    def sync(self) -> Path:
        """Écrit le fichier .clinerules/mloop.md de façon idempotente."""
        self.ensure_rules_dir()
        content = self.build_rules_content().strip() + "\n"
        if self.target_file.exists():
            existing = self.target_file.read_text(encoding="utf-8")
            if existing == content:
                logger.debug("[ClineRules] .clinerules/mloop.md inchangé (idempotent).")
                return self.target_file
        self.target_file.write_text(content, encoding="utf-8")
        logger.info("[ClineRules] .clinerules/mloop.md synchronisé avec succès.")
        return self.target_file
