"""
mLoop Framework — Pont OCR pour SVG vectorisés (Phase 1, Plan Enforcement
Déterministe du Grounding Visuel & Épistémique).

Encapsule l'invocation des scripts du skill `svg-ocr` :
  1. render_svg.js  (Chromium headless via Playwright global) : SVG -> PNG
  2. ocr_png.ps1    (Windows.Media.Ocr natif)                  : PNG -> texte

Contrat de dégradation gracieuse (OBLIGATOIRE) :
- Ne lève JAMAIS d'exception vers l'appelant. Toute erreur (outil absent,
  timeout, plateforme non-Windows, Playwright non installé, etc.) se traduit
  par un retour `None` — le convertisseur d'ingestion (svg_to_md.py) doit
  alors retomber sur son comportement historique (placeholder).
- Désactivable via la variable d'environnement `MLOOP_SVG_OCR=0` (ex: CI Linux
  sans Chromium/Windows.Media.Ocr).
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Any

SKILL_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "svg-ocr"
RENDER_SCRIPT = SKILL_DIR / "render_svg.js"
OCR_SCRIPT = SKILL_DIR / "ocr_png.ps1"

DEFAULT_RENDER_TIMEOUT_S = 30
DEFAULT_OCR_TIMEOUT_S = 30


def _decode_bytes(raw: Any) -> str:
    """Décode les octets d'un flux de sous-processus avec fallback robuste multi-encodage Windows."""
    if not raw:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, bytes):
        for enc in ("utf-8", "cp850", "cp1252"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                pass
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def is_svg_ocr_enabled() -> bool:
    """MLOOP_SVG_OCR=0 (ou 'false'/'no', insensible à la casse) désactive l'OCR."""
    val = os.environ.get("MLOOP_SVG_OCR", "1").strip().lower()
    return val not in ("0", "false", "no")


def _npm_global_root() -> Optional[str]:
    try:
        proc = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            timeout=15,
            shell=True,
        )
        stdout = _decode_bytes(proc.stdout).strip()
        if proc.returncode == 0 and stdout:
            return stdout
    except Exception:
        pass
    return None


def _render_svg_to_png(svg_path: Path, work_dir: Path) -> Optional[Path]:
    """Rend le SVG en PNG via Chromium headless. Retourne le chemin PNG ou None."""
    if not RENDER_SCRIPT.exists():
        return None

    svg_path = svg_path.resolve()
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if not env.get("NPM_GLOBAL_ROOT"):
        gr = _npm_global_root()
        if gr:
            env["NPM_GLOBAL_ROOT"] = gr

    try:
        proc = subprocess.run(
            [
                "node",
                str(RENDER_SCRIPT),
                "--src",
                str(svg_path.parent),
                "--out",
                str(work_dir),
                "--files",
                svg_path.name,
            ],
            capture_output=True,
            timeout=DEFAULT_RENDER_TIMEOUT_S,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    if proc.returncode != 0:
        return None

    out_png = work_dir / (svg_path.stem + ".png")
    return out_png if out_png.exists() else None


def _ocr_png(png_path: Path) -> Optional[str]:
    """Exécute l'OCR natif Windows sur le PNG. Retourne le texte reconnu ou None."""
    if not OCR_SCRIPT.exists():
        return None

    png_path = png_path.resolve()
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(OCR_SCRIPT),
                "-Files",
                str(png_path),
            ],
            capture_output=True,
            timeout=DEFAULT_OCR_TIMEOUT_S,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    stdout = _decode_bytes(proc.stdout).strip()
    if proc.returncode != 0 or not stdout:
        return None

    return stdout


def ocr_vectorized_svg(
    svg_path: Path, work_dir: Optional[Path] = None
) -> Optional[str]:
    """
    Extrait le texte réel d'un SVG à texte vectorisé (aucune balise <text>/<tspan>)
    via rendu Chromium headless puis OCR natif Windows.

    Args:
        svg_path: chemin du fichier .svg source (Mode 2 / vectorisé confirmé par l'appelant).
        work_dir: répertoire temporaire de travail pour le PNG intermédiaire
                  (par défaut : Temp/opencode/ocr_work, hors workspace versionné).

    Returns:
        Le texte OCR brut (multi-lignes, un fichier), ou `None` en cas d'indisponibilité
        d'un des deux outils, de timeout, ou si `MLOOP_SVG_OCR=0`. Ne lève jamais.
    """
    if not is_svg_ocr_enabled():
        return None

    svg_path = Path(svg_path).resolve()
    if not svg_path.exists():
        return None

    if work_dir is None:
        work_dir = Path(os.environ.get("TEMP", ".")) / "opencode" / "ocr_work"
    work_dir = Path(work_dir).resolve()

    try:
        png_path = _render_svg_to_png(svg_path, work_dir)
        if png_path is None:
            return None
        return _ocr_png(png_path)
    except Exception:
        # Garde-fou ultime : jamais d'exception ne doit remonter au pipeline d'ingestion.
        return None
