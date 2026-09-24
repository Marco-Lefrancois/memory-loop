"""
herdr_daemon.py - Herdr daemon lifecycle management (ADR-0306 / Zero-Fail Carryover).

Auto-heal du daemon Herdr : vérifie la joignabilité du serveur headless via
`herdr status server`, le relance en arrière-plan détaché si nécessaire, et
re-sonde jusqu'à confirmation.
"""

import json
import subprocess
import sys
import logging
from typing import Any, Dict

logger = logging.getLogger("mloop.herdr_daemon")


class HerdrDaemonMixin:
    """Daemon lifecycle management (auto-heal, Zero-Fail Carryover)."""

    def _is_server_running(self) -> bool:
        """Vérifie si le daemon Herdr est joignable via `herdr status server`."""
        res = self._exec(["status", "server"], timeout=10)
        if not res.get("success"):
            return False
        blob = ""
        if isinstance(res.get("result"), dict):
            blob = json.dumps(res["result"]).lower()
        else:
            blob = str(res.get("raw_output", "")).lower()
        if "not running" in blob:
            return False
        return "running" in blob

    def ensure_server_running(self, wait_sec: int = 5) -> bool:
        """
        Auto-heal du daemon Herdr (Zero-Fail Carryover) : si le serveur headless n'est pas
        démarré, le lance via `herdr server` en arrière-plan détaché, puis re-sonde
        jusqu'à confirmation ou expiration. Idempotent si déjà running.
        """
        import time

        if self._is_server_running():
            return True

        logger.warning("Daemon Herdr non démarré — tentative d'auto-heal via 'herdr server'.")
        try:
            kwargs: Dict[str, Any] = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
                    subprocess, "DETACHED_PROCESS", 0
                )
            else:
                kwargs["start_new_session"] = True
            try:
                proc = subprocess.Popen(  # noqa: RULE-AST-03 (attente bornée via proc.wait(timeout=10) L64)
                    [self.herdr_bin, "server"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **kwargs,
                )
                # RULE-AST-03: timeout explicite sur Popen via wait()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.debug(
                        "Daemon 'herdr server' détaché et toujours actif après 10s.",
                        extra={"pid": proc.pid},
                    )
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.debug(
                        "Daemon 'herdr server' détaché et toujours actif après 2s.",
                        extra={"pid": proc.pid},
                    )
            except Exception as e:
                logger.error(
                    f"Échec du lancement de 'herdr server' : {e}",
                    exc_info=True,
                    extra={"bin": self.herdr_bin},
                )
                return False
        except Exception as e:
            logger.error(
                f"Erreur inattendue durant l'auto-heal du daemon Herdr : {e}",
                exc_info=True,
                extra={"bin": self.herdr_bin},
            )
            return False

        deadline = wait_sec
        elapsed = 0.0
        while elapsed < deadline:
            time.sleep(0.5)
            elapsed += 0.5
            if self._is_server_running():
                logger.info("Daemon Herdr démarré avec succès (auto-heal).")
                return True
        logger.error("Le daemon Herdr n'a pas répondu après auto-heal.")
        return False
