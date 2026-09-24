"""
Handlers OpenCode CLI : init, run, status (MLOOP-220-BE / ADR-014).

Pilote l'intégration d'OpenCode CLI avec configuration déclarative par projet
et routage des appels vers le proxy local LiteLLM (port 4000).
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.state import LoopState

logger = get_logger("commands.opencode")

DEFAULT_LITELLM_ENDPOINT = "http://localhost:4000/v1"
DEFAULT_MODELS = [
    "claude-3-5-sonnet-20241022",
    "gemini-2.0-flash",
    "gpt-4o",
]


def is_opencode_available() -> bool:
    """Détecte si le binaire 'opencode' est installé et résoluble sur le PATH."""
    return shutil.which("opencode") is not None


def check_litellm_connectivity(
    host: str = "127.0.0.1", port: int = 4000, timeout: float = 1.0
) -> bool:
    """Vérifie la disponibilité locale du socket LiteLLM (délai configurable)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def generate_opencode_config(project_name: str) -> Dict[str, Any]:
    """Génère la structure déclarative normalisée pour opencode.json."""
    return {
        "$schema": "https://opencode.ai/schema.json",
        "project": project_name,
        "providers": {
            "litellm": {
                "endpoint": DEFAULT_LITELLM_ENDPOINT,
                "models": DEFAULT_MODELS,
            }
        },
        "rules": [
            "Respecter scrupuleusement les protocoles et directives mLoop (AGENTS.md).",
            "Plafond strict de 300 lignes par fichier de code Python source (ADR-0202).",
            "Éviter toute modification de code de production sans plan validé.",
        ],
    }


def handle_init(args: argparse.Namespace, state: Any, project_path: Path) -> int:
    """Initialise le fichier de configuration `.opencode/opencode.json` pour un projet."""
    if not project_path or not project_path.exists():
        ZeroFluffConsole.error(f"Dossier projet introuvable : {project_path}")
        return 1

    opencode_dir = project_path / ".opencode"
    opencode_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = opencode_dir / "opencode.json"

    project_name = getattr(args, "project", None) or project_path.name
    if not project_name or not project_name.strip():
        ZeroFluffConsole.error("Nom de projet invalide ou champ vide.")
        return 1

    try:
        cfg = generate_opencode_config(project_name)
        cfg_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success(f"Configuration OpenCode initialisée : {cfg_file}")
        return 0
    except OSError as e:
        logger.error("Échec de l'écriture du fichier opencode.json", exc_info=True)
        ZeroFluffConsole.error(f"Erreur d'écriture : {e}")
        return 1


def handle_status(args: argparse.Namespace, state: Any, project_path: Path) -> int:
    """Affiche un audit de l'environnement de développement OpenCode."""
    has_bin = is_opencode_available()
    has_proxy = check_litellm_connectivity()

    cfg_file = project_path / ".opencode" / "opencode.json" if project_path else None
    has_cfg = cfg_file.exists() if cfg_file else False

    ZeroFluffConsole.info("=== État de l'Environnement OpenCode CLI ===")
    if has_bin:
        ZeroFluffConsole.success("  • Binaire OpenCode : DISPONIBLE sur le PATH")
    else:
        ZeroFluffConsole.warning("  • Binaire OpenCode : NON DÉTECTÉ (npm i -g opencode-ai)")

    if has_proxy:
        ZeroFluffConsole.success("  • Proxy LiteLLM (port 4000) : CONNECTÉ")
    else:
        ZeroFluffConsole.warning("  • Proxy LiteLLM (port 4000) : NON ACCESSIBLE")

    if has_cfg:
        ZeroFluffConsole.success(f"  • Configuration projet : PRÉSENTE ({cfg_file})")
    else:
        ZeroFluffConsole.info("  • Configuration projet : NON INITIALISÉE (mloop opencode init)")

    return 0 if has_bin else 1


def handle_run(args: argparse.Namespace, state: Any, project_path: Path) -> int:
    """Lance une session OpenCode avec contexte projet isolé."""
    if not is_opencode_available():
        ZeroFluffConsole.error(
            "Le binaire 'opencode' est introuvable. Installez-le via 'npm i -g opencode-ai'."
        )
        return 1

    cmd = ["opencode"]
    prompt = getattr(args, "prompt", None)
    if prompt:
        cmd.extend(["--prompt", prompt])

    if getattr(args, "headless", False):
        cmd.append("--headless")

    cwd = project_path if project_path and project_path.exists() else Path.cwd()
    ZeroFluffConsole.info(f"Lancement d'OpenCode CLI dans {cwd}...")

    try:
        res = subprocess.run(cmd, cwd=cwd, timeout=3600.0)
        return res.returncode
    except Exception as e:
        logger.error("Erreur lors de l'exécution d'OpenCode", exc_info=True)
        ZeroFluffConsole.error(f"Erreur d'exécution : {e}")
        return 1


def handle_opencode(args: argparse.Namespace, state: Any, project_path: Path) -> int:
    """Point d'entrée principal pour la commande `mloop opencode`."""
    action = getattr(args, "action", "status") or "status"
    action = action.lower()

    if action == "init":
        return handle_init(args, state, project_path)
    if action == "run":
        return handle_run(args, state, project_path)
    if action == "status":
        return handle_status(args, state, project_path)

    ZeroFluffConsole.error(f"Action OpenCode inconnue : '{action}'. Actions valides : init, run, status.")
    return 1
