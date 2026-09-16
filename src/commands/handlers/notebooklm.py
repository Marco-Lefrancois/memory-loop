"""
Handler pour la commande CLI mLoop 'notebooklm' (Gestion, Export et Authentification).
"""

from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from src.cli import ZeroFluffConsole
from src.pipelines.notebooklm_export import NotebookLMExporter

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

NOTEBOOK_URL = "https://notebook.google.com/notebook/ddf80a44-cf1c-4eb8-86fd-7cebe6156f87"
DEFAULT_NOTEBOOK_ID = "memory-loop-ssot"

def _get_auth_status() -> dict:
    localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
    profile_dir = localappdata / "notebooklm-mcp" / "Data" / "chrome_profile"
    if not profile_dir.exists():
        return {"authenticated": False, "reason": "Profil Chrome inexistant"}

    cookies_file = profile_dir / "Default" / "Network" / "Cookies"
    storage_dir = profile_dir / "Default" / "Local Storage"
    has_data = cookies_file.exists() or (storage_dir.exists() and any(storage_dir.iterdir()))

    return {
        "authenticated": has_data,
        "profile_dir": str(profile_dir),
        "notebook_id": DEFAULT_NOTEBOOK_ID,
        "notebook_url": NOTEBOOK_URL,
        "reason": "Session Chrome active détectée" if has_data else "Session incomplète"
    }

def handle_notebooklm(args: "argparse.Namespace", state: "LoopState" = None, project_path: Path = None) -> int:
    """Point d'entrée pour la commande mLoop 'notebooklm'."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent

    # 1. Action Auth
    if getattr(args, "auth", False):
        script_path = root_dir / "login_notebooklm.mjs"
        if not script_path.exists():
            ZeroFluffConsole.error(f"Script de connexion introuvable : {script_path}")
            return 1
        ZeroFluffConsole.info("Lancement de la fenêtre Chrome pour connexion à Google NotebookLM...")
        try:
            res = subprocess.run(["node", str(script_path)], check=True, timeout=120.0)
            return res.returncode
        except subprocess.TimeoutExpired:
            ZeroFluffConsole.error("Délai de connexion Google NotebookLM expiré (120s).")
            return 124
        except Exception as e:
            ZeroFluffConsole.error(f"Erreur lors de l'exécution de node : {e}")
            return 1

    # 2. Action Status
    if getattr(args, "status", False):
        st = _get_auth_status()
        ZeroFluffConsole.section("ORACLE GOOGLE NOTEBOOKLM - STATUT PASSERELLE")
        ZeroFluffConsole.info(f"Connecté              : {'OUI (Session active)' if st['authenticated'] else 'NON'}")
        ZeroFluffConsole.info(f"Raison                : {st['reason']}")
        ZeroFluffConsole.info(f"Carnet Dédié mLoop    : {st['notebook_id']}")
        ZeroFluffConsole.info(f"URL du Carnet         : {st['notebook_url']}")
        ZeroFluffConsole.info(f"Profil Chrome         : {st['profile_dir']}")
        return 0

    # 3. Action Export / Bundle (par défaut ou si --bundle)
    ZeroFluffConsole.section("EXPORT DOCUMENTAIRE NOTEBOOKLM - BUNDLE SSOT")
    exporter = NotebookLMExporter(root_dir)

    files = exporter.export_framework_bundle()

    # Si un projet actif est ciblé
    proj_name = getattr(args, "project", None)
    if proj_name:
        p_file = exporter.export_project_bundle(proj_name)
        if p_file:
            files.append(p_file)

    ZeroFluffConsole.success(f"\n✅ {len(files)} fichiers générés sous 'storage/notebooklm_export/'.")
    print(f"👉 Ouvrez votre carnet officiel : {NOTEBOOK_URL}")
    print(f"👉 Glissez-déposez simplement le fichier consolidé :")
    print(f"   storage/notebooklm_export/mloop_complete_ssot_bundle.md\n")
    return 0
