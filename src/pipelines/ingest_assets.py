"""
ingest_assets.py - Asset processing logic for Ingest Agent (ADR-0202 <=300L).

Extracted from ingest_agent.py to comply with modular ceiling.
"""

import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger
from src.state import ProjectLayout

logger = get_logger("ingest_assets")


def compute_sha256(filepath: Path) -> Optional[str]:
    """Compute SHA-256 hash of file content."""
    try:
        file_content_raw = filepath.read_bytes()
        return hashlib.sha256(file_content_raw).hexdigest()
    except Exception as e:
        ZeroFluffConsole.error(f"Impossible de lire le fichier {filepath.name} : {e}")
        return None


def process_svg_asset(filepath: Path, state, initiative: Optional[str] = None) -> str:
    """Process SVG file: sync to assets and generate Markdown note."""
    try:
        rel_parent = filepath.parent.name
        if initiative:
            target_assets = Path("Projects") / "mLoop" / "docs" / initiative / "05-assets"
        else:
            target_assets = Path("Projects") / "mLoop" / "docs" / "05-assets"
        if filepath.parent.name in ["01-reception", "02-incubation", "03-ventes"]:
            target_assets = target_assets / filepath.parent.name
        target_assets.mkdir(parents=True, exist_ok=True)
        target_svg = target_assets / filepath.name
        if not target_svg.exists() or target_svg.resolve() != filepath.resolve():
            shutil.copy2(filepath, target_svg)

        return f"# 🖼️ Capture / Maquette : {filepath.stem}\n\n![{filepath.stem}](../05-assets/{filepath.parent.name}/{filepath.name})\n\n- **Fichier source** : `{filepath.name}`\n- **Module associé** : `{filepath.parent.name}`\n"
    except Exception as e:
        return f"[Erreur lors du traitement de l'image ({filepath.name}) : {e}]"


def process_image_asset(filepath: Path, state, initiative: Optional[str] = None) -> str:
    """Sync image to docs/05-assets/ and generate artifact note."""
    try:
        rel_parent = filepath.parent.name
        if initiative:
            target_assets = Path("Projects") / "mLoop" / "docs" / initiative / "05-assets"
        else:
            target_assets = Path("Projects") / "mLoop" / "docs" / "05-assets"
        if filepath.parent.name in ["01-reception", "02-incubation", "03-ventes"]:
            target_assets = target_assets / filepath.parent.name
        target_assets.mkdir(parents=True, exist_ok=True)
        target_img = target_assets / filepath.name
        shutil.copy2(filepath, target_img)

        return f"# 🖼️ Capture / Maquette : {filepath.stem}\n\n![{filepath.stem}](../05-assets/{filepath.parent.name}/{filepath.name})\n\n- **Fichier source** : `{filepath.name}`\n- **Module associé** : `{filepath.parent.name}`\n"
    except Exception as e:
        return f"[Erreur lors du traitement de l'image ({filepath.name}) : {e}]"


def sync_svg_asset(filepath: Path, state, initiative: Optional[str] = None) -> None:
    """Sync SVG asset to docs/05-assets/maquettes/ (ADR-0332)."""
    try:
        if initiative:
            assets_maquettes = (
                Path("Projects") / "mLoop" / "docs" / initiative / "05-assets" / "maquettes"
            )
        else:
            assets_maquettes = Path("Projects") / "mLoop" / "docs" / "05-assets" / "maquettes"
        assets_maquettes.mkdir(parents=True, exist_ok=True)
        target_svg = assets_maquettes / filepath.name
        if not target_svg.exists() or target_svg.resolve() != filepath.resolve():
            shutil.copy2(filepath, target_svg)
    except Exception as e:
        ZeroFluffConsole.warning(f"Impossible de synchroniser l'actif SVG {filepath.name} : {e}")
