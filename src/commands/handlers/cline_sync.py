# -*- coding: utf-8 -*-
"""
Commandes CLI `cline-sync` & `cline-status` — Harnais écosystème Cline (MLOOP-264-FULL).

`cline-sync`   : projette la Memory Bank (6 fichiers), génère .clinerules/mloop.md et
                 projette les serveurs MCP mLoop (opencode.json) vers cline_mcp_settings.json.
`cline-status` : inspection READ-ONLY (binaire cline, Memory Bank, règles, parité MCP).

OQ-264 : opérations 100% locales sur fichiers, aucun endpoint REST distant.
Conforme ADR-0202 (<=300L), ADR-0369 (logging structuré, context managers, zéro except nu).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.cli import ZeroFluffConsole
from src.bridges.cline.memory_bank_bridge import MemoryBankBridge, MEMORY_BANK_DIR_NAME
from src.bridges.cline.rules_mirror import (
    ClineRulesMirror,
    CLINERULES_DIR_NAME,
    MLOOP_RULES_FILE_NAME,
)
from src.utils.logger import get_logger

logger = get_logger("commands.handlers.cline_sync")

_MEMORY_BANK_FILES = (
    "projectbrief.md",
    "productContext.md",
    "activeContext.md",
    "systemPatterns.md",
    "techContext.md",
    "progress.md",
)
_CLINE_MCP_SETTINGS = "cline_mcp_settings.json"


def _resolve_workspace_root(project_path: Optional[Path]) -> Path:
    """Remonte jusqu'à la racine du workspace (dossier contenant Projects/ ou standards/)."""
    base = (project_path or Path.cwd()).resolve()
    ws = base
    while ws.parent != ws and not (ws / "Projects").exists() and not (ws / "standards").exists():
        ws = ws.parent
    return ws


def _project_dir(ws_root: Path, project_name: str) -> Path:
    """Résout le répertoire projet sous Projects/<name> (ou racine si absent)."""
    candidate = ws_root / "Projects" / project_name
    return candidate if candidate.exists() else ws_root


def _project_mcp_settings(ws_root: Path, source: Dict[str, Any]) -> Dict[str, Any]:
    """Transforme la config MCP opencode.json vers le format Cline cline_mcp_settings.json.

    Format opencode : {name: {type, command:[bin, *args], environment?, enabled?, timeout?}}
    Format Cline    : {"mcpServers": {name: {command, args, env, disabled, timeout}}}
    """
    servers: Dict[str, Any] = {}
    for name, cfg in source.items():
        if not isinstance(cfg, dict):
            continue
        command_spec = cfg.get("command")
        if isinstance(command_spec, list) and command_spec:
            binary, args = command_spec[0], list(command_spec[1:])
        elif isinstance(command_spec, str):
            binary, args = command_spec, []
        else:
            continue
        entry: Dict[str, Any] = {"command": binary, "args": args}
        env = cfg.get("environment") or cfg.get("env")
        if isinstance(env, dict) and env:
            entry["env"] = env
        if "timeout" in cfg:
            entry["timeout"] = cfg["timeout"]
        entry["disabled"] = cfg.get("enabled", True) is False
        servers[name] = entry
    return {"mcpServers": servers}


def _sync_mcp_settings(ws_root: Path, project_dir: Path) -> Optional[Path]:
    """Projette les serveurs MCP depuis opencode.json vers cline_mcp_settings.json (idempotent)."""
    source_file = ws_root / "opencode.json"
    if not source_file.exists():
        logger.debug(
            "[cline-sync] opencode.json introuvable — projection MCP ignorée.",
            extra={"source": str(source_file)},
        )
        return None
    try:
        with source_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug(
            "[cline-sync] opencode.json illisible — projection MCP ignorée.",
            exc_info=True,
            extra={"source": str(source_file), "error": str(exc)},
        )
        return None
    mcp_source = data.get("mcp")
    if not isinstance(mcp_source, dict) or not mcp_source:
        return None
    projected = _project_mcp_settings(ws_root, mcp_source)
    rendered = json.dumps(projected, indent=2, ensure_ascii=False) + "\n"
    target = project_dir / _CLINE_MCP_SETTINGS
    if target.exists() and target.read_text(encoding="utf-8") == rendered:
        return target
    target.write_text(rendered, encoding="utf-8")
    logger.info(
        "[cline-sync] Serveurs MCP projetés vers cline_mcp_settings.json.",
        extra={"target": str(target), "server_count": len(projected["mcpServers"])},
    )
    return target


def handle_cline_sync(args: Any, state: Any, project_path: Path) -> int:
    """`cline-sync --project <p>` : synchronise Memory Bank + règles + serveurs MCP.

    Returns:
        0 en cas de succès, 1 si le répertoire projet est inaccessible en écriture.
    """
    project_name = str(getattr(args, "project", None) or getattr(state, "project_name", "mLoop"))
    ws_root = _resolve_workspace_root(project_path)
    project_dir = _project_dir(ws_root, project_name)
    try:
        bridge = MemoryBankBridge(workspace_root=ws_root, project_name=project_name)
        bank_files = bridge.sync_all()
        mirror = ClineRulesMirror(workspace_root=ws_root)
        rules_file = mirror.sync()
        mcp_file = _sync_mcp_settings(ws_root, project_dir)
    except OSError as exc:
        ZeroFluffConsole.error(f"[cline-sync] Répertoire projet inaccessible en écriture : {exc}")
        logger.error(
            "cline-sync échec I/O (aucune synchronisation complète).",
            exc_info=True,
            extra={"command": "cline-sync", "project": project_name, "error": str(exc)},
        )
        return 1

    ZeroFluffConsole.success(
        f"[cline-sync] Memory Bank ({len(bank_files)} fichiers) et .clinerules/mloop.md synchronisés."
    )
    if mcp_file is not None:
        ZeroFluffConsole.info(f"[cline-sync] Serveurs MCP projetés vers {mcp_file.name}.")
    else:
        ZeroFluffConsole.info("[cline-sync] Aucune source MCP (opencode.json) à projeter.")
    logger.info(
        "cline-sync exécuté avec succès.",
        extra={
            "command": "cline-sync",
            "project": project_name,
            "bank_files": len(bank_files),
            "rules_file": str(rules_file),
            "mcp_projected": mcp_file is not None,
        },
    )
    return 0


def _memory_bank_status(project_dir: Path) -> Dict[str, Any]:
    """Inspecte la présence des 6 fichiers de la Memory Bank (READ-ONLY)."""
    bank_dir = project_dir / "memory" / MEMORY_BANK_DIR_NAME
    present: List[str] = []
    missing: List[str] = []
    for fname in _MEMORY_BANK_FILES:
        (present if (bank_dir / fname).exists() else missing).append(fname)
    return {
        "bank_dir": str(bank_dir),
        "present": present,
        "missing": missing,
        "complete": not missing,
    }


def handle_cline_status(args: Any, state: Any, project_path: Path) -> int:
    """`cline-status --project <p>` : inspection déterministe READ-ONLY de l'écosystème Cline.

    Returns:
        0 systématiquement (commande d'observabilité sans mutation ni échec métier).
    """
    project_name = str(getattr(args, "project", None) or getattr(state, "project_name", "mLoop"))
    ws_root = _resolve_workspace_root(project_path)
    project_dir = _project_dir(ws_root, project_name)

    cline_bin = shutil.which("cline")
    bank = _memory_bank_status(project_dir)
    mirror = ClineRulesMirror(workspace_root=ws_root)
    parity = mirror.verify_parity()
    mcp_file = project_dir / _CLINE_MCP_SETTINGS

    ZeroFluffConsole.section(f"Cline Ecosystem Status — {project_name}")
    ZeroFluffConsole.value("Binaire cline", cline_bin or "ABSENT (non détecté dans le PATH)")
    ZeroFluffConsole.value(
        "Memory Bank",
        f"{len(bank['present'])}/{len(_MEMORY_BANK_FILES)} fichiers"
        + ("" if bank["complete"] else f" — manquants: {', '.join(bank['missing'])}"),
    )
    ZeroFluffConsole.value("Règles .clinerules", parity["status"])
    ZeroFluffConsole.value("cline_mcp_settings.json", "présent" if mcp_file.exists() else "absent")
    if parity["status"] != "PASS":
        ZeroFluffConsole.warning(parity["message"])

    logger.info(
        "cline-status inspecté.",
        extra={
            "command": "cline-status",
            "project": project_name,
            "cline_binary": bool(cline_bin),
            "memory_bank_complete": bank["complete"],
            "rules_parity": parity["status"],
            "mcp_settings_present": mcp_file.exists(),
        },
    )
    return 0
