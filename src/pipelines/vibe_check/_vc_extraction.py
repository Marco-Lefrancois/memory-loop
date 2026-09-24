"""
Sous-module vibe_check/_vc_extraction.py — Check 22 : Protocole d'Extraction Modulaire.

Checks inclus :
  - check_22_extraction_protocol : conformité au protocole MLOOP-172-BE (ADR-0202 Phase 3)

Règle Phase 3 BUILD :
    Si le working tree modifie un fichier déjà en dépassement RULE-AST-01
    OU un package d'extraction en cours :
      - FAIL si plan d'extraction absent ET fumée non exécutable/rouge
      - WARNING si plan présent mais fumée non exécutée, ou plan absent mais fichiers conformes
      - PASS si plan présent ET fumée verte (ou aucune modification en dépassement)

Conforme ADR-0369 : timeout=, with, zéro except pass nu.
Conforme ADR-0202 : <300 L / 15 Ko.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_extraction")

# ── Constantes ────────────────────────────────────────────────────────────────

_PLAN_GLOB = "implementation_plan_*extraction*"
_SMOKE_MODULE = "src.pipelines.import_smoke_check"
_SMOKE_TIMEOUT = 30  # secondes
_AST_LIMIT_LINES = 300
_GIT_TIMEOUT = 10  # secondes


# ── Helpers internes ──────────────────────────────────────────────────────────


def _get_staged_files() -> list[str]:
    """Retourne la liste des fichiers Python stagés dans le working tree Git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached", "--diff-filter=AM"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".py")]
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug(
            "git diff indisponible (fallback : zéro fichier stagé).",
            exc_info=True,
            extra={"error": str(exc)},
        )
        return []


def _count_lines(file_path: str) -> int:
    """Compte les lignes d'un fichier Python (HEAD ou working tree)."""
    p = Path(file_path)
    if not p.exists():
        return 0
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except Exception as exc:
        logger.debug(
            "Lecture impossible de %s.",
            file_path,
            exc_info=True,
            extra={"file": file_path, "error": str(exc)},
        )
        return 0


def _has_extraction_plan(plan_dir: Path) -> bool:
    """Vérifie la présence d'un plan d'extraction archivé dans memory/plan/."""
    if not plan_dir.exists():
        return False
    return any(plan_dir.glob(_PLAN_GLOB))


def _run_smoke_check(module_path: str) -> tuple[bool, str]:
    """
    Exécute le check de fumée pour un module donné.

    Returns:
        (success, message)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", _SMOKE_MODULE, "--module", module_path],
            capture_output=True,
            text=True,
            timeout=_SMOKE_TIMEOUT,
        )
        success = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        return success, output
    except FileNotFoundError as exc:
        logger.debug(
            "Module import_smoke_check introuvable.",
            exc_info=True,
            extra={"error": str(exc)},
        )
        return False, f"Module {_SMOKE_MODULE!r} introuvable : {exc}"
    except subprocess.TimeoutExpired:
        logger.warning(
            "Timeout check fumée pour %r.",
            module_path,
            extra={"smoke_module": module_path, "timeout_s": _SMOKE_TIMEOUT},
        )
        return False, f"Timeout ({_SMOKE_TIMEOUT}s) lors du check fumée pour {module_path!r}"


# ── Check principal ───────────────────────────────────────────────────────────


def check_22_extraction_protocol(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 22 — Protocole d'Extraction Modulaire (MLOOP-172-BE, ADR-0202).

    Phase 3 BUILD uniquement (ignoré en dehors de STAGE_BUILD / STAGE_RUN).

    Règle :
      - Si un fichier Python stagé dépasse déjà RULE-AST-01 (>300 L) :
          → FAIL si plan absent ET fumée rouge/non exécutable
          → WARNING si plan présent mais fumée non exécutée, ou plan absent mais fumée verte
          → PASS si plan présent ET fumée verte (ou aucune modification en dépassement)
      - Si aucun fichier en dépassement dans le staging → PASS immédiat.
    """
    check_name = "Protocole d'Extraction Modulaire (MLOOP-172-BE)"

    # Ce check est actif uniquement en Phase 3 BUILD (et STAGE_RUN générique).
    active_stages = {"STAGE_BUILD", "STAGE_RUN", "STAGE_SHIP_SYNC"}
    if stage_label not in active_stages and lifecycle_mode != "RUN":
        return {"check": check_name, "status": "PASS"}

    # 1. Collecter les fichiers stagés en dépassement
    staged_files = _get_staged_files()
    oversized_staged: list[str] = [f for f in staged_files if _count_lines(f) > _AST_LIMIT_LINES]

    if not oversized_staged:
        # Aucun fichier en dépassement dans le staging : PASS
        return {"check": check_name, "status": "PASS"}

    # 2. Vérifier la présence d'un plan d'extraction
    plan_dir = Path("Projects") / project_name / "memory" / "plan"
    has_plan = _has_extraction_plan(plan_dir)

    # 3. Tenter le check de fumée sur le premier fichier en dépassement
    target_module = oversized_staged[0]
    smoke_ok, smoke_msg = _run_smoke_check(target_module)

    # 4. Appliquer la matrice PASS/WARNING/FAIL (§5.3 du protocole)
    if has_plan and smoke_ok:
        status = "PASS"
        detail = f"{len(oversized_staged)} fichier(s) >300L stagé(s) ; plan présent, fumée verte."
    elif has_plan and not smoke_ok:
        status = "WARNING"
        detail = (
            f"{len(oversized_staged)} fichier(s) >300L stagé(s) ; "
            f"plan présent mais fumée non verte : {smoke_msg[:120]}"
        )
    elif not has_plan and smoke_ok:
        status = "WARNING"
        detail = (
            f"{len(oversized_staged)} fichier(s) >300L stagé(s) ; "
            f"fumée verte mais plan d'extraction absent sous {plan_dir}."
        )
    else:
        # Ni plan, ni fumée verte → FAIL
        status = "FAIL"
        detail = (
            f"{len(oversized_staged)} fichier(s) >300L stagé(s), "
            f"plan absent ET fumée rouge/non exécutable. "
            f"Créer memory/plan/implementation_plan_*extraction*.md "
            f"et corriger les imports (fumée : {smoke_msg[:120]})."
        )
        logger.error(
            "Check 22 FAIL : plan absent ET fumée rouge pour %d fichier(s) en dépassement.",
            len(oversized_staged),
            extra={
                "check_name": "extraction_protocol",
                "oversized_count": len(oversized_staged),
                "plan_found": has_plan,
                "smoke_ok": smoke_ok,
                "smoke_msg": smoke_msg[:200],
            },
        )

    return {"check": f"{check_name} ({detail})", "status": status}
