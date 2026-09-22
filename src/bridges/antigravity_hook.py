# -*- coding: utf-8 -*-
"""
Antigravity IDE Hook Bridge for mLoop (ADR-0364).

Pont de communication bidirectionnel entre le moteur de hooks d'Antigravity IDE
(.agents/hooks.json) et le moteur de pré-compaction et de points de contrôle mLoop.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.engine.hooks.compaction import PreCompactionHandler, CompactionRecoveryManager
from src.engine.hooks.path_resolver import PathAliasResolver
from src.utils.logger import get_logger

# NOTE : les appels print(json.dumps(...)) de ce module constituent le contrat de sortie
# stdout du protocole de hooks Antigravity et NE doivent PAS être convertis en logs.
# Seuls les handlers d'exception silencieux sont instrumentés (vers stderr via le logger).
logger = get_logger("bridges.antigravity_hook")


def parse_stdin_json() -> dict:
    """Lit et décode le JSON de manière 100% non bloquante sous Windows (PeekNamedPipe) et POSIX (select)."""
    try:
        if sys.platform == "win32":
            import msvcrt
            import ctypes
            from ctypes import wintypes

            handle = msvcrt.get_osfhandle(sys.stdin.fileno())
            avail = wintypes.DWORD()
            success = ctypes.windll.kernel32.PeekNamedPipe(
                handle, None, 0, None, ctypes.byref(avail), None
            )
            if success and avail.value > 0:
                raw_input = sys.stdin.read(avail.value)
                if raw_input and raw_input.strip():
                    data = json.loads(raw_input)
                    if isinstance(data, dict):
                        return data
        else:
            import select

            r, _, _ = select.select([sys.stdin], [], [], 0.0)
            if r:
                raw_input = sys.stdin.read()
                if raw_input and raw_input.strip():
                    data = json.loads(raw_input)
                    if isinstance(data, dict):
                        return data
    except Exception as e:
        logger.debug(
            "Lecture non bloquante du JSON stdin Antigravity échouée (payload vide utilisé)",
            exc_info=True,
            extra={
                "component": "bridges.antigravity_hook",
                "operation": "parse_stdin_json",
                "platform": sys.platform,
                "error": str(e),
            },
        )
    return {}


def resolve_project_name(payload: dict, cli_project: str | None = None) -> str:
    """Résout le nom de projet à partir de la CLI, de l'environnement ou du payload Antigravity."""
    if cli_project and cli_project != "auto":
        return cli_project

    env_proj = os.environ.get("MLOOP_ACTIVE_PROJECT")
    if env_proj:
        return env_proj

    # Recherche dans active_project.json
    active_json = REPO_ROOT / "memory" / "active_project.json"
    if active_json.exists():
        try:
            data = json.loads(active_json.read_text(encoding="utf-8"))
            if data.get("active_project"):
                return data["active_project"]
        except Exception as e:
            logger.debug(
                "Lecture de active_project.json échouée lors de la résolution projet",
                exc_info=True,
                extra={
                    "component": "bridges.antigravity_hook",
                    "operation": "resolve_project_name",
                    "active_json": str(active_json),
                    "error": str(e),
                },
            )

    # Détection via workspacePaths
    workspace_paths = payload.get("workspacePaths", [])
    if workspace_paths:
        ws_name = Path(workspace_paths[0]).name
        if ws_name and ws_name not in (".", "Memory Loop", "memory-loop"):
            return ws_name

    return "Memory Loop"


def main():
    parser = argparse.ArgumentParser(description="mLoop Antigravity Hook Bridge")
    parser.add_argument(
        "--event",
        choices=[
            "pre_tool_use",
            "post_tool_use",
            "pre_invocation",
            "post_invocation",
            "stop",
            "pre_compact",
        ],
        default="post_tool_use",
        help="Type d'événement Antigravity intercepté",
    )
    parser.add_argument("--project", default="auto", help="Nom du projet actif")
    args = parser.parse_args()

    payload = parse_stdin_json()
    project_name = resolve_project_name(payload, args.project)

    # 1. Événement PostToolUse
    if args.event == "post_tool_use":
        try:
            tool_call = payload.get("toolCall", {})
            tool_name = tool_call.get("name", "")
            # Mise à jour du checkpoint lors d'éditions ou d'exécutions de commandes
            if any(k in tool_name for k in ("write", "replace", "command")):
                PreCompactionHandler.create_checkpoint(
                    project_name=project_name,
                    base_dir=REPO_ROOT,
                )
        except Exception as e:
            logger.warning(
                "Création du checkpoint sur PostToolUse échouée",
                exc_info=True,
                extra={
                    "component": "bridges.antigravity_hook",
                    "operation": "main.post_tool_use",
                    "project": project_name,
                    "error": str(e),
                },
            )
        # Antigravity PostToolUse attend un objet JSON vide sur stdout
        print(json.dumps({}))
        sys.exit(0)

    # 2. Événement PreInvocation
    elif args.event == "pre_invocation":
        # Vérification si un checkpoint de reprise doit être injecté
        response = {"injectSteps": []}
        try:
            checkpoint = CompactionRecoveryManager.recover_checkpoint(
                project_name=project_name, base_dir=REPO_ROOT
            )
            # Si le checkpoint a des instructions de reprise récentes
            if checkpoint and checkpoint.resume_instructions:
                # Injection optionnelle si désiré
                pass
        except Exception as e:
            logger.warning(
                "Récupération du checkpoint sur PreInvocation échouée",
                exc_info=True,
                extra={
                    "component": "bridges.antigravity_hook",
                    "operation": "main.pre_invocation",
                    "project": project_name,
                    "error": str(e),
                },
            )
        print(json.dumps(response))
        sys.exit(0)

    # 3. Événement Stop
    elif args.event == "stop":
        try:
            PreCompactionHandler.create_checkpoint(
                project_name=project_name,
                base_dir=REPO_ROOT,
            )
        except Exception as e:
            logger.warning(
                "Création du checkpoint sur l'événement Stop échouée",
                exc_info=True,
                extra={
                    "component": "bridges.antigravity_hook",
                    "operation": "main.stop",
                    "project": project_name,
                    "error": str(e),
                },
            )
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # 4. Événement PreCompact direct
    elif args.event == "pre_compact":
        try:
            cp = PreCompactionHandler.create_checkpoint(
                project_name=project_name,
                base_dir=REPO_ROOT,
            )
            print(json.dumps({"status": "ok", "checkpoint_hash": cp.checkpoint_hash}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(0)

    else:
        print(json.dumps({}))
        sys.exit(0)


if __name__ == "__main__":
    main()
