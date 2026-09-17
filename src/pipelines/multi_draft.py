"""
multi_draft.py — Moteur de Challenge Multi-Drafts & Auto-Évaluation Déterministe Locale (ADR-0373)

Ce pipeline orchestre l'évaluation comparative sur disque de 2 à 3 branches de récits
candidates (draft_A_*.md, draft_B_*.md, draft_C_*.md) via le Gatekeeper Structurel
(struct-check) et la Revue Sémantique Sentinel (rubber-duck).

Règle Constitutionnelle :
Aucune histoire ne peut être validée sans la matérialisation physique préalable
d'au moins deux drafts physiques sous memory/drafts/<STORY_ID>/.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.cli import ZeroFluffConsole
from src.engine.rubber_duck.critic import DevilAdvocateCritic, DevilAdvocateCritique
from src.pipelines.struct_checker import StructCheckEngine, StructCheckReport


@dataclass
class DraftEvaluationResult:
    draft_file: str
    file_name: str
    struct_check_passed: bool
    struct_violations: List[str] = field(default_factory=list)
    rubber_duck_status: str = "REJECTED"
    trust_score: float = 0.0
    business_discernment: float = 0.0
    ecosystem_coherence: float = 0.0
    technical_rigor: float = 0.0
    critical_flaws: List[str] = field(default_factory=list)
    silent_failures: List[str] = field(default_factory=list)


@dataclass
class ChallengeReport:
    story_id: str
    evaluated_at: str
    drafts_count: int
    passed_drafts_count: int
    best_draft: Optional[str]
    best_trust_score: float
    results: List[DraftEvaluationResult] = field(default_factory=list)
    status: str = "SUCCESS"
    message: str = ""


class MultiDraftChallengeEngine:
    """Moteur d'évaluation et de challenge pour les brouillons multi-branches."""

    MIN_PHYSICAL_DRAFTS = 2

    def __init__(self, project_path: Path, story_id: str) -> None:
        self.project_path = project_path
        self.story_id = story_id.strip()
        self.drafts_dir = self.project_path / "memory" / "drafts" / self.story_id

    def discover_drafts(self) -> List[Path]:
        """Découvre les fichiers de brouillon physiques sous memory/drafts/<story_id>/."""
        if not self.drafts_dir.exists():
            return []
        drafts = sorted(self.drafts_dir.glob("draft_*.md"))
        return drafts

    def run_challenge(self, strict: bool = True) -> TournamentReport:
        """
        Exécute le challenge local automatisé sur tous les brouillons découverts.
        Génère challenge_matrix.json et challenge_report.md.
        """
        drafts = self.discover_drafts()
        run_ts = datetime.now().isoformat()

        if len(drafts) < self.MIN_PHYSICAL_DRAFTS:
            msg = (
                f"[ADR-0373] Règle violée : {len(drafts)} draft(s) trouvé(s) sous "
                f"{self.drafts_dir.relative_to(self.project_path) if self.drafts_dir.exists() else self.drafts_dir}. "
                f"Au moins {self.MIN_PHYSICAL_DRAFTS} drafts physiques sont requis pour arbitrage."
            )
            return ChallengeReport(
                story_id=self.story_id,
                evaluated_at=run_ts,
                drafts_count=len(drafts),
                passed_drafts_count=0,
                best_draft=None,
                best_trust_score=0.0,
                status="FAILED",
                message=msg,
            )

        struct_engine = StructCheckEngine(self.project_path)
        eval_results: List[DraftEvaluationResult] = []

        for df in drafts:
            # 1. Évaluation Structurelle (struct-check)
            struct_rep: StructCheckReport = struct_engine.check_file(df, strict=strict)
            struct_passed = struct_rep.passed
            struct_violations = [
                f"[{v.check_id}] {v.message}" for v in struct_rep.violations
            ]

            # 2. Évaluation Sémantique Sentinel (rubber-duck)
            critique: DevilAdvocateCritique = DevilAdvocateCritic.evaluate_story(
                story_file=df,
                project_name=self.project_path.name,
                project_dir=self.project_path,
                persist_evidence=False,
            )

            res = DraftEvaluationResult(
                draft_file=str(df),
                file_name=df.name,
                struct_check_passed=struct_passed,
                struct_violations=struct_violations,
                rubber_duck_status=critique.status,
                trust_score=critique.overall_trust_score,
                business_discernment=critique.business_discernment_score,
                ecosystem_coherence=critique.ecosystem_coherence_score,
                technical_rigor=critique.technical_rigor_score,
                critical_flaws=critique.critical_flaws,
                silent_failures=critique.silent_failures,
            )
            eval_results.append(res)

        # Classement Pareto : d'abord struct-check OK, puis Trust Score max
        # APPROVED = aucun flaw ni warn; ACTION_REQUIRED = warns non-bloquants (trust_score reste élevé)
        _PASSING_STATUSES = {"APPROVED", "ACTION_REQUIRED"}
        passed_drafts = [
            r for r in eval_results if r.struct_check_passed and r.rubber_duck_status in _PASSING_STATUSES
        ]

        # Meilleur candidat
        ranked = sorted(
            eval_results,
            key=lambda r: (1 if r.struct_check_passed else 0, r.trust_score),
            reverse=True,
        )
        best = ranked[0] if ranked else None

        report = ChallengeReport(
            story_id=self.story_id,
            evaluated_at=run_ts,
            drafts_count=len(eval_results),
            passed_drafts_count=len(passed_drafts),
            best_draft=best.file_name if best else None,
            best_trust_score=best.trust_score if best else 0.0,
            results=eval_results,
            status="SUCCESS",
            message=f"Challenge achevé avec succès sur {len(eval_results)} branches.",
        )

        # Sauvegarde de la matrice JSON
        matrix_path = self.drafts_dir / "challenge_matrix.json"
        matrix_data = {
            "story_id": report.story_id,
            "evaluated_at": report.evaluated_at,
            "drafts_count": report.drafts_count,
            "passed_drafts_count": report.passed_drafts_count,
            "best_draft": report.best_draft,
            "best_trust_score": report.best_trust_score,
            "results": [asdict(r) for r in report.results],
        }
        matrix_path.write_text(json.dumps(matrix_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Sauvegarde du rapport Markdown
        md_path = self.drafts_dir / "challenge_report.md"
        md_lines = [
            f"# 🏆 Multi-Draft Challenge Local — {self.story_id}",
            "",
            f"> **Date d'Évaluation** : {report.evaluated_at}  ",
            f"> **Nombre de Branches** : {report.drafts_count}  ",
            f"> **Meilleure Branche** : `{report.best_draft}` ({report.best_trust_score:.1f}/100)  ",
            "",
            "---",
            "",
            "## Tableau Comparatif des Scores",
            "",
            "| Fichier Draft | Struct-Check | Sentinel | Discernement | Cohérence | Rigueur | Trust Score |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for r in report.results:
            sc_icon = "✅" if r.struct_check_passed else "❌"
            rd_icon = "✅" if r.rubber_duck_status == "APPROVED" else "❌"
            md_lines.append(
                f"| `{r.file_name}` | {sc_icon} | {rd_icon} | {r.business_discernment:.1f} | "
                f"{r.ecosystem_coherence:.1f} | {r.technical_rigor:.1f} | **{r.trust_score:.1f}/100** |"
            )

        md_lines.extend([
            "",
            "## Détail des Violations & Alertes",
            "",
        ])
        for r in report.results:
            md_lines.append(f"### `{r.file_name}`")
            if r.struct_violations:
                md_lines.append("**Violations Structurelles :**")
                for v in r.struct_violations:
                    md_lines.append(f"- ❌ {v}")
            else:
                md_lines.append("- ✅ Structure 100% conforme")

            if r.critical_flaws:
                md_lines.append("**Rejets Critiques Sentinel :**")
                for cf in r.critical_flaws:
                    md_lines.append(f"- ❌ {cf}")
            if r.silent_failures:
                md_lines.append("**Points d'attention & cas limites :**")
                for sf in r.silent_failures:
                    md_lines.append(f"- ⚠️ {sf}")
            md_lines.append("")

        md_path.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")

        return report

