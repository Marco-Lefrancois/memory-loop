"""
_critic_api.py — Checks API (F/G) + persistance EvidencePack (MLOOP-172-BE).

Contient :
  - Checks F (Traçabilité Conditionnelle Backend/Fullstack)
  - Check G (Anti-Invention de Routes ADR-0319)
  - Persistance du rapport dans l'EvidencePack

Conforme ADR-0369 : with sur ressources, zéro except pass nu.
Conforme ADR-0202 : <300 L / 15 Ko.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from src.utils.logger import get_logger

logger = get_logger("rubber_duck.critic._critic_api")


@runtime_checkable
class DevilAdvocateCritiqueProtocol(Protocol):
    """Protocol structurel pour DevilAdvocateCritique (injection ADR-0369)."""

    story_id: str
    project_name: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]: ...


# ── Tokens de routes fictives (Check G) ──────────────────────────────────────

_PHANTOM_ROUTE_TOKENS = (
    "dummy",
    "placeholder",
    "test",
    "fake",
    "todo",
    "tbd",
    "example",
)


# ── Extraction de métadonnées du contenu ──────────────────────────────────────


def extract_layer(content: str) -> Optional[str]:
    """Extrait le champ `layer:` du frontmatter YAML."""
    m = re.search(r"^layer:\s*([A-Za-z_-]+)\s*$", content, re.MULTILINE)
    return m.group(1).strip().lower() if m else None


def extract_api_routes(content: str) -> List[str]:
    """Extrait les routes API mentionnées (Markdown table, liste, inline code)."""
    routes: set[str] = set()
    # Table markdown : | `METHOD` | `/route` | ...
    for m in re.finditer(r"`(GET|POST|PUT|PATCH|DELETE)`\s*\|\s*`(/[^\s`]+)`", content):
        routes.add(f"{m.group(1)} {m.group(2)}")
    # Liste / inline : `GET /api/...` ou **Endpoint** : `POST /api/dummy`
    for m in re.finditer(r"`(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s`]+)`", content):
        routes.add(f"{m.group(1)} {m.group(2)}")
    return sorted(routes)


def has_contract_matrix(content: str) -> bool:
    """Une Matrice des Contrats API est présente si un tableau de routes existe."""
    return bool(extract_api_routes(content))


def has_oq_exemption(content: str) -> bool:
    """Clause d'exemption : question ouverte OQ-XXX/OQ-XXXX + mention déclarative (L-09)."""
    has_oq = bool(re.search(r"\bOQ-\d{3,4}\b", content))
    has_deferred_marker = "[API de soumission à définir]" in content or bool(
        re.search(r"à confirmer|à définir", content, re.IGNORECASE)
    )
    return has_oq and has_deferred_marker


# ── Check F/G principal ───────────────────────────────────────────────────────


def run_api_traceability_checks(
    content: str, critical_flaws: List[str], silent_failures: List[str]
) -> None:
    """
    Check F (Traçabilité Conditionnelle Backend/Fullstack) & Check G
    (Anti-Invention de Routes ADR-0319).

    Se déclenche uniquement si le frontmatter porte un champ `layer:`.
    """
    layer = extract_layer(content)
    if layer is None:
        return

    routes = extract_api_routes(content)
    phantom_routes = [r for r in routes if any(tok in r.lower() for tok in _PHANTOM_ROUTE_TOKENS)]

    # Check G : Anti-Invention de Routes (priorité sur Check F)
    if phantom_routes:
        critical_flaws.append(
            f"[ADR-0319] Route(s) API fictive(s)/placeholder détectée(s) : "
            f"{', '.join(phantom_routes)}. Zéro Fausse Route (AGENTS.md) : "
            f"toute route API inconnue doit être consignée en question ouverte "
            f"(OQ-XXX) avec la mention déclarative '[API de soumission à définir]', "
            f"jamais inventée."
        )
        return

    # Check F : Traçabilité Conditionnelle (uniquement backend/fullstack)
    if layer not in ("backend", "fullstack"):
        return

    if has_contract_matrix(content):
        return  # F2 / F4 : matrice présente

    if has_oq_exemption(content):
        silent_failures.append(
            f"[ADR-0319] Récit layer:{layer} sans Matrice des Contrats API, "
            f"mais couvert par une question ouverte de traçabilité — route à "
            f"confirmer avant passage en développement."
        )
        return

    # F1 : ni matrice, ni exemption OQ → BLOCKING
    critical_flaws.append(
        f"[ADR-0319] Récit layer:{layer} sans Matrice des Contrats API "
        f"(section '#### Matrice des Contrats API') ni clause d'exemption "
        f"OQ-XXX. Toute route API doit être déclarée explicitement ou "
        f"consignée en question ouverte (Zéro Fausse Route, AGENTS.md)."
    )


# ── Persistance EvidencePack ──────────────────────────────────────────────────


def persist_critique_to_evidence(
    critique: "DevilAdvocateCritiqueProtocol", project_dir: Path
) -> None:
    """Injecte le rapport de l'Avocat du Diable dans l'EvidencePack du récit."""
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / f"{critique.story_id}_evidence.json"

    evidence_data: dict = {}
    if evidence_file.exists():
        try:
            with open(evidence_file, encoding="utf-8") as f:
                evidence_data = json.load(f)
        except Exception as exc:
            logger.debug(
                "Lecture EvidencePack impossible pour %s.",
                evidence_file,
                exc_info=True,
                extra={"evidence_file": str(evidence_file), "error": str(exc)},
            )
            evidence_data = {}

    evidence_data["story_id"] = critique.story_id
    evidence_data["project_name"] = critique.project_name
    evidence_data["last_updated"] = critique.timestamp
    evidence_data["devil_advocate_review"] = critique.to_dict()

    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, indent=2, ensure_ascii=False)

    logger.info(
        "Rapport Avocat du Diable consigné dans %s",
        evidence_file,
        extra={"evidence_file": str(evidence_file), "story_id": critique.story_id},
    )
