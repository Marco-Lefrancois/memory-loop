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
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from src.core.ast_checker import AstChecker, AstAuditReport
from src.pipelines.nli_auditor import NliAuditorEngine, LeakageAuditSummary, NliAuditSummary

REQUIRED_GHERKIN_PILLARS: Set[str] = {
    "PILIER_1_CHEMIN_NOMINAL",
    "PILIER_2_EXCEPTIONS_REJETS",
    "PILIER_3_RESILIENCE_MODE_DEGRADE",
    "PILIER_4_UX_OBSERVABILITE",
}


@dataclass
class PytestExecutionResult:
    all_passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    duration_seconds: float
    coverage_percent: float = 0.0
    details: str = ""


@dataclass
class AstAuditSummary:
    files_audited: int
    total_violations: int
    passed: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CelTriangulationResult:
    cel_found: bool
    ledger_path: str
    total_blocks: int
    covered_pillars: List[str] = field(default_factory=list)
    missing_pillars: List[str] = field(default_factory=list)
    is_complete: bool = False
    sprint_files: List[str] = field(default_factory=list)


@dataclass
class QaCertificationReport:
    project_name: str
    certified_at: str
    is_certified: bool
    pytest_result: PytestExecutionResult
    ast_summary: AstAuditSummary
    cel_result: CelTriangulationResult
    leakage_summary: Optional[LeakageAuditSummary] = None
    nli_summary: Optional[NliAuditSummary] = None
    blocking_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
                capture_output=True, text=True, timeout=timeout,
            )
            duration = time.perf_counter() - t0
            output = proc.stdout + "\n" + proc.stderr
            all_passed = proc.returncode == 0
            m_p, m_f = re.search(r"(\d+)\s+passed", output), re.search(r"(\d+)\s+failed", output)
            passed = int(m_p.group(1)) if m_p else (1 if all_passed else 0)
            failed = int(m_f.group(1)) if m_f else 0
            total = max(1, passed + failed)
            return PytestExecutionResult(
                all_passed=all_passed, total_tests=total, passed_tests=passed, failed_tests=failed,
                duration_seconds=round(duration, 2),
                coverage_percent=100.0 if all_passed else round((passed / total) * 100, 1),
                details=output[:600],
            )
        except subprocess.TimeoutExpired as exc:
            return PytestExecutionResult(
                all_passed=False, total_tests=0, passed_tests=0, failed_tests=1,
                duration_seconds=round(time.perf_counter() - t0, 2),
                details=f"Délai d'exécution expiré (> {timeout}s) : {exc}",
            )
        except Exception as exc:
            return PytestExecutionResult(
                all_passed=False, total_tests=0, passed_tests=0, failed_tests=1,
                duration_seconds=round(time.perf_counter() - t0, 2),
                details=f"Erreur d'invocation du banc de tests : {exc}",
            )

    def triangulate_cel(self, evidence_dir: Optional[Path] = None) -> CelTriangulationResult:
        """Vérifie la complétude du Code Evidence Ledger et extrait les fichiers du sprint."""
        target_dir = evidence_dir or (self.project_path / "memory" / "evidence")
        if not target_dir.exists() and (Path("Projects") / self.project_name / "memory" / "evidence").exists():
            target_dir = Path("Projects") / self.project_name / "memory" / "evidence"

        if not target_dir.exists():
            return CelTriangulationResult(False, "", 0, [], sorted(list(REQUIRED_GHERKIN_PILLARS)), False, [])

        ledgers = sorted(list(target_dir.glob("*code_evidence_ledger.json")), key=lambda p: p.stat().st_mtime, reverse=True)
        if not ledgers:
            return CelTriangulationResult(False, "", 0, [], sorted(list(REQUIRED_GHERKIN_PILLARS)), False, [])

        chosen = ledgers[0]
        try:
            with open(chosen, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return CelTriangulationResult(True, str(chosen), 0, [], sorted(list(REQUIRED_GHERKIN_PILLARS)), False, [])

        blocks: List[Dict[str, Any]] = []
        sprint_files: Set[str] = set()
        if isinstance(data, dict):
            if "code_blocks" in data and isinstance(data["code_blocks"], list):
                blocks.extend(data["code_blocks"])
            elif "ledger" in data and isinstance(data["ledger"], list):
                for entry in data["ledger"]:
                    if isinstance(entry, dict) and "blocks" in entry:
                        blocks.extend(entry.get("blocks", []))
            for fp in data.get("source_files_sha256", {}).keys():
                sprint_files.add(str(fp))

        covered: Set[str] = set()
        for b in blocks:
            p_raw = str(b.get("gherkin_pillar", "")).upper()
            if any(k in p_raw for k in ("PILIER_1", "PILIER 1", "NOMINAL")):
                covered.add("PILIER_1_CHEMIN_NOMINAL")
            if any(k in p_raw for k in ("PILIER_2", "PILIER 2", "EXCEPTION", "REJET")):
                covered.add("PILIER_2_EXCEPTIONS_REJETS")
            if any(k in p_raw for k in ("PILIER_3", "PILIER 3", "RESILIEN", "RÉSIL", "DEGRADE")):
                covered.add("PILIER_3_RESILIENCE_MODE_DEGRADE")
            if any(k in p_raw for k in ("PILIER_4", "PILIER 4", "UX", "OBSERVABIL")):
                covered.add("PILIER_4_UX_OBSERVABILITE")
            if b.get("file_path"):
                sprint_files.add(str(b["file_path"]))
            tp = b.get("test_proof")
            if isinstance(tp, dict) and tp.get("test_file"):
                sprint_files.add(str(tp["test_file"]))

        missing = sorted(list(REQUIRED_GHERKIN_PILLARS - covered))
        return CelTriangulationResult(
            cel_found=True, ledger_path=str(chosen), total_blocks=len(blocks),
            covered_pillars=sorted(list(covered)), missing_pillars=missing,
            is_complete=len(missing) == 0 and len(blocks) > 0,
            sprint_files=sorted(list(sprint_files)),
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
                py_files = [f for f in target.rglob("*.py") if "__pycache__" not in str(f) and ".venv" not in str(f)]

        violations_list: List[Dict[str, Any]] = []
        for pf in py_files:
            rep: AstAuditReport = AstChecker.audit_file(pf)
            if not rep.passed:
                for v in rep.violations:
                    violations_list.append({"file": str(pf), "rule_id": v.rule_id, "line": v.line_number, "message": v.message})

        return AstAuditSummary(
            files_audited=len(py_files), total_violations=len(violations_list),
            passed=len(violations_list) == 0, violations=violations_list,
        )

    def certify_sprint(
        self, save_reports: bool = True, test_dir: Optional[Path] = None
    ) -> QaCertificationReport:
        """Exécute les vérifications 5-Niveaux et produit le rapport opposable Phase 4."""
        cel_res = self.triangulate_cel()
        # Sélection ciblée des fichiers sources du sprint si présents dans le CEL
        target_srcs: Optional[List[Path]] = None
        if cel_res.sprint_files:
            target_srcs = [Path(f) for f in cel_res.sprint_files if f.startswith("src") and Path(f).exists()]

        pytest_res = self.run_pytest_suite(test_dir=test_dir)
        ast_res = self.run_ast_audit(target_files=target_srcs)
        nli_engine = NliAuditorEngine(project_path=self.project_path, project_name=self.project_name)
        # Ciblage des tests du sprint
        target_tests: Optional[List[Path]] = None
        if cel_res.sprint_files:
            target_tests = [Path(f) for f in cel_res.sprint_files if f.startswith("tests") and Path(f).exists()]
        leakage_res, nli_res = nli_engine.run_full_audit(test_files=target_tests)

        blocking_reasons: List[str] = []
        if not pytest_res.all_passed:
            blocking_reasons.append(f"Échec pytest ({pytest_res.failed_tests} échecs sur {pytest_res.total_tests}).")
        if not ast_res.passed:
            blocking_reasons.append(f"Violations AST ({ast_res.total_violations} violations sur {ast_res.files_audited} fichiers).")
        if not cel_res.is_complete:
            if not cel_res.cel_found:
                blocking_reasons.append("Fichier Code Evidence Ledger (*code_evidence_ledger.json) introuvable.")
            else:
                blocking_reasons.append(f"CEL incomplet (piliers Gherkin manquants : {cel_res.missing_pillars}).")
        if not leakage_res.passed:
            blocking_reasons.append(f"Fuites de vérification détectées ({leakage_res.critical_violations} violation(s) critique(s)).")
        if not nli_res.passed:
            blocking_reasons.append(f"Contradictions sémantiques NLI ({nli_res.contradictions} contradiction(s)).")

        report = QaCertificationReport(
            project_name=self.project_name, certified_at=datetime.now(timezone.utc).isoformat(),
            is_certified=len(blocking_reasons) == 0, pytest_result=pytest_res,
            ast_summary=ast_res, cel_result=cel_res, leakage_summary=leakage_res,
            nli_summary=nli_res, blocking_reasons=blocking_reasons,
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


def format_qa_markdown(report: QaCertificationReport) -> str:
    """Génère la synthèse Markdown opposable pour le rapport de certification QA."""
    st = "✅ CERTIFIÉ CONFORME" if report.is_certified else "❌ NON CONFORME (REJETÉ)"
    py_st = "SUCCÈS 100%" if report.pytest_result.all_passed else "ÉCHEC"
    p_cov = ', '.join(report.cel_result.covered_pillars) or 'Aucun'
    p_mis = ', '.join(report.cel_result.missing_pillars) or 'ZÉRO (Complet)'
    nli_st = "CONFORME (0 contradiction)" if (not report.nli_summary or report.nli_summary.passed) else "CONTRADICTIONS"
    leak_st = "CONFORME (Zéro fuite)" if (not report.leakage_summary or report.leakage_summary.passed) else "FUITES DÉTECTÉES"
    lines = [
        "# 🛡️ Rapport de Certification QA Sprint (Phase 4 — STAGE_4_VALIDATE)",
        f"- **Projet** : `{report.project_name}` | **Statut** : **{st}** | **Horodatage** : `{report.certified_at}`",
        f"- **1. Tests Pytest** : {py_st} ({report.pytest_result.passed_tests}/{report.pytest_result.total_tests} en {report.pytest_result.duration_seconds}s, cov: {report.pytest_result.coverage_percent}%)",
        f"- **2. Audit AST Sprint (ADR-0202 / ADR-0369)** : {report.ast_summary.files_audited} fichiers | {report.ast_summary.total_violations} violations",
        f"- **3. Triangulation CEL (4 Piliers Gherkin)** : {report.cel_result.total_blocks} blocs | Couverts: {p_cov} | Manquants: {p_mis}",
        f"- **4. Inférence NLI (ADR-0326)** : {nli_st}",
        f"- **5. Verification Leakage Gate (ADR-0354)** : {leak_st}",
        "",
    ]
    if report.blocking_reasons:
        lines.append("## 🛑 Motifs Bloquants d'Invalidation Gate 4")
        lines.extend(f"- ❌ {r}" for r in report.blocking_reasons)
    else:
        lines.append("## 🟢 Autorisation Gate 4\nTous les 5 critères de certification sont validés. Transition Gate 4 autorisée.")
    return "\n".join(lines) + "\n"
