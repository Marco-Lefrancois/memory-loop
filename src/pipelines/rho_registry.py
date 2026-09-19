"""
RHO Registry — Registre des hypothèses rejetées et calcul du chemin de l'impact file.
Module satellite de rho_optimizer.py (ADR-0202 — découpage ≤300L).
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

from src.cli import ZeroFluffConsole

logger = logging.getLogger(__name__)


def get_rho_impact_file(project_name: str, scope: str = "project") -> Path:
    """Retourne le chemin du registre des hypothèses rejetées (rho_impact.yaml)."""
    if scope == "global" or project_name == "global":
        return Path("standards") / "rho_impact.yaml"
    return Path("Projects") / project_name / "memory" / "rho_impact.yaml"


def record_rejected_hypothesis(
    project_name: str,
    keyword: str,
    reason: str,
    scope: str = "project",
    score_delta: float = 0.0,
) -> Dict[str, Any]:
    """Consigne une hypothèse ou règle RHO rejetée (WikiSkill Negative Constraints)."""
    target_file = get_rho_impact_file(project_name, scope)
    target_file.parent.mkdir(parents=True, exist_ok=True)

    data: Dict[str, Any] = {"rejected_hypotheses": []}
    if target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {"rejected_hypotheses": []}
                if "rejected_hypotheses" not in data:
                    data["rejected_hypotheses"] = []
        except Exception as exc:
            logger.debug("Erreur lecture rho_impact.yaml, réinitialisation : %s", exc, exc_info=True)
            data = {"rejected_hypotheses": []}

    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "keyword": keyword.lower().strip(),
        "reason": reason.strip(),
        "score_delta": float(score_delta),
        "verdict": "REJECTED",
        "scope": scope,
    }

    # Éviter les doublons stricts
    for existing in data["rejected_hypotheses"]:
        if existing.get("keyword") == entry["keyword"] and existing.get("reason") == entry["reason"]:
            return entry

    data["rejected_hypotheses"].append(entry)

    with open(target_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    ZeroFluffConsole.warning(
        f"Hypothèse RHO rejetée consignée dans {target_file.as_posix()} : '{keyword}' -> {reason}"
    )
    return entry


def get_rejected_hypotheses(project_name: str, scope: str = "project") -> List[Dict[str, Any]]:
    """Retourne la liste des hypothèses rejetées."""
    target_file = get_rho_impact_file(project_name, scope)
    if not target_file.exists():
        return []
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("rejected_hypotheses", [])
    except Exception as exc:
        logger.debug("Erreur lecture rho_impact.yaml dans get_rejected_hypotheses : %s", exc, exc_info=True)
        return []
