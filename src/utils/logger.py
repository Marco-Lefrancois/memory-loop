"""
mLoop Framework Logging Engine (ADR-0369 Standard Senior)
Système de logging unifié, structuré et contextuel pour l'ensemble du runtime Memory Loop.
Permet d'éliminer les 'except Exception: pass' silencieux en capturant les erreurs avec contexte.
Supporte le pattern 'extra={...}' et 'MLoopLoggerAdapter' selon les standards d'ingénierie mLoop.
"""

import logging
import os
import sys
from typing import Any, Dict, Optional


class MLoopFormatter(logging.Formatter):
    """
    Formateur compact et lisible pour la console et les fichiers de log mLoop.
    Extrait et affiche automatiquement les paires clé-valeur passées via `extra={...}`.
    """

    FORMAT_CONSOLE = "%(levelname)s [%(name)s] %(message)s"
    FORMAT_DEBUG = "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"

    BUILTIN_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def __init__(self, debug_mode: bool = False):
        fmt = self.FORMAT_DEBUG if debug_mode else self.FORMAT_CONSOLE
        super().__init__(fmt, datefmt="%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        base_msg = super().format(record)
        # Extraction dynamique des attributs extra transmis
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self.BUILTIN_ATTRS and not k.startswith("_")
        }
        if extras:
            extra_str = " ".join(f"{k}={v}" for k, v in sorted(extras.items()))
            return f"{base_msg} | {extra_str}"
        return base_msg


class MLoopLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter contextuel mLoop permettant d'attacher automatiquement des métadonnées
    communes (projet, story_id, phase) à l'ensemble des appels de log d'un composant.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        extra = kwargs.get("extra", {})
        combined = {**self.extra, **extra}
        kwargs["extra"] = combined
        return msg, kwargs


def get_logger(name: str = "mloop", **context_kwargs) -> logging.Logger:
    """
    Retourne une instance de logger configurée pour le module demandé.
    Si des paramètres contextuels sont fournis, retourne un MLoopLoggerAdapter.
    
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

    if context_kwargs:
        return MLoopLoggerAdapter(logger, context_kwargs)  # type: ignore

    return logger
