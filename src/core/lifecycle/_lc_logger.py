"""
_lc_logger.py — Logger proxy patchable pour le package lifecycle.

Le proxy délègue dynamiquement à src.core.lifecycle.logger, ce qui permet
à patch.object(src.core.lifecycle, 'logger') d'affecter tous les sous-modules
sans circularité d'import.
"""

from __future__ import annotations
import sys
from typing import Any


class _ProxyLogger:
    """Délègue dynamiquement à src.core.lifecycle.logger (patchable via patch.object)."""

    def _delegate(self):
        mod = sys.modules.get("src.core.lifecycle")
        if mod is not None:
            delegate = mod.__dict__.get("logger")
            if delegate is not None and delegate is not self:
                return delegate
        # Fallback : logger Python standard si le package n'est pas encore résolu
        import logging

        return logging.getLogger("mloop.core.lifecycle")

    @property
    def name(self) -> str:
        return self._delegate().name

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._delegate().info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._delegate().warning(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._delegate().debug(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._delegate().error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._delegate().critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._delegate().exception(msg, *args, **kwargs)


logger = _ProxyLogger()
