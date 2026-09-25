"""
src/pipelines/bridge_certifier/_bc_checks.py — Agrégateur d'assertions du
harnais de certification (MLOOP-215-FULL).

Un contrôle ne s'arrête pas à la première rupture : il accumule **toutes** les
constatations pour publier un diagnostic exhaustif. Un échec partiel reste
lisibles pièce par pièce dans ``failures``, ce qui évite le diagnostic
« une assertion a échoué » sans objet pour l'agent aval.
"""

from __future__ import annotations

from typing import Any, Iterable

from src.pipelines.bridge_certifier._bc_models import (
    STATUS_FAIL,
    STATUS_PASS,
    CertificationError,
    ControlResult,
)

MAX_DIAGNOSTIC_FAILURES = 6


class Checks:
    """Collecteur borné d'assertions pour un contrôle unique."""

    def __init__(self, code: str, label: str, *, level: int) -> None:
        self.code = code
        self.label = label
        self.level = level
        self.failures: list[str] = []
        self.details: dict[str, Any] = {}

    def expect(self, condition: Any, message: str) -> bool:
        """Constate un fait ; ``False`` ajoute ``message`` aux ruptures."""
        if not condition:
            self.failures.append(message)
            return False
        return True

    def capture(self, key: str, value: Any) -> Any:
        """Consigne une valeur observable dans les détails du rapport."""
        self.details[key] = value
        return value

    @property
    def ok(self) -> bool:
        return not self.failures

    def diagnostic(self) -> str:
        if not self.failures:
            return "Contrôle conforme."
        head = self.failures[:MAX_DIAGNOSTIC_FAILURES]
        extra = len(self.failures) - len(head)
        text = " | ".join(head)
        if extra > 0:
            text += f" | (+{extra} autre(s) rupture(s))"
        return text

    def result(self) -> ControlResult:
        return ControlResult(
            code=self.code,
            level=self.level,
            label=self.label,
            status=STATUS_PASS if self.ok else STATUS_FAIL,
            diagnostic=self.diagnostic(),
            details=dict(self.details),
        )


def guard(
    code: str,
    label: str,
    fn: Any,
    *args: Any,
    level: int = 1,
    **kwargs: Any,
) -> ControlResult:
    """
    Exécute un contrôle et convertit toute rupture imprévue en ``FAIL``
    explicite (état ``ERREUR`` jamais silencieux, ADR-0369 anti-silent-pass).

    Une exception de contrôle est un constat, pas un crash du harnais : elle
    devient un diagnostic nommant l'exception et sa cause.
    """
    checks = Checks(code, label, level=level)
    try:
        fn(checks, *args, **kwargs)
    except CertificationError as exc:
        checks.failures.append(f"Certification interrompue : {exc}")
    except Exception as exc:  # noqa: BLE001 — bornage volontaire du harnais
        checks.failures.append(f"{type(exc).__name__} : {exc}")
    return checks.result()


def failed_only(results: Iterable[ControlResult]) -> list[str]:
    """Codes des contrôles en échec (diagnostic rapide)."""
    return [r.code for r in results if r.status == STATUS_FAIL]
