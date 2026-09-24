"""
src/dashboard/routers/drawdb.py — Router FastAPI DrawDB Souverain (MLOOP-152-BE)

Expose trois endpoints pour le widget Cockpit DrawDB :
  GET  /api/drawdb/list?project=<nom>  — Inventaire *.dbml sous Projects/<projet>/
  GET  /api/drawdb/health              — Sonde d'état du serveur drawdb (:8081)
  POST /api/drawdb/start               — Spawn subprocess du serveur (timeout explicite ADR-0369)

Sous-module de helpers déplacé dans _drawdb_core.py pour ADR-0202 (≤300 lignes).
Contraintes :
  - ADR-0369 : timeout explicite sur subprocess, context managers, jamais except:pass
  - ADR-0202 : module ≤ 300 lignes
  - Zéro exfiltration : aucun appel réseau vers drawdb.app ou CDN
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path
from src.dashboard.routers._drawdb_core import (
    DRAWDB_DEFAULT_PORT,
    REPO_ROOT,
    SPAWN_TIMEOUT_S,
    _spawn_in_progress,
    _spawn_lock,
    check_drawdb_health,
    find_dbml_files,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/drawdb", tags=["DrawDB Sovereign"])

# Re-exports rétrocompatibles (ADR-0202)
__all__ = ["router", "drawdb_health", "drawdb_list", "drawdb_start"]

# Alias rétrocompat pour les tests qui mockent le nom historique
_check_drawdb_health = check_drawdb_health
_find_dbml_files = find_dbml_files


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────


@router.get("/health")
def drawdb_health(port: int = Query(DRAWDB_DEFAULT_PORT, ge=1024, le=65535)) -> Dict[str, Any]:
    """
    Sonde l'état du serveur DrawDB local.
    Retourne {"running": true|false, "port": <port>, "url": "http://localhost:<port>/"}.
    """
    running = _check_drawdb_health(port)
    return {
        "running": running,
        "port": port,
        "url": f"http://localhost:{port}/",
        "status": "🟢 démarré" if running else "🔴 arrêté",
    }


@router.get("/list")
def drawdb_list(
    project: Optional[str] = Query(None, description="Nom du projet mLoop"),
) -> Dict[str, Any]:
    """
    Inventaire récursif des *.dbml sous Projects/<projet>/.
    Retourne la liste des fichiers avec métadonnées (name, parent, path, size_bytes).
    """
    proj_name = resolve_project_canonical_name(project)
    files = find_dbml_files(proj_name)

    response: Dict[str, Any] = {
        "project": proj_name,
        "total": len(files),
        "files": files,
    }
    if not files:
        response["message"] = (
            f"Aucun fichier *.dbml trouvé sous Projects/{proj_name}/. "
            "Créez un fichier DBML pour visualiser votre schéma ERD."
        )
    return response


@router.post("/start")
def drawdb_start(
    port: int = Query(DRAWDB_DEFAULT_PORT, ge=1024, le=65535),
    project: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Démarre le serveur DrawDB en subprocess avec timeout explicite (ADR-0369).
    Anti-rebond : un seul spawn simultané via threading.Lock.
    Re-sonde l'état avant de retourner.

    Retourne {"started": bool, "already_running": bool, "port": int, "error": str|None}.
    """
    global _spawn_in_progress

    proj_name = resolve_project_canonical_name(project) if project else None

    # Vérification rapide : déjà démarré ?
    if _check_drawdb_health(port):
        return {
            "started": True,
            "already_running": True,
            "port": port,
            "url": f"http://localhost:{port}/",
            "error": None,
        }

    # Anti-rebond : verrou + flag
    with _spawn_lock:
        if _spawn_in_progress:
            # Un spawn est en cours — attente passive puis re-sonde
            for _ in range(SPAWN_TIMEOUT_S * 2):
                time.sleep(0.5)
                if _check_drawdb_health(port):
                    return {
                        "started": True,
                        "already_running": False,
                        "port": port,
                        "url": f"http://localhost:{port}/",
                        "error": None,
                    }
            return {
                "started": False,
                "already_running": False,
                "port": port,
                "url": None,
                "error": "Un spawn était en cours mais le serveur n'a pas répondu dans le délai imparti.",
            }

        _spawn_in_progress = True

    runner = REPO_ROOT / "tools" / "drawdb" / "runner.py"
    if not runner.exists():
        _spawn_in_progress = False
        raise HTTPException(
            status_code=500,
            detail=f"runner.py introuvable : {runner}",
        )

    cmd = [sys.executable, str(runner), str(port)]
    if proj_name:
        cmd.append(proj_name)

    try:
        # Popen non-bloquant — le serveur tourne en arrière-plan
        proc = subprocess.Popen(  # noqa: RULE-AST-03 (bornes via boucle deadline SPAWN_TIMEOUT_S + proc.poll())
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            close_fds=True,
        )

        # Attendre que le serveur soit prêt (max SPAWN_TIMEOUT_S secondes)
        deadline = time.monotonic() + SPAWN_TIMEOUT_S
        healthy = False
        while time.monotonic() < deadline:
            time.sleep(0.4)
            if _check_drawdb_health(port):
                healthy = True
                break
            # Vérifier si le processus a déjà crashé
            if proc.poll() is not None:
                stderr_out = ""
                try:
                    raw_err = proc.stderr.read(500) if proc.stderr else b""
                    stderr_out = (raw_err or b"").decode("utf-8", errors="replace")
                except Exception as exc_rd:
                    logger.debug(
                        "Lecture stderr subprocess crashé impossible",
                        exc_info=True,
                        extra={
                            "component": "drawdb",
                            "operation": "drawdb_start",
                            "error": str(exc_rd),
                        },
                    )
                _spawn_in_progress = False
                return {
                    "started": False,
                    "already_running": False,
                    "port": port,
                    "url": None,
                    "error": f"Le processus DrawDB s'est terminé prématurément (code {proc.returncode}). {stderr_out}",
                }

        _spawn_in_progress = False

        if healthy:
            logger.info(
                "Serveur DrawDB démarré avec succès",
                extra={
                    "component": "drawdb",
                    "operation": "drawdb_start",
                    "port": port,
                    "project": proj_name,
                    "pid": proc.pid,
                },
            )
            return {
                "started": True,
                "already_running": False,
                "port": port,
                "url": f"http://localhost:{port}/",
                "error": None,
            }

        # Timeout dépassé — tenter de lire stderr pour la cause
        stderr_out = ""
        try:
            proc.terminate()
            raw_err2 = proc.stderr.read(500) if proc.stderr else b""
            stderr_out = (raw_err2 or b"").decode("utf-8", errors="replace")
        except Exception as exc2:
            logger.debug(
                "Impossible de lire stderr du subprocess DrawDB",
                exc_info=True,
                extra={"component": "drawdb", "operation": "drawdb_start", "error": str(exc2)},
            )

        error_msg = (
            f"Le serveur DrawDB n'a pas répondu dans {SPAWN_TIMEOUT_S}s "
            f"(port {port} peut être occupé). {stderr_out}"
        )
        logger.warning(
            error_msg,
            extra={
                "component": "drawdb",
                "operation": "drawdb_start",
                "port": port,
                "timeout": SPAWN_TIMEOUT_S,
            },
        )
        return {
            "started": False,
            "already_running": False,
            "port": port,
            "url": None,
            "error": error_msg,
        }

    except OSError as exc:
        _spawn_in_progress = False
        logger.error(
            "OSError lors du spawn DrawDB",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "drawdb_start",
                "port": port,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Impossible de lancer le subprocess DrawDB : {exc}",
        ) from exc
    except Exception as exc:
        _spawn_in_progress = False
        logger.error(
            "Erreur inattendue lors du spawn DrawDB",
            exc_info=True,
            extra={
                "component": "drawdb",
                "operation": "drawdb_start",
                "port": port,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors du démarrage DrawDB : {exc}",
        ) from exc
