"""
Blueprint Loader Engine (mLoop SSOT)
Gouvernance : ADR-0319 / ADR-0330 / ADR-0369

Charge et instancie les gabarits déclaratifs sous standards/blueprints/
sans AUCUN gabarit de fichier hardcodé dans le code Python source.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logger import get_logger

logger = get_logger("blueprints")


class BlueprintNotFoundError(FileNotFoundError):
    """Exception levée lorsqu'un gabarit officiel est manquant sous standards/blueprints/."""
    pass


class BlueprintLoader:
    """Chargeur centralisé et moteur de rendu des gabarits officiels mLoop."""

    _BLUEPRINTS_DIR_NAME = "standards/blueprints"

    @classmethod
    def find_workspace_root(cls) -> Path:
        """Remonte l'arborescence pour localiser la racine contenant standards/blueprints/."""
        cur = Path.cwd().resolve()
        while cur.parent != cur:
            if (cur / cls._BLUEPRINTS_DIR_NAME).exists():
                return cur
            cur = cur.parent
        return Path.cwd().resolve()

    @classmethod
    def get_blueprint_path(cls, filename: str) -> Path:
        """Résout le chemin absolu d'un fichier blueprint."""
        root = cls.find_workspace_root()
        target = root / cls._BLUEPRINTS_DIR_NAME / filename
        if not target.exists():
            # Fallback relatif direct
            fallback = Path(cls._BLUEPRINTS_DIR_NAME) / filename
            if fallback.exists():
                return fallback.resolve()
            raise BlueprintNotFoundError(
                f"Gabarit officiel '{filename}' introuvable sous '{target}'. "
                f"Assurez-vous que le fichier existe dans {cls._BLUEPRINTS_DIR_NAME}/."
            )
        return target

    @classmethod
    def load_raw(cls, filename: str) -> str:
        """Lit le contenu brut d'un gabarit officiel sous gestionnaire de contexte."""
        path = cls.get_blueprint_path(filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def render(cls, filename: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Charge et injecte les variables déclaratives dans le gabarit.
        Supporte les notations {{VARIABLE}} et {VARIABLE}.
        """
        content = cls.load_raw(filename)
        if not context:
            return content

        rendered = content
        for key, value in context.items():
            str_val = str(value) if value is not None else ""
            # 1. Remplacement de la notation moustaches {{KEY}}
            rendered = rendered.replace(f"{{{{{key}}}}}", str_val)
            # 2. Remplacement de la notation simple {KEY} si présente
            rendered = rendered.replace(f"{{{key}}}", str_val)

        return rendered
