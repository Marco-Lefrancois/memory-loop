"""
Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture (MLOOP-302-BE / EPIC-30).

Découpe et ancre chaque schéma d'architecture extrait à l'aide de sa légende
contextuelle (*caption*) et des paragraphes du texte qui le référencent
(algorithme ORBIT — Caption Harvesting), éliminant les extractions d'images
orphelines sans sémantique et préservant la fenêtre de contexte des agents avals.

Traitement :
  - Détection des légendes (Figure N, Diagramme N, Schéma : ...) par regex.
  - Recherche des paragraphes d'appel (cf. Figure X, comme illustré Figure X).
  - Fiche d'ancrage JSON liant figure / légende / contextes, scellée par SHA-256.
  - Filtrage des images décoratives (sans légende ni référence) => DECORATIVE_FIGURE_SKIPPED.

Conforme ADR-0202 (≤ 300L), ADR-0369 (typage, logging structuré, zéro except pass nu).
Référence scientifique : ReFigBench (arXiv:2609.18844, Algorithme ORBIT).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines.orbit_caption_harvester")

STATUS_ANCHORED = "FIGURE_ANCHORED"
STATUS_DECORATIVE = "DECORATIVE_FIGURE_SKIPPED"

# Nombre de phrases amont/aval conservées autour d'une référence (ORBIT window).
CONTEXT_SENTENCE_WINDOW: int = 3

# Détection de légende : « Figure 3 : ... », « Diagramme 2 - ... », « Schéma : ... ».
_CAPTION_RE = re.compile(
    r"(?P<kind>Figure|Diagramme|Sch[ée]ma)\s*(?P<num>\d+)?\s*[:\-–]\s*(?P<label>.+)",
    re.IGNORECASE,
)

# Détection d'appel textuel : « cf. Figure 3 », « comme illustré sur la Figure 3 », « voir Diagramme 2 ».
_REFERENCE_RE = re.compile(
    r"(?:cf\.?|voir|comme illustr[ée].*?|selon)\s+(?:la\s+|le\s+)?"
    r"(?P<kind>Figure|Diagramme|Sch[ée]ma)\s*(?P<num>\d+)",
    re.IGNORECASE,
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _sha256_text(payload: str) -> str:
    """Empreinte SHA-256 déterministe d'une chaîne (UTF-8)."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_figure_ref(kind: str, num) -> str:
    """Normalise une référence de figure en clé canonique (ex: 'figure_3')."""
    base = "figure"
    kind_lower = (kind or "").lower()
    if kind_lower.startswith("diagramme"):
        base = "diagramme"
    elif kind_lower.startswith("sch"):
        base = "schema"
    return f"{base}_{num}" if num is not None and str(num) != "" else base


def _extract_caption(figure: dict, text: str) -> tuple[str | None, str | None]:
    """Extrait la légende d'une figure depuis son champ dédié ou le texte adjacent."""
    explicit = figure.get("caption")
    if explicit and str(explicit).strip():
        match = _CAPTION_RE.search(str(explicit))
        if match:
            return match.group("label").strip(), _normalize_figure_ref(
                match.group("kind"), match.group("num")
            )
        return str(explicit).strip(), None

    figure_id = figure.get("id")
    if figure_id:
        for line in text.splitlines():
            if str(figure_id) in line:
                match = _CAPTION_RE.search(line)
                if match:
                    return match.group("label").strip(), _normalize_figure_ref(
                        match.group("kind"), match.group("num")
                    )
    return None, None


def _find_calling_paragraphs(text: str, figure_ref: str | None) -> list[str]:
    """Repère les phrases d'appel citant explicitement la figure (contextes distincts)."""
    if not figure_ref:
        return []
    contexts: list[str] = []
    seen: set[str] = set()
    sentences = _SENTENCE_SPLIT_RE.split(text)
    for idx, sentence in enumerate(sentences):
        ref_match = _REFERENCE_RE.search(sentence)
        if not ref_match:
            continue
        candidate_ref = _normalize_figure_ref(ref_match.group("kind"), ref_match.group("num"))
        if candidate_ref != figure_ref:
            continue
        start = max(0, idx - 1)
        end = min(len(sentences), idx + CONTEXT_SENTENCE_WINDOW - 1)
        block = " ".join(s.strip() for s in sentences[start:end] if s.strip())
        if block and block not in seen:
            seen.add(block)
            contexts.append(block)
    return contexts


def _build_anchor_card(
    figure: dict, caption: str, figure_ref: str | None, contexts: list[str]
) -> dict:
    """Construit la fiche d'ancrage JSON scellée par SHA-256."""
    figure_id = str(figure.get("id", figure_ref or "unknown"))
    seal_payload = f"{figure_id}|{caption}|{'|'.join(contexts)}"
    return {
        "figure_id": figure_id,
        "figure_ref": figure_ref,
        "caption": caption,
        "calling_contexts": contexts,
        "context_count": len(contexts),
        "status": STATUS_ANCHORED,
        "sha256": _sha256_text(seal_payload),
        "source_ref": figure.get("source_ref"),
    }


def harvest_orbit_figures(doc_path: Path, figures: list) -> list[dict]:
    """
    Moisson contextuelle ORBIT des légendes et figures d'un document technique.

    Args:
        doc_path: Chemin du document source ingéré (docs/00-ingested/).
        figures: Liste des figures candidates (dict avec `id`, `caption`, `decorative`).

    Returns:
        list[dict] : fiches d'ancrage des figures directrices (status FIGURE_ANCHORED)
        et fiches minimales des images décoratives écartées (DECORATIVE_FIGURE_SKIPPED).
        Ne lève jamais d'exception non gérée (Zero Crash Policy).
    """
    path = Path(doc_path)
    text = ""
    if path.exists() and path.is_file():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.debug(
                "Lecture du document source ORBIT impossible.",
                exc_info=True,
                extra={
                    "check_name": "orbit_harvester",
                    "violation_type": "io_error",
                    "file_path": str(path),
                    "error": str(exc),
                },
            )

    figures = figures if isinstance(figures, list) else []
    cards: list[dict] = []
    anchored = 0
    skipped = 0

    for figure in figures:
        if not isinstance(figure, dict):
            skipped += 1
            continue

        caption, figure_ref = _extract_caption(figure, text)
        contexts = _find_calling_paragraphs(text, figure_ref)
        is_decorative_flag = bool(figure.get("decorative", False))

        # Image décorative : aucun ancrage sémantique (ni légende ni référence).
        if is_decorative_flag or (not caption and not contexts):
            skipped += 1
            cards.append(
                {
                    "figure_id": str(figure.get("id", "unknown")),
                    "status": STATUS_DECORATIVE,
                    "caption": caption,
                    "calling_contexts": [],
                }
            )
            continue

        anchored += 1
        cards.append(_build_anchor_card(figure, caption or "", figure_ref, contexts))

    logger.debug(
        "Moisson ORBIT achevée.",
        extra={
            "check_name": "orbit_harvester",
            "document": str(path),
            "anchored_figures": anchored,
            "decorative_skipped": skipped,
        },
    )
    return cards


__all__ = ["harvest_orbit_figures", "STATUS_ANCHORED", "STATUS_DECORATIVE"]
