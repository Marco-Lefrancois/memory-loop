"""
QA Certifier Models (ADR-0383).
Dataclasses et formateur Markdown pour la certification Phase 4.
Extrait de qa_certifier.py pour respecter ADR-0202 (<=300 lignes).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.pipelines.nli_auditor import LeakageAuditSummary, NliAuditSummary


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


def format_qa_markdown(report: QaCertificationReport) -> str:
    """Génère la synthèse Markdown opposable pour le rapport de certification QA."""
    st = "✅ CERTIFIÉ CONFORME" if report.is_certified else "❌ NON CONFORME (REJETÉ)"
    py_st = "SUCCÈS 100%" if report.pytest_result.all_passed else "ÉCHEC"
    p_cov = ", ".join(report.cel_result.covered_pillars) or "Aucun"
    p_mis = ", ".join(report.cel_result.missing_pillars) or "ZÉRO (Complet)"
    nli_st = (
        "CONFORME (0 contradiction)"
        if (not report.nli_summary or report.nli_summary.passed)
        else "CONTRADICTIONS"
    )
    leak_st = (
        "CONFORME (Zéro fuite)"
        if (not report.leakage_summary or report.leakage_summary.passed)
        else "FUITES DÉTECTÉES"
    )
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
        lines.append(
            "## 🟢 Autorisation Gate 4\nTous les 5 critères de certification sont validés. Transition Gate 4 autorisée."
        )
    return "\n".join(lines) + "\n"
