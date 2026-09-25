"""
Handlers OpenCode CLI : init, run, status, sync (MLOOP-220-BE / MLOOP-254-FULL / ADR-014).

Pilote l'intégration d'OpenCode CLI avec configuration déclarative, parité miroir des personas,
outils TypeScript natifs et synchronisation préservatrice.
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

from src.bridges.opencode.mirror_sync import PersonasSyncEngine
from src.bridges.opencode.tools_bridge import OpenCodeToolsBridge
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


def handle_sync(args: argparse.Namespace, state: Any, project_path: Path) -> int:
    """Synchronise les personas, outils natifs et configuration OpenCode."""
    if not project_path or not project_path.exists():
        ZeroFluffConsole.error(f"Dossier projet introuvable : {project_path}")
        return 1

    dry_run = getattr(args, "dry_run", False)
    opencode_dir = project_path / ".opencode"
    cfg_file = opencode_dir / "opencode.json"
    project_name = getattr(args, "project", None) or project_path.name

    prefix = "[Dry-Run] " if dry_run else ""
    ZeroFluffConsole.info(f"{prefix}Synchronisation OpenCode pour le projet '{project_name}'...")

    if dry_run:
        ZeroFluffConsole.info("  • Simulation : synchronisation miroir .agents/ -> .opencode/agents/")
        ZeroFluffConsole.info("  • Simulation : déploiement outils natifs .opencode/tools/")
        ZeroFluffConsole.info("  • Simulation : mise à jour préservatrice de .opencode/opencode.json")
        return 0

    personas_engine = PersonasSyncEngine(workspace_root=project_path)
    personas_stats = personas_engine.sync_all()
    ZeroFluffConsole.success(
        f"  • Personas : {personas_stats['synced']} synchronisé(s), {personas_stats['skipped']} inchangé(s)"
    )

    tools_bridge = OpenCodeToolsBridge(workspace_root=project_path)
    tools_stats = tools_bridge.deploy_tools()
    ZeroFluffConsole.success(
        f"  • Outils TypeScript : {tools_stats['deployed']} déployé(s), {tools_stats['skipped']} inchangé(s)"
    )

    opencode_dir.mkdir(parents=True, exist_ok=True)
    fresh_cfg = generate_opencode_config(project_name)

    if cfg_file.exists():
        try:
            bak_file = opencode_dir / "opencode.json.bak"
            existing_raw = cfg_file.read_text(encoding="utf-8")
            bak_file.write_text(existing_raw, encoding="utf-8")
            existing_data = json.loads(existing_raw)
            for key, val in fresh_cfg.items():
                if key not in existing_data:
                    existing_data[key] = val
                elif isinstance(val, dict) and isinstance(existing_data[key], dict):
                    for subkey, subval in val.items():
                        if subkey not in existing_data[key]:
                            existing_data[key][subkey] = subval
            cfg_file.write_text(json.dumps(existing_data, indent=2, ensure_ascii=False), encoding="utf-8")
            ZeroFluffConsole.success(f"  • Configuration fusionnée (sauvegarde : {bak_file.name})")
        except Exception as e:
            logger.warning(f"Erreur fusion opencode.json : {e}")
            cfg_file.write_text(json.dumps(fresh_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        cfg_file.write_text(json.dumps(fresh_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.success("  • Configuration opencode.json initialisée")

    return 0


def handle_status(args: argparse.Namespace, state: Any, project_path: Path) -> int:
    """Affiche un audit complet de l'environnement de développement OpenCode."""
    has_bin = is_opencode_available()
    has_proxy = check_litellm_connectivity()

    cfg_file = project_path / ".opencode" / "opencode.json" if project_path else None
    has_cfg = cfg_file.exists() if cfg_file else False

    personas_engine = PersonasSyncEngine(workspace_root=project_path)
    is_sync, missing_personas = personas_engine.check_mirror_parity()

    tools_bridge = OpenCodeToolsBridge(workspace_root=project_path)
    has_tools = tools_bridge.check_tools_installed()

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

    if is_sync:
        ZeroFluffConsole.success("  • Personas miroir : 100% SYNCHRONISÉS (.opencode/agents/)")
    else:
        ZeroFluffConsole.warning(f"  • Personas miroir : MANQUANTS ({', '.join(missing_personas)})")

    if has_tools:
        ZeroFluffConsole.success("  • Outils TypeScript : DÉPLOYÉS (.opencode/tools/)")
    else:
        ZeroFluffConsole.info("  • Outils TypeScript : NON INSTALLÉS (mloop opencode sync)")

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
    if action == "sync":
        return handle_sync(args, state, project_path)
    if action == "run":
        return handle_run(args, state, project_path)
    if action == "status":
        return handle_status(args, state, project_path)

    ZeroFluffConsole.error(f"Action OpenCode inconnue : '{action}'. Actions valides : init, sync, run, status.")
    return 1
