"""
Préservation des champs immuables d'un EvidencePack lors de sa régénération
(MLOOP-181-BE / CA-1, CA-2, CA-4 et Gate 3 ADR-0381).

Le harnais Phase 3 (tournoi, cycle TDD, contrats, citations) écrit ses captures
directement dans `<SID>_evidence.json`. `EvidencePackEngine.extract_evidence()`
reconstruit le pack à chaque `sync` : sans préservation, les captures et le sceau
Red/Green `tdd_cycle` seraient écrasés à chaque synchronisation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.utils.logger import get_logger

logger = get_logger("pipelines.pack_preserver")

#: Champs de parité et traçabilité qui doivent survivre à la régénération (ADR-0394).
PRESERVED_LIST_FIELDS = (
    "verbatim_extracts",
    "implementation_decisions",
    "declarative_contracts",
    "conflict_matrix",
    "code_traceability_matrix",
)

#: Sceau cryptographique TDD (ADR-0381) — dict {red, green}.
PRESERVED_OBJECT_FIELDS = ("tdd_cycle",)


def load_preserved_fields(existing_pack_path: Path) -> Dict[str, Any]:
    """
    Charge depuis le pack existant les champs qui doivent survivre à la régénération.

    Pack absent, illisible ou champs vides -> structures par défaut
    (rétrocompat MLOOP-180-BE CA-5 : listes vides, tdd_cycle None).

    ADR-0369 : aucun swallow silencieux — un pack corrompu est loggé en DEBUG
    contextualisé avant de retomber sur les défauts.
    """
    preserved: Dict[str, Any] = {field: [] for field in PRESERVED_LIST_FIELDS}
    preserved.update({field: None for field in PRESERVED_OBJECT_FIELDS})

    path = Path(existing_pack_path)
    if not path.exists():
        return preserved

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.debug(
            "EvidencePack existant illisible, préservation neutralisée (défauts vides)",
            exc_info=True,
            extra={
                "component": "pipelines.pack_preserver",
                "operation": "load_preserved_fields",
                "path": str(path),
            },
        )
        return preserved

    for field in PRESERVED_LIST_FIELDS:
        value = data.get(field)
        if isinstance(value, list) and value:
            preserved[field] = value
    for field in PRESERVED_OBJECT_FIELDS:
        value = data.get(field)
        if isinstance(value, dict) and value:
            preserved[field] = value
    return preserved
