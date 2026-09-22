# -*- coding: utf-8 -*-
"""
Lanceur Uvicorn pour le Dashboard d'Observabilité mLoop.
Gère l'initialisation du serveur FastAPI et l'ouverture automatique du navigateur.
"""

from __future__ import annotations

import os
import threading
import webbrowser
from typing import Optional

import uvicorn
from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("dashboard.runner")


def serve_dashboard(
    port: int = 8080,
    host: str = "127.0.0.1",
    project: Optional[str] = None,
    open_browser: bool = True,
) -> None:
    """
    Démarre le serveur FastAPI d'observabilité en local et ouvre le dashboard dans le navigateur.
    """
    if project:
        os.environ["MLOOP_ACTIVE_PROJECT"] = project

    url = f"http://{host}:{port}"

    ZeroFluffConsole.section("Tableau de Bord Souverain d'Observabilité mLoop")
    ZeroFluffConsole.info(f"Serveur local Uvicorn/FastAPI démarré sur : {url}")
    ZeroFluffConsole.info("Mode Zéro-Docker actif : 100% Python pur et données locales.")
    if project:
        ZeroFluffConsole.info(f"Projet actif ciblé : {project}")
    ZeroFluffConsole.info("Pressez Ctrl+C pour arrêter le serveur.")

    if open_browser:

        def _open():
            try:
                webbrowser.open(url)
            except Exception as e:
                logger.debug(
                    "Ouverture automatique du navigateur échouée, serveur toujours actif",
                    exc_info=True,
                    extra={
                        "component": "dashboard.runner",
                        "operation": "serve_dashboard",
                        "url": url,
                        "error": str(e),
                    },
                )

        # Ouvrir le navigateur après 1.2 seconde
        threading.Timer(1.2, _open).start()

    # Démarrage du serveur Uvicorn
    uvicorn.run(
        "src.dashboard.server:app",
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
