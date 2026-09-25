"""
src/pipelines/bridge_certifier/_bc_ast.py — Contrôle d'isolement structurel des
modules de pont (MLOOP-215-FULL), niveau 2 structurel.

La limite d'isolement convenue (ADR-0387, pilier 4) est mesurée par le moteur
AST du framework — ``src.core.ast_checker`` — et non par un compteur de lignes
réécrit ici : une seconde implémentation de la règle serait elle-même une source
de dérive.

Le contrôle est **muable et exhaustif** : il liste les modules hors limite au
lieu de se contenter d'un booléen, de sorte que l'écart soit attribuable au
module fautif sans ouvrir de second fichier. Une violation préexistante est un
constat du rapport, pas une raison d'assouplir la règle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.ast_checker import check_file_ast
from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_models import (
    LEVEL_INTEGRATION,
    MODULE_MAX_BYTES,
    MODULE_MAX_LINES,
)

BRIDGES_DIR = Path("src") / "bridges"
RULE_ISOLATION = "RULE-AST-01"
MAX_LISTED_VIOLATIONS = 8


def control_isolation(checks: Checks) -> None:
    """``N2-ISOLEMENT-PONTS`` — mesure AST de chaque module sous ``src/bridges``."""
    modules = sorted(BRIDGES_DIR.rglob("*.py"))
    checks.capture("modules_scanned", len(modules))
    checks.capture(
        "limits",
        {"max_lines": MODULE_MAX_LINES, "max_bytes": MODULE_MAX_BYTES, "rule": RULE_ISOLATION},
    )
    if not checks.expect(bool(modules), f"aucun module trouvé sous {BRIDGES_DIR.as_posix()}"):
        return

    violations: list[str] = []
    for module in modules:
        try:
            audit = check_file_ast(module)
        except OSError as exc:
            checks.failures.append(f"{module.as_posix()} illisible : {exc}")
            continue
        for violation in getattr(audit, "violations", []):
            if getattr(violation, "rule_id", "") != RULE_ISOLATION:
                continue
            violations.append(
                f"{module.as_posix()} ({audit.line_count} lignes / "
                f"{module.stat().st_size} octets) : {getattr(violation, 'message', '')}"
            )

    checks.capture("violations_total", len(violations))
    checks.capture("violations", violations[:MAX_LISTED_VIOLATIONS])
    checks.expect(
        not violations,
        f"{len(violations)} module(s) de pont dépassent la limite "
        f"{MODULE_MAX_LINES} lignes / {MODULE_MAX_BYTES} octets — "
        + " ; ".join(violations[:MAX_LISTED_VIOLATIONS]),
    )


def run_isolation_controls() -> list[Any]:
    """Contrôle structurel unique du périmètre isolement (niveau 2)."""
    return [
        guard(
            "N2-ISOLEMENT-PONTS",
            "Limite d'isolement des modules de pont mesurée par le moteur AST",
            control_isolation,
            level=LEVEL_INTEGRATION,
        ),
    ]
