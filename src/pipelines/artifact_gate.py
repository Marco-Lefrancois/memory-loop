"""
Porte Déterministe d'Artefacts & Anti-Raster Paste (MLOOP-300-BE / EPIC-30).

Implémente une porte de validation binaire g(P) ∈ {0, 1} certifiant l'intégrité
des livrables visuels (SVG, HTML, Canvas JSON) avant toute consommation de jetons
par un juge ou relecteur LLM (frugalité d'inférence).

Contrôles déterministes :
  - Openability : bonne formation syntaxique XML/SVG (parsing sécurisé defusedxml).
  - Anti-Raster Paste : ratio de surface matricielle (<image>, data-URI base64)
    vs viewBox global. Rejet si raster > 80 % ET < 3 éléments vectoriels.
  - Résilience : tout fichier corrompu/tronqué renvoie is_valid=False sans crash.

Motifs standardisés : ARTIFACT_CONFORME, RASTER_PASTE_DETECTED, CORRUPT_ARTIFACT.

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, context managers, logging structuré,
zéro except pass nu). Référence scientifique : ReFigBench (arXiv:2609.18844, §3).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from defusedxml.ElementTree import fromstring as safe_fromstring
from defusedxml.common import DefusedXmlException

from src.utils.logger import get_logger

logger = get_logger("pipelines.artifact_gate")

# Seuils déterministes (Règles d'affaires MLOOP-300-BE).
RASTER_RATIO_THRESHOLD: float = 0.80
MIN_VECTOR_ELEMENTS: int = 3

# Motifs de résultat standardisés.
REASON_CONFORME = "ARTIFACT_CONFORME"
REASON_RASTER_PASTE = "RASTER_PASTE_DETECTED"
REASON_CORRUPT = "CORRUPT_ARTIFACT"

_SUPPORTED_SUFFIXES = {".svg", ".html", ".json", ".canvas"}

# Éléments géométriques vectoriels éditables reconnus.
_VECTOR_TAGS = {"path", "rect", "circle", "line", "polygon", "polyline", "ellipse"}
# Éléments matriciels (bitmap incrusté).
_RASTER_TAGS = {"image"}

_NS_RE = re.compile(r"\{.*\}")
_NUM_RE = re.compile(r"[-+]?\d*\.?\d+")


@dataclass
class ArtifactGateResult:
    """Résultat déterministe de la porte d'artefact (contrat gelé MLOOP-300-BE)."""

    is_valid: bool
    reason: str
    raster_ratio: float = 0.0
    vector_elements_count: int = 0
    checksum: str = ""
    details: dict = field(default_factory=dict)


def _strip_ns(tag: str) -> str:
    """Retire l'espace de noms XML d'une balise ({http://...}rect -> rect)."""
    return _NS_RE.sub("", tag).lower()


def _compute_checksum(file_path: Path) -> str:
    """Calcule l'empreinte SHA-256 du contenu binaire du fichier."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _parse_length(raw: str | None) -> float:
    """Extrait la première valeur numérique d'une dimension SVG (px, %, unités)."""
    if not raw:
        return 0.0
    match = _NUM_RE.search(str(raw))
    return float(match.group()) if match else 0.0


def _canvas_area(root) -> float:
    """Calcule l'aire de référence du canvas via viewBox ou width/height."""
    view_box = root.get("viewBox")
    if view_box:
        parts = _NUM_RE.findall(view_box)
        if len(parts) == 4:
            width, height = abs(float(parts[2])), abs(float(parts[3]))
            if width > 0 and height > 0:
                return width * height
    width = _parse_length(root.get("width"))
    height = _parse_length(root.get("height"))
    return width * height


def _image_area(element) -> float:
    """Aire déclarée d'un élément <image> (width * height)."""
    return _parse_length(element.get("width")) * _parse_length(element.get("height"))


def _scan_geometry(root) -> tuple[float, int, float]:
    """Parcourt l'arbre XML et agrège aire raster, compte vectoriel et aire canvas."""
    canvas_area = _canvas_area(root)
    raster_area = 0.0
    vector_count = 0
    for element in root.iter():
        tag = _strip_ns(element.tag)
        if tag in _RASTER_TAGS:
            raster_area += _image_area(element)
        elif tag in _VECTOR_TAGS:
            vector_count += 1
    return raster_area, vector_count, canvas_area


def _evaluate_svg(text: str, checksum: str) -> ArtifactGateResult:
    """Évalue un document SVG/XML : parsing sécurisé puis géométrie anti-raster."""
    try:
        root = safe_fromstring(text)
    except (DefusedXmlException, SyntaxError, ValueError) as exc:
        logger.debug(
            "Artefact SVG/XML mal formé rejeté proprement.",
            exc_info=True,
            extra={
                "check_name": "artifact_gate",
                "violation_type": "corrupt_xml",
                "error": str(exc),
            },
        )
        return ArtifactGateResult(False, REASON_CORRUPT, checksum=checksum)

    raster_area, vector_count, canvas_area = _scan_geometry(root)
    raster_ratio = round(raster_area / canvas_area, 4) if canvas_area > 0 else 0.0

    is_raster_paste = raster_ratio > RASTER_RATIO_THRESHOLD and vector_count < MIN_VECTOR_ELEMENTS
    reason = REASON_RASTER_PASTE if is_raster_paste else REASON_CONFORME

    result = ArtifactGateResult(
        is_valid=not is_raster_paste,
        reason=reason,
        raster_ratio=raster_ratio,
        vector_elements_count=vector_count,
        checksum=checksum,
        details={"canvas_area": canvas_area, "raster_area": round(raster_area, 2)},
    )
    logger.debug(
        "Évaluation géométrique de l'artefact SVG achevée.",
        extra={
            "check_name": "artifact_gate",
            "reason": reason,
            "raster_ratio": raster_ratio,
            "vector_elements_count": vector_count,
            "checksum": checksum,
        },
    )
    return result


def _evaluate_json(text: str, checksum: str) -> ArtifactGateResult:
    """Évalue un artefact JSON/Canvas : bonne formation JSON suffit (openability)."""
    import json

    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.debug(
            "Artefact JSON/Canvas mal formé rejeté proprement.",
            exc_info=True,
            extra={
                "check_name": "artifact_gate",
                "violation_type": "corrupt_json",
                "error": str(exc),
            },
        )
        return ArtifactGateResult(False, REASON_CORRUPT, checksum=checksum)

    node_like = payload.get("nodes", []) if isinstance(payload, dict) else []
    return ArtifactGateResult(
        is_valid=True,
        reason=REASON_CONFORME,
        raster_ratio=0.0,
        vector_elements_count=len(node_like) if isinstance(node_like, list) else 0,
        checksum=checksum,
    )


def evaluate_artifact_gate(file_path: Path) -> ArtifactGateResult:
    """
    Porte déterministe g(P) ∈ {0, 1} d'intégrité d'un artefact visuel.

    Args:
        file_path: Chemin du fichier d'artefact (.svg, .html, .json, .canvas).

    Returns:
        ArtifactGateResult : verdict binaire, motif, ratio raster, compte vectoriel,
        empreinte SHA-256. Ne lève jamais d'exception non gérée (Zero Crash Policy).
    """
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        logger.debug(
            "Artefact introuvable ou non-fichier.",
            extra={
                "check_name": "artifact_gate",
                "violation_type": "missing_file",
                "file_path": str(path),
            },
        )
        return ArtifactGateResult(False, REASON_CORRUPT)

    if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
        logger.debug(
            "Extension d'artefact non reconnue.",
            extra={
                "check_name": "artifact_gate",
                "violation_type": "unsupported_suffix",
                "file_path": str(path),
            },
        )
        return ArtifactGateResult(False, REASON_CORRUPT)

    try:
        checksum = _compute_checksum(path)
        text = path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as exc:
        logger.debug(
            "Lecture de l'artefact impossible (I/O ou encodage).",
            exc_info=True,
            extra={
                "check_name": "artifact_gate",
                "violation_type": "io_error",
                "file_path": str(path),
                "error": str(exc),
            },
        )
        return ArtifactGateResult(False, REASON_CORRUPT)

    if not text.strip():
        return ArtifactGateResult(False, REASON_CORRUPT, checksum=checksum)

    suffix = path.suffix.lower()
    if suffix in {".json", ".canvas"}:
        return _evaluate_json(text, checksum)
    return _evaluate_svg(text, checksum)


__all__ = ["evaluate_artifact_gate", "ArtifactGateResult"]
