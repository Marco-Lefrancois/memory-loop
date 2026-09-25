"""
mLoop Gate 4 Validator - Contrôles Bloquants Déterministes de Recette QA (ADR-0383 / MLOOP-092-BE).
Évalue les 5 conditions d'inviolabilité avant d'autoriser la transition vers STAGE_5_SHIP.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (Python Senior).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("core.gate4_validator")

BOT_DISALLOWED_NAMES = frozenset({"ai", "bot", "sentinel", "swarm", "subagent", "agent", "robot"})
HUMAN_KEYWORDS = ("marco", "lead", "architect", "human", "owner", "admin")

# Message canonique du Contrôle 5 — conservé à l'identique pour la Gate 4 (0 régression).
_GATE4_HUMAN_REQUIREMENT = (
    "la Gate 4 exige obligatoirement une signature humaine formelle "
    "(ex: approver='Marco' ou 'Lead Architect')."
)


def validate_human_authority(
    approver: str,
    context: str = "Approbation de Gate 4",
    requirement: str = _GATE4_HUMAN_REQUIREMENT,
) -> str:
    """
    Contrôle 5 (extrait — opération 2 MLOOP-270-BE) : exige une signature
    humaine formelle et rejette les identifiants machine.

    Réutilisé par `story-approve` pour qualifier un approbateur **sans** exiger
    le rapport QA (la Gate 4 garde son propre contexte par défaut).

    Returns:
        L'approbateur nettoyé (stripped, casing d'origine conservé).

    Raises:
        ValueError : nom vide, ou identifiant machine sans mention humaine.
    """
    approver_clean = (approver or "").strip().lower()
    is_bot_only = approver_clean in BOT_DISALLOWED_NAMES
    has_human = any(h in approver_clean for h in HUMAN_KEYWORDS)
    if not approver_clean or (is_bot_only and not has_human):
        raise ValueError(f"{context} refusée : {requirement}")
    return (approver or "").strip()


def validate_gate4_approval(project_path: Path, approver: str) -> Dict[str, Any]:
    """
    Vérifie les 5 contrôles bloquants déterministes avant de permettre la validation de Gate 4.
    Lève un ValueError explicite si l'un des critères est violé.
    """
    proj_name = project_path.name
    qa_report_file = project_path / "memory" / "qa_certification_report.json"
    if (
        not qa_report_file.exists()
        and (Path("Projects") / proj_name / "memory" / "qa_certification_report.json").exists()
    ):
        qa_report_file = Path("Projects") / proj_name / "memory" / "qa_certification_report.json"

    # Contrôle 1 : Présence physique et intégrité du rapport de certification QA
    if not qa_report_file.exists():
        raise ValueError(
            f"Approbation de Gate 4 refusée : aucun rapport de certification QA "
            f"n'a été trouvé sous memory/qa_certification_report.json pour '{proj_name}'. "
            f"Lancez 'python src/swarm.py validate-sprint --project {proj_name}' avant d'approuver la Gate 4."
        )

    try:
        with open(qa_report_file, "r", encoding="utf-8") as f:
            qa_data = json.load(f)
    except Exception as exc:
        raise ValueError(
            f"Approbation de Gate 4 refusée : rapport QA corrompu ou illisible : {exc}"
        )

    # Contrôle 2 : Tests pytest 100% au vert
    py_res = qa_data.get("pytest_result", {})
    py_passed = py_res.get("all_passed", False) or qa_data.get("pytest_all_passed", False)
    if not py_passed:
        failed_cnt = py_res.get("failed_tests", 1)
        raise ValueError(
            f"Approbation de Gate 4 refusée : la suite de tests comporte {failed_cnt} échec(s). "
            f"La Gate 4 exige 100% de tests au vert."
        )

    # Contrôle 3 : Audit statique AST (0 violation ADR-0202 et ADR-0369)
    ast_sum = qa_data.get("ast_summary", {})
    ast_violations = ast_sum.get("total_violations", 0)
    if ast_violations > 0 or not ast_sum.get("passed", True):
        raise ValueError(
            f"Approbation de Gate 4 refusée : {ast_violations} violations de standards AST "
            f"(ADR-0202 / ADR-0369) détectées."
        )

    # Contrôle 4 : Triangulation Code Evidence Ledger (4 Piliers Gherkin complets)
    cel_res = qa_data.get("cel_result", {})
    if not cel_res.get("is_complete", False):
        missing_p = cel_res.get("missing_pillars", [])
        raise ValueError(
            f"Approbation de Gate 4 refusée : le Code Evidence Ledger présente des angles morts "
            f"sur les 4 Piliers Gherkin : {missing_p}."
        )

    # Contrôle 5 : Signature humaine formelle obligatoire (rejet des bots/agents)
    validate_human_authority(approver)

    return qa_data
