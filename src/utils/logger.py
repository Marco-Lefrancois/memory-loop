"""
mLoop Framework Logging Engine (ADR-0369 Standard Senior)
Système de logging unifié, structuré et contextuel pour l'ensemble du runtime Memory Loop.
Permet d'éliminer les 'except Exception: pass' silencieux en capturant les erreurs avec contexte.
Supporte le pattern 'extra={...}' et 'MLoopLoggerAdapter' selon les standards d'ingénierie mLoop.

MLOOP-110-BE : Ajout de la persistance rotative des journaux d'erreurs.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class MLoopFormatter(logging.Formatter):
    """
    Formateur compact et lisible pour la console et les fichiers de log mLoop.
    Extrait et affiche automatiquement les paires clé-valeur passées via `extra={...}`.
    """

    FORMAT_CONSOLE = "%(levelname)s [%(name)s] %(message)s"
    FORMAT_DEBUG = "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"
    FORMAT_FILE = "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"

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

    def __init__(self, debug_mode: bool = False, file_mode: bool = False):
        if file_mode:
            fmt = self.FORMAT_FILE
        elif debug_mode:
            fmt = self.FORMAT_DEBUG
        else:
            fmt = self.FORMAT_CONSOLE
        super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")

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


def _setup_rotating_error_handler(
    logger_instance: logging.Logger,
    log_dir: Path,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Configure un RotatingFileHandler pour les logs d'erreurs (ERROR et supérieur).

    Args:
        logger_instance: Instance du logger à configurer.
        log_dir: Répertoire de destination des fichiers de log.
        max_bytes: Taille maximale par fichier (défaut : 5 Mo).
        backup_count: Nombre de fichiers de backup à conserver (défaut : 5).
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    error_log_path = log_dir / "errors.log"

    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(MLoopFormatter(file_mode=True))
    logger_instance.addHandler(error_handler)


def _setup_rotating_info_handler(
    logger_instance: logging.Logger,
    log_dir: Path,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """
    Configure un RotatingFileHandler pour tous les logs (INFO et supérieur).

    Args:
        logger_instance: Instance du logger à configurer.
        log_dir: Répertoire de destination des fichiers de log.
        max_bytes: Taille maximale par fichier (défaut : 10 Mo).
        backup_count: Nombre de fichiers de backup à conserver (défaut : 3).
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    info_log_path = log_dir / "mloop.log"

    info_handler = logging.handlers.RotatingFileHandler(
        info_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(MLoopFormatter(file_mode=True))
    logger_instance.addHandler(info_handler)


def get_logger(name: str = "mloop", **context_kwargs) -> logging.Logger:
    """
    Retourne une instance de logger configurée pour le module demandé.
    Si des paramètres contextuels sont fournis, retourne un MLoopLoggerAdapter.

    Configuration :
        - MLOOP_LOG_LEVEL : Niveau de log console (défaut : WARNING).
        - MLOOP_LOG_DIR : Répertoire pour les fichiers rotatifs (défaut : memory/logs/).
        - MLOOP_LOG_MAX_BYTES : Taille max par fichier (défaut : 5 Mo pour errors, 10 Mo pour info).
        - MLOOP_LOG_BACKUP_COUNT : Nombre de backups (défaut : 5 pour errors, 3 pour info).
        - MLOOP_LOG_ENABLE_FILE : Activer la persistance fichier (défaut : true).
    """
    logger = logging.getLogger(f"mloop.{name}" if not name.startswith("mloop") else name)

    # Éviter d'ajouter plusieurs handlers si get_logger est appelé plusieurs fois
    if not logger.handlers:
        log_level_str = os.environ.get("MLOOP_LOG_LEVEL", "WARNING").upper()
        level = getattr(logging, log_level_str, logging.WARNING)
        logger.setLevel(level)

        # Handler console
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        handler.setFormatter(MLoopFormatter(debug_mode=(level == logging.DEBUG)))
        logger.addHandler(handler)

        # Configuration de la persistance rotative (MLOOP-110-BE)
        enable_file = os.environ.get("MLOOP_LOG_ENABLE_FILE", "true").lower()
        if enable_file not in ("false", "0", "no"):
            log_dir_str = os.environ.get("MLOOP_LOG_DIR", "memory/logs")
            log_dir = Path(log_dir_str)

            max_bytes_str = os.environ.get("MLOOP_LOG_MAX_BYTES", "")
            backup_count_str = os.environ.get("MLOOP_LOG_BACKUP_COUNT", "")

            error_max = int(max_bytes_str) if max_bytes_str.isdigit() else 5 * 1024 * 1024
            error_backup = int(backup_count_str) if backup_count_str.isdigit() else 5
            info_max = error_max * 2 if max_bytes_str.isdigit() else 10 * 1024 * 1024
            info_backup = max(1, error_backup - 2) if backup_count_str.isdigit() else 3

            _setup_rotating_error_handler(logger, log_dir, error_max, error_backup)
            _setup_rotating_info_handler(logger, log_dir, info_max, info_backup)

        logger.propagate = False

    if context_kwargs:
        return MLoopLoggerAdapter(logger, context_kwargs)  # type: ignore

    return logger
