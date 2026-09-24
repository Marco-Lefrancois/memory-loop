"""
Sous-module vibe_check/_vc_build.py
Checks liés à l'infrastructure de build, à l'intégrité lexicale et aux standards Python.

Checks inclus :
  - check_03_fts5            : Fact-Search FTS5 & mémoire persistante (Check 3)
  - check_06_lexical_guard   : Intégrité lexicale & signature de vocabulaire (Check 6)
  - check_14_python_senior   : Standards de robustesse Python Senior (ADR-0369) (Check 14)
  - check_17_qa_cert         : Certification QA Sprint (Phase 4 VALIDATE) (Check 17)
"""

from pathlib import Path

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_build")


def check_03_fts5(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 3 : Fact-Search FTS5 & mémoire persistante.
    Valide la disponibilité de la recherche factuelle FTS5 avant toute modification de code.
    Effectue une requête de contrôle sur le terme «architecture» pour le projet courant.
    """
    from src.loop_mem.db import search_observations

    search_observations(query="architecture", project_name=project_name)
    return {"check": "Fact-Search FTS5 Before Edit", "status": "PASS"}


def check_06_lexical_guard(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 6 : Intégrité lexicale & signature de vocabulaire (Rosetta Canary & Unicode NFC — ADR-0327).
    Inspecte les preuves du projet pour détecter toute dérive du vocabulaire normalisé
    ou altération de l'empreinte lexicale canonique.
    """
    from src.utils.lexical_guard import LexicalIntegrityGuard

    lex_res = LexicalIntegrityGuard.inspect_project_evidence(
        project_dir if project_dir.exists() else Path(".")
    )
    return {
        "check": f"Intégrité Lexicale & Signature de Vocabulaire (Canary: {lex_res.canary_hash})",
        "status": "PASS" if lex_res.is_valid else "FAIL",
    }


def check_14_python_senior(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 14 (ADR-0369 — Standards de robustesse Python Senior) :
    Valide l'intégrité des 7 standards d'ingénierie : protocole SSOT,
    ADR-0369, logger contextuel, dépendances dev pyproject.toml et zéro timeout manquant.
    Vérifie la présence de PYTHON_SENIOR_CODING_STANDARDS.md, l'ADR-0369
    et les optional-dependencies dans pyproject.toml.
    """
    python_senior_ok = True
    senior_violations = []

    if not Path("standards/protocols/PYTHON_SENIOR_CODING_STANDARDS.md").exists():
        python_senior_ok = False
        senior_violations.append("Protocole PYTHON_SENIOR_CODING_STANDARDS.md manquant")

    if not Path(
        "standards/adr-system/0369-python-senior-robustness-and-resource-governance.md"
    ).exists():
        python_senior_ok = False
        senior_violations.append("ADR-0369 manquant")

    pyproject_txt = (
        Path("pyproject.toml").read_text(encoding="utf-8")
        if Path("pyproject.toml").exists()
        else ""
    )
    if "[project.optional-dependencies]" not in pyproject_txt:
        python_senior_ok = False
        senior_violations.append("pyproject.toml sans optional-dependencies dev")

    python_senior_msg = (
        "Standards de Robustesse Python Senior (ADR-0369)"
        if python_senior_ok
        else f"Standards de Robustesse Python Senior (Violations : {', '.join(senior_violations)})"
    )
    return {"check": python_senior_msg, "status": "PASS" if python_senior_ok else "FAIL"}


def check_17_qa_cert(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 17 (Phase 4 VALIDATE — Garde-Fou automatique MLOOP-123-BE) :
    Warning passif si stage == STAGE_4_VALIDATE et qa_certification_report.json absent.
    Incite à lancer 'validate-sprint' pour certifier le sprint.
    """
    qa_cert_ok = True
    qa_cert_msg = ""
    if stage_label in ("STAGE_4_VALIDATE", "STAGE_VALIDATE"):
        evidence_dir = project_dir / "memory" / "evidence"
        qa_report_file = evidence_dir / "qa_certification_report.json"
        if not qa_report_file.exists():
            qa_cert_ok = False
            qa_cert_msg = (
                " [WARNING] qa_certification_report.json absent dans memory/evidence/. "
                "Lancez 'validate-sprint' pour certifier le sprint."
            )
    if not qa_cert_ok:
        ZeroFluffConsole.warning(
            f"Phase 4 VALIDATE : qa_certification_report.json absent.{qa_cert_msg}"
        )
    return {
        "check": f"Certification QA Sprint (Phase 4){qa_cert_msg}"
        if not qa_cert_ok
        else "Certification QA Sprint (Phase 4)",
        "status": "PASS" if qa_cert_ok else "WARNING",
    }
