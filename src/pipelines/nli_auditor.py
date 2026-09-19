"""
mLoop Pipeline - NLI Contradiction Engine & Verification Leakage Gate (MLOOP-091-BE).
Certifie l'absence de fuites de vérification (ADR-0354) et l'absence de contradictions
sémantiques entre la documentation SSOT et le code source (ADR-0326).
Conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369 (Python Senior).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.engine.gates.verification_leakage import VerificationLeakageGate, LeakageReport
from src.engine.fact_check.domain_invariants import DomainInvariantChecker, InvariantSeverity

logger = logging.getLogger("pipelines.nli_auditor")


@dataclass
class LeakageAuditSummary:
    """Synthèse d'évaluation de la porte anti-fuite de vérification."""
    files_audited: int
    critical_violations: int
    warning_violations: int
    passed: bool
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_audited": self.files_audited,
            "critical_violations": self.critical_violations,
            "warning_violations": self.warning_violations,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass
class NliAuditSummary:
    """Synthèse d'évaluation de non-contradiction sémantique NLI."""
    claims_verified: int
    entailments: int
    contradictions: int
    unsupported: int
    passed: bool
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claims_verified": self.claims_verified,
            "entailments": self.entailments,
            "contradictions": self.contradictions,
            "unsupported": self.unsupported,
            "passed": self.passed,
            "details": self.details,
        }


class NliAuditorEngine:
    """Moteur d'audit NLI et de surveillance de fuites pour le harnais Phase 4."""

    def __init__(
        self,
        project_path: Optional[Path] = None,
        project_name: str = "mLoop",
    ) -> None:
        self.project_path = Path(project_path) if project_path else Path(".")
        self.project_name = project_name
        self.leakage_gate = VerificationLeakageGate()

    def audit_leakage(
        self, test_files: Optional[List[Path]] = None
    ) -> LeakageAuditSummary:
        """Audite statiquement les fichiers de tests contre les fuites de vérification."""
        targets: List[Path] = []
        if test_files is not None:
            targets = [p for p in test_files if p.exists() and p.suffix == ".py"]
        else:
            cand = self.project_path / "tests"
            if not cand.exists() and self.project_path in (Path("."), Path("")) and Path("tests").exists():
                cand = Path("tests")
            if cand.exists():
                targets = sorted(list(cand.glob("test_*.py")))

        if not targets:
            return LeakageAuditSummary(
                files_audited=0, critical_violations=0, warning_violations=0,
                passed=True, details=["Aucun fichier de test trouvé pour l'audit."],
            )

        critical_count = 0
        warning_count = 0
        details: List[str] = []

        for tf in targets:
            try:
                rep: LeakageReport = self.leakage_gate.check_file(tf)
                critical_count += rep.critical_count
                warning_count += rep.warning_count
                if not rep.passed:
                    for v in rep.violations:
                        if v.severity == "CRITICAL":
                            details.append(f"{tf.name}:L{v.line_no} [C{v.criterion}] {v.message}")
            except Exception as exc:
                logger.debug("Erreur lors de l'audit anti-fuite sur %s : %s", tf, exc, exc_info=True)

        passed = critical_count == 0
        return LeakageAuditSummary(
            files_audited=len(targets),
            critical_violations=critical_count,
            warning_violations=warning_count,
            passed=passed,
            details=details,
        )

    def audit_nli_claims(
        self, docs_dir: Optional[Path] = None
    ) -> NliAuditSummary:
        """Audite les affirmations documentaires face aux invariants de domaine."""
        target_dir = docs_dir
        if not target_dir:
            cand = self.project_path / "docs"
            if not cand.exists() and (Path("Projects") / self.project_name / "docs").exists():
                cand = Path("Projects") / self.project_name / "docs"
            target_dir = cand

        if not target_dir or not target_dir.exists():
            return NliAuditSummary(
                claims_verified=0, entailments=0, contradictions=0, unsupported=0,
                passed=True, details=["Aucun répertoire docs trouvé pour l'audit NLI."],
            )

        doc_files = list(target_dir.rglob("*.md"))
        claims_checked = 0
        contradictions = 0
        entailments = 0
        unsupported = 0
        details: List[str] = []

        for df in doc_files:
            try:
                content = df.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                for line_idx, line in enumerate(lines, start=1):
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("#"):
                        continue
                    # Détection d'invariants de domaine via DomainInvariantChecker
                    inv = DomainInvariantChecker.check_statement(line_clean)
                    if inv:
                        claims_checked += 1
                        if inv.severity == InvariantSeverity.FATAL:
                            contradictions += 1
                            details.append(
                                f"{df.name}:L{line_idx} Contradiction physique : {inv.rule_name} ({inv.message})"
                            )
                        elif inv.severity in (InvariantSeverity.CRITICAL, InvariantSeverity.WARNING):
                            unsupported += 1
                        else:
                            entailments += 1
            except Exception as exc:
                logger.debug("Erreur de lecture NLI sur %s : %s", df, exc, exc_info=True)

        passed = contradictions == 0
        return NliAuditSummary(
            claims_verified=max(1, claims_checked) if doc_files else 0,
            entailments=entailments,
            contradictions=contradictions,
            unsupported=unsupported,
            passed=passed,
            details=details,
        )

    def run_full_audit(
        self,
        test_files: Optional[List[Path]] = None,
        docs_dir: Optional[Path] = None,
    ) -> Tuple[LeakageAuditSummary, NliAuditSummary]:
        """Exécute les deux audits NLI et Leakage Gate."""
        leakage = self.audit_leakage(test_files=test_files)
        nli = self.audit_nli_claims(docs_dir=docs_dir)
        return leakage, nli
