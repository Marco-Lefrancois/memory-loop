"""
mLoop Framework Logging Engine
Système de logging unifié, structuré et contextuel pour l'ensemble du runtime Memory Loop.
Permet d'éliminer les 'except Exception: pass' silencieux en capturant les erreurs avec contexte.
"""

import logging
import os
import sys
from typing import Optional


class MLoopFormatter(logging.Formatter):
    """Formateur compact et lisible pour la console et les fichiers de log mLoop."""

    FORMAT_CONSOLE = "%(levelname)s [%(name)s] %(message)s"
    FORMAT_DEBUG = "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"

    def __init__(self, debug_mode: bool = False):
        fmt = self.FORMAT_DEBUG if debug_mode else self.FORMAT_CONSOLE
        super().__init__(fmt, datefmt="%H:%M:%S")


def get_logger(name: str = "mloop") -> logging.Logger:
    """
    Retourne une instance de logger configurée pour le module demandé.
    
    Le niveau de log peut être ajusté via la variable d'environnement MLOOP_LOG_LEVEL
    (DEBUG, INFO, WARNING, ERROR, CRITICAL). Par défaut : WARNING pour éviter tout bruit en console.
    """
    logger = logging.getLogger(f"mloop.{name}" if not name.startswith("mloop") else name)

    # Éviter d'ajouter plusieurs handlers si get_logger est appelé plusieurs fois
    if not logger.handlers:
        log_level_str = os.environ.get("MLOOP_LOG_LEVEL", "WARNING").upper()
        level = getattr(logging, log_level_str, logging.WARNING)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        handler.setFormatter(MLoopFormatter(debug_mode=(level == logging.DEBUG)))
        logger.addHandler(handler)
        logger.propagate = False

    return logger
