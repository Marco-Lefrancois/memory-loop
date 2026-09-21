"""
mLoop QA Certifier Engine (ADR-0383 / MLOOP-090-BE & MLOOP-091-BE).
Moteur de certification de sprint 5-Niveaux pour Phase 4 (STAGE_4_VALIDATE & QA).
Exécute tests, audite AST, triangule CEL 4-piliers, audite NLI & Leakage Gate.
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (Python Senior).
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Callable, List, Optional

from src.core.ast_checker import AstChecker, AstAuditReport
from src.pipelines.cel_triangulation import triangulate_cel, REQUIRED_GHERKIN_PILLARS
from src.pipelines.nli_auditor import NliAuditorEngine
from src.pipelines.qa_certifier_models import (
    AstAuditSummary,
    CelTriangulationResult,
    PytestExecutionResult,
    QaCertificationReport,
    format_qa_markdown,
)
from src.utils.logger import get_logger

logger = get_logger("pipelines.qa_certifier")


class QaCertifierEngine:
    """Moteur de certification déterministe 5-Niveaux Phase 4 conforme ADR-0202 et ADR-0369."""

    def __init__(
        self,
        project_path: Optional[Path] = None,
        project_name: str = "mLoop",
        pytest_runner: Optional[Callable[..., PytestExecutionResult]] = None,
        default_timeout: float = 180.0,
    ) -> None:
        self.project_path = Path(project_path) if project_path else Path(".")
        self.project_name = project_name
        self.pytest_runner = pytest_runner
        self.default_timeout = default_timeout

    def _log_pytest_error(self, message: str, violation_type: str) -> None:
        """Journalise une erreur d'invocation pytest avec contexte métier (ADR-0369)."""
        logger.error(
            message,
            exc_info=True,
            extra={
                "project": self.project_name,
                "gate": 3,
                "phase": "STAGE_4_VALIDATE",
                "check_name": "pytest_suite",
                "violation_type": violation_type,
            },
        )

    def run_pytest_suite(
        self, test_dir: Optional[Path] = None, timeout_seconds: Optional[float] = None
    ) -> PytestExecutionResult:
        """Exécute la suite de tests avec timeout explicite (ADR-0369 Standard 3)."""
        timeout = timeout_seconds or self.default_timeout
        if self.pytest_runner:
            return self.pytest_runner(test_dir=test_dir, timeout_seconds=timeout)

        target = test_dir or (self.project_path / "tests")
        if not target.exists() and Path("tests").exists():
            target = Path("tests")

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                ["pytest", str(target), "-q"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.perf_counter() - t0
            output = proc.stdout + "\n" + proc.stderr
            all_passed = proc.returncode == 0
            m_p, m_f = re.search(r"(\d+)\s+passed", output), re.search(r"(\d+)\s+failed", output)
            passed = int(m_p.group(1)) if m_p else (1 if all_passed else 0)
            failed = int(m_f.group(1)) if m_f else 0
            total = max(1, passed + failed)
            return PytestExecutionResult(
                all_passed=all_passed,
                total_tests=total,
                passed_tests=passed,
                failed_tests=failed,
                duration_seconds=round(duration, 2),
                coverage_percent=100.0 if all_passed else round((passed / total) * 100, 1),
                details=output[:600],
            )
        except subprocess.TimeoutExpired as exc:
            self._log_pytest_error(
                f"Délai d'exécution expiré (> {timeout}s) lors de pytest.", "timeout"
            )
            return PytestExecutionResult(
                all_passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=round(time.perf_counter() - t0, 2),
                details=f"Délai d'exécution expiré (> {timeout}s) : {exc}",
            )
        except Exception as exc:
            self._log_pytest_error(
                "Erreur d'invocation du banc de tests pytest.", "invocation_error"
            )
            return PytestExecutionResult(
                all_passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=round(time.perf_counter() - t0, 2),
                details=f"Erreur d'invocation du banc de tests : {exc}",
            )

    def run_ast_audit(
        self, src_dir: Optional[Path] = None, target_files: Optional[List[Path]] = None
    ) -> AstAuditSummary:
        """Audite statiquement les modules du sprint ou de src/."""
        py_files: List[Path] = []
        if target_files:
            py_files = [p for p in target_files if p.exists() and p.suffix == ".py"]
        else:
            target = src_dir or (self.project_path / "src")
            if not target.exists() and Path("src").exists():
                target = Path("src")
            if target.exists():
                py_files = [
                    f
                    for f in target.rglob("*.py")
                    if "__pycache__" not in str(f) and ".venv" not in str(f)
                ]

        reports = [(pf, AstChecker.audit_file(pf)) for pf in py_files]
        violations_list = [
            {"file": str(pf), "rule_id": v.rule_id, "line": v.line_number, "message": v.message}
            for pf, rep in reports
            if not rep.passed
            for v in rep.violations
        ]

        return AstAuditSummary(
            files_audited=len(py_files),
            total_violations=len(violations_list),
            passed=len(violations_list) == 0,
            violations=violations_list,
        )

    def certify_sprint(
        self, save_reports: bool = True, test_dir: Optional[Path] = None
    ) -> QaCertificationReport:
        """Exécute les vérifications 5-Niveaux et produit le rapport opposable Phase 4."""
        t_total = time.perf_counter()

        # Niveau 1 : Triangulation Code Evidence Ledger
        t1 = time.perf_counter()
        cel_res = triangulate_cel(self.project_path, self.project_name)
        dur1 = round(time.perf_counter() - t1, 3)
        logger.info(
            "qa.certification.level.1",
            extra={
                "level": 1,
                "status": "passed" if cel_res.is_complete else "failed",
                "duration_s": dur1,
                "details": f"blocks={cel_res.total_blocks}, missing_pillars={cel_res.missing_pillars}",
            },
        )

        # Sélection ciblée des fichiers sources du sprint
        target_srcs: Optional[List[Path]] = None
        if cel_res.sprint_files:
            target_srcs = [
                Path(f) for f in cel_res.sprint_files if f.startswith("src") and Path(f).exists()
            ]

        # Niveau 2 : Exécution Pytest
        t2 = time.perf_counter()
        pytest_res = self.run_pytest_suite(test_dir=test_dir)
        dur2 = round(time.perf_counter() - t2, 3)
        logger.info(
            "qa.certification.level.2",
            extra={
                "level": 2,
                "status": "passed" if pytest_res.all_passed else "failed",
                "duration_s": dur2,
                "details": f"passed={pytest_res.passed_tests}, failed={pytest_res.failed_tests}",
            },
        )

        # Niveau 3 : Audit AST Sprint
        t3 = time.perf_counter()
        ast_res = self.run_ast_audit(target_files=target_srcs)
        dur3 = round(time.perf_counter() - t3, 3)
        logger.info(
            "qa.certification.level.3",
            extra={
                "level": 3,
                "status": "passed" if ast_res.passed else "failed",
                "duration_s": dur3,
                "details": f"files_audited={ast_res.files_audited}, violations={ast_res.total_violations}",
            },
        )

        # Niveau 4 & 5 : NLI & Leakage Gate
        nli_engine = NliAuditorEngine(
            project_path=self.project_path, project_name=self.project_name
        )
        target_tests: Optional[List[Path]] = None
        if cel_res.sprint_files:
            target_tests = [
                Path(f) for f in cel_res.sprint_files if f.startswith("tests") and Path(f).exists()
            ]

        t4 = time.perf_counter()
        leakage_res, nli_res = nli_engine.run_full_audit(test_files=target_tests)
        dur4 = round(time.perf_counter() - t4, 3)

        logger.info(
            "qa.certification.level.4",
            extra={
                "level": 4,
                "status": "passed" if nli_res.passed else "failed",
                "duration_s": dur4,
            },
        )
        logger.info(
            "qa.certification.level.5",
            extra={
                "level": 5,
                "status": "passed" if leakage_res.passed else "failed",
                "duration_s": dur4,
            },
        )

        blocking_reasons: List[str] = []
        if not pytest_res.all_passed:
            blocking_reasons.append(
                f"Échec pytest ({pytest_res.failed_tests}/{pytest_res.total_tests})."
            )
        if not ast_res.passed:
            blocking_reasons.append(
                f"Violations AST ({ast_res.total_violations}/{ast_res.files_audited})."
            )
        if not cel_res.is_complete:
            reason = (
                "CEL introuvable"
                if not cel_res.cel_found
                else f"CEL incomplet — piliers Gherkin manquants : {cel_res.missing_pillars}"
            )
            blocking_reasons.append(reason)
        if not leakage_res.passed:
            blocking_reasons.append(f"Fuites ({leakage_res.critical_violations} critique(s)).")
        if not nli_res.passed:
            blocking_reasons.append(f"Contradictions NLI ({nli_res.contradictions}).")

        report = QaCertificationReport(
            project_name=self.project_name,
            certified_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            is_certified=len(blocking_reasons) == 0,
            pytest_result=pytest_res,
            ast_summary=ast_res,
            cel_result=cel_res,
            leakage_summary=leakage_res,
            nli_summary=nli_res,
            blocking_reasons=blocking_reasons,
        )

        dur_total = round(time.perf_counter() - t_total, 3)
        logger.info(
            "qa.certification.complete",
            extra={
                "project": self.project_name,
                "is_certified": report.is_certified,
                "duration_total_s": dur_total,
            },
        )
        if save_reports:
            self._save_reports(report)
        return report

    def _save_reports(self, report: QaCertificationReport) -> None:
        """Sauvegarde les rapports JSON et Markdown dans memory/ (ADR-0369 Standard 2)."""
        mem_dir = self.project_path / "memory"
        if not mem_dir.exists() and (Path("Projects") / self.project_name / "memory").exists():
            mem_dir = Path("Projects") / self.project_name / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        with open(mem_dir / "qa_certification_report.json", "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        with open(mem_dir / "qa_certification_report.md", "w", encoding="utf-8") as f:
            f.write(format_qa_markdown(report))
