"""
src/pipelines/bridge_certifier/_bc_runner.py — Orchestrateur du harnais de
certification des ponts MCP (MLOOP-215-FULL).

Séquence d'exécution, dans l'ordre, avec compteurs de contrôle actualisés à
chaque étape (état de surface ``CHARGEMENT``) :

1. périmètre **mémoire** (échanges in-process) ;
2. périmètre **extensions** officielles (élicitation, compétences, tâches) ;
3. périmètre **dégradation** gracieuse ;
4. périmètre **navigateur** (2 ressources ``ui://`` dans un cadre sandboxé) ;
5. périmètre **transport** (processus fils réel borné) ;
6. périmètre **isolement** structurel (moteur AST) ;
7. périmètre **non-régression** (collecte puis suite intégrale, sans sharding).

Le verdict n'est ``CONFORME`` que si **aucun** contrôle n'échoue et que le
périmètre est complet. Un périmètre partiel produit un rapport explicitement
marqué ``complete: false`` : il ne peut jamais être lu comme un vert.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from src.pipelines.bridge_certifier._bc_ast import run_isolation_controls
from src.pipelines.bridge_certifier._bc_browser import missing_dependency, run_browser_controls
from src.pipelines.bridge_certifier._bc_degrade import run_degradation_controls
from src.pipelines.bridge_certifier._bc_extensions import run_extension_controls
from src.pipelines.bridge_certifier._bc_memory import run_memory_controls
from src.pipelines.bridge_certifier._bc_models import (
    CertificationReport,
    default_report_dir,
    summarize_controls,
)
from src.pipelines.bridge_certifier._bc_persist import write_certification_report
from src.pipelines.bridge_certifier._bc_pytest import run_nonregression_controls
from src.pipelines.bridge_certifier._bc_subprocess import run_transport_controls

# Périmètre complet de la certification (tout écart est visible dans `scope`).
FULL_SCOPES: tuple[str, ...] = (
    "memory",
    "extensions",
    "degradation",
    "browser",
    "transport",
    "isolation",
    "nonregression",
)

LIMIT_IDE_AUDIT = (
    "Audit manuel des 3 IDE réels (VS Code, JetBrains, Windsurf) — niveau 3, "
    "exigence manuelle du récit, jamais exécuté par le harnais (Macro Q6)."
)


@dataclass
class CertificationConfig:
    """Paramètres d'exécution ; le périmètre par défaut est le périmètre complet."""

    project_root: Path
    report_dir: Optional[Path] = None
    scopes: Sequence[str] = field(default_factory=lambda: list(FULL_SCOPES))
    suite_timeout_s: float = 2400.0
    collection_timeout_s: float = 300.0
    transport_timeout_s: float = 60.0
    browser_timeout_s: float = 45.0
    persist: bool = True
    progress: Optional[Callable[[str], None]] = None

    @property
    def resolved_report_dir(self) -> Path:
        return Path(self.report_dir) if self.report_dir else default_report_dir(self.project_root)

    @property
    def complete(self) -> bool:
        return tuple(sorted(self.scopes)) == tuple(sorted(FULL_SCOPES))

    def emit(self, message: str) -> None:
        if self.progress is not None:
            self.progress(message)


def _collect(config: CertificationConfig) -> list[Any]:
    """Assemble les contrôles du périmètre demandé, dans l'ordre canonique."""
    root = Path(config.project_root)
    results: list[Any] = []
    if "memory" in config.scopes:
        results += run_memory_controls()
    if "extensions" in config.scopes:
        results += run_extension_controls()
    if "degradation" in config.scopes:
        results += run_degradation_controls()
    if "browser" in config.scopes:
        results += run_browser_controls(timeout_s=config.browser_timeout_s)
    if "transport" in config.scopes:
        work_dir = Path(tempfile.mkdtemp(prefix="mloop-bridge-transport-"))
        results += run_transport_controls(
            repo_root=root, work_dir=work_dir, timeout_s=config.transport_timeout_s
        )
    if "isolation" in config.scopes:
        results += run_isolation_controls()
    if "nonregression" in config.scopes:
        results += run_nonregression_controls(repo_root=root, timeout_s=config.suite_timeout_s)
    return results


def run_certification(config: CertificationConfig) -> CertificationReport:
    """
    Exécute le harnais et retourne le rapport finalisé.

    ``config.persist=False`` produit un rapport en mémoire seul : c'est le mode
    de vérification, qui ne modifie pas l'état persisté du dépôt.
    """
    report = CertificationReport(scope={"scopes": list(config.scopes), "complete": config.complete})
    report.note(
        "start",
        f"Démarrage de la certification — périmètre {'complet' if config.complete else 'partiel'} "
        f"({', '.join(config.scopes)}).",
        scopes=len(config.scopes),
        complete=config.complete,
    )
    config.emit(f"CHARGEMENT — périmètre {', '.join(config.scopes)}")

    results = _collect(config)
    for result in results:
        report.add(result)
        report.counters.update(summarize_controls(report.controls))
        config.emit(
            f"[{report.counters['controls_total']}] {result.code} {result.status} — {result.label}"
        )

    report.dependency_missing = missing_dependency() if "browser" in config.scopes else []
    report.executable = not report.dependency_missing
    report.limits_admitted.append(LIMIT_IDE_AUDIT)
    report.note(
        "scope",
        "Périmètre exécuté : " + ", ".join(config.scopes),
        complete=config.complete,
        missing_deps=report.dependency_missing,
    )
    report.finalize()
    config.emit(
        f"VERDICT {report.verdict} — {len(report.passed_controls)}/{len(report.controls)} contrôles"
    )

    if config.persist:
        json_path, md_path = write_certification_report(report, config.resolved_report_dir)
        report.note("persist", f"Rapport écrit : {json_path.name} (+ {md_path.name})")
    else:
        report.note("persist", "Mode vérification : aucun rapport persisté.")
    return report


def certify(project_root: Path, **kwargs: Any) -> CertificationReport:
    """Raccourci d'exécution avec périmètre complet."""
    return run_certification(CertificationConfig(project_root=Path(project_root), **kwargs))
