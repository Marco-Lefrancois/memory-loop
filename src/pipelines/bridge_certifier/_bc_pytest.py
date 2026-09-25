"""
src/pipelines/bridge_certifier/_bc_pytest.py — Contrôles de non-régression du
socle (MLOOP-215-FULL), niveau 2 intégration.

Le harnais **rejoue le vrai runner** : il appelle ``pytest`` en sous-processus
borné, lit le récapitulatif final et n'utilise **que le compteur dynamique** de
cette exécution. Aucun nombre de tests n'est écrit en dur dans le harnais : le
compteur de la suite grandit à chaque récit, et un chiffre figé deviendrait
aussitôt faux — ou pire, masquerait un test supprimé.

Le contrôle ``N2-NONREG-SUITE`` compare en plus le nombre de tests **exécutés**
au nombre de tests **collectés** : un écart est la signature d'un sharding ou
d'un filtre silencieux, exactement ce que le récit interdit.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from src.pipelines.bridge_certifier._bc_checks import Checks, guard
from src.pipelines.bridge_certifier._bc_models import LEVEL_INTEGRATION
from src.pipelines.bridge_certifier._bc_persist import dynamic_counters


def _run_pytest(args: list[str], *, repo_root: Path, timeout_s: float) -> Any:
    """Exécute pytest avec un délai explicite et une sortie capturée (ADR-0369)."""
    return subprocess.run(  # noqa: S603 — runner interne, entrées non externes
        [sys.executable, "-m", "pytest", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(repo_root),
        timeout=timeout_s,
    )


def _tail(output: str, *, lines: int = 6) -> list[str]:
    return [line for line in (output or "").splitlines() if line.strip()][-lines:]


def control_collection(checks: Checks, *, repo_root: Path, timeout_s: float) -> None:
    """``N2-NONREG-SCOLTEUR`` — compteur dynamique de la collecte complète."""
    try:
        proc = _run_pytest(["--collect-only", "-q"], repo_root=repo_root, timeout_s=timeout_s)
    except subprocess.TimeoutExpired:
        checks.failures.append(f"collecte interrompue : délai de {timeout_s}s dépassé")
        return
    output = (proc.stdout or "") + (proc.stderr or "")
    counters = dynamic_counters(proc.stdout or "")
    checks.capture("counters", counters)
    checks.capture("tail", _tail(proc.stdout or ""))
    checks.expect(
        proc.returncode == 0,
        f"collecte en échec (code {proc.returncode}) : {_tail(output)!r}",
    )
    collected = counters.get("collected")
    checks.expect(
        isinstance(collected, int) and collected > 0,
        f"compteur dynamique de collecte illisible ({collected!r}) — "
        "refus d'un chiffre figé de repli",
    )
    checks.expect(
        counters.get("failed", 0) == 0 and counters.get("errors", 0) == 0,
        f"erreurs de collecte détectées ({counters!r})",
    )


def control_suite(
    checks: Checks,
    *,
    repo_root: Path,
    timeout_s: float,
    expected_collected: Optional[int] = None,
) -> None:
    """``N2-NONREG-SUITE`` — suite intégrale à 0 échec, sans sharding."""
    try:
        proc = _run_pytest(["-q"], repo_root=repo_root, timeout_s=timeout_s)
    except subprocess.TimeoutExpired:
        checks.failures.append(f"suite interrompue : délai de {timeout_s}s dépassé")
        return
    output = (proc.stdout or "") + (proc.stderr or "")
    counters = dynamic_counters(proc.stdout or "")
    checks.capture("counters", counters)
    checks.capture("duration_s", counters.get("duration_s"))
    checks.capture("tail", _tail(proc.stdout or ""))

    checks.expect(
        proc.returncode in (0, 1),
        f"runner interrompu (code {proc.returncode}) : {_tail(output)!r}",
    )
    checks.expect(
        counters.get("failed", 0) == 0,
        f"{counters.get('failed', 0)} test(s) en échec",
    )
    checks.expect(
        counters.get("errors", 0) == 0,
        f"{counters.get('errors', 0)} erreur(s) de collection ou d'erreur interne",
    )
    executed = counters.get("collected")
    checks.expect(
        isinstance(executed, int) and executed > 0,
        f"compteur dynamique d'exécution illisible ({executed!r})",
    )
    if isinstance(expected_collected, int) and expected_collected > 0:
        checks.capture("expected_collected", expected_collected)
        checks.expect(
            executed == expected_collected,
            f"{executed} tests exécutés pour {expected_collected} collectés : "
            "sharding ou filtre silencieux détecté",
        )
    checks.expect(
        proc.returncode == 0,
        f"pytest terminé en code {proc.returncode} (au moins un échec signalé)",
    )


def run_nonregression_controls(*, repo_root: Path, timeout_s: float) -> list[Any]:
    """
    Contrôles de non-régression, le second consommant le compteur dynamique du
    premier : la suite exécutée doit correspondre exactement à la suite
    collectée, sinon un shard ou un filtre silencieux s'est glissé.
    """
    collection = guard(
        "N2-NONREG-SCOLTEUR",
        "Collecte intégrale et compteur dynamique (zéro valeur figée)",
        control_collection,
        level=LEVEL_INTEGRATION,
        repo_root=repo_root,
        timeout_s=timeout_s,
    )
    counters = collection.details.get("counters") or {}
    expected = counters.get("collected") if isinstance(counters.get("collected"), int) else None
    suite = guard(
        "N2-NONREG-SUITE",
        "Suite intégrale à 0 échec, exécutée sans sharding",
        control_suite,
        level=LEVEL_INTEGRATION,
        repo_root=repo_root,
        timeout_s=timeout_s,
        expected_collected=expected,
    )
    return [collection, suite]
