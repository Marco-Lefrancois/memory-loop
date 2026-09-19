"""
Moteur de Tournoi de Code Multi-Draft et Matrice de Décision Pareto (MLOOP-081-BE / ADR-0381).
Évalue physiquement les candidats concurrents face à un banc de test unitaire et au linter AST,
puis calcule la fonction d'utilité multicritère pour promouvoir le Golden Master.
"""
from __future__ import annotations

import ast
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from src.core.ast_checker import check_file_ast

logger = logging.getLogger(__name__)


class NoQualifiedCandidateError(RuntimeError):
    """Levée lorsqu'aucun candidat n'a franchi avec succès les portes dures (Pytest + AST)."""
    pass


class DraftFolderNotFoundError(FileNotFoundError):
    """Levée lorsque le répertoire contenant les ébauches est introuvable."""
    pass


@dataclass
class CandidateResult:
    """Résultats d'évaluation et scores d'un candidat physique."""
    candidate_id: str
    file_path: Path
    pytest_passed: bool
    ast_passed: bool
    disqualified: bool
    disqualification_reason: Optional[str]
    robustness_score: float
    simplicity_score: float
    performance_score: float
    pareto_score: float
    execution_duration_ms: float


@dataclass
class TournamentReport:
    """Rapport d'arbitrage exhaustif du tournoi de code."""
    story_id: str
    winner_id: Optional[str]
    winner_path: Optional[Path]
    target_path: Path
    promoted: bool
    candidates: List[CandidateResult] = field(default_factory=list)


class CodeTournamentEngine:
    """Orchestrateur du tournoi multi-drafts opposant 2 à 3 candidats physiques."""

    def __init__(
        self,
        story_id: str,
        drafts_dir: Path,
        target_path: Path,
        test_file: Path,
    ) -> None:
        self.story_id = story_id
        self.drafts_dir = Path(drafts_dir)
        self.target_path = Path(target_path)
        self.test_file = Path(test_file)

    def _compute_ast_metrics(self, file_path: Path) -> tuple[float, float, int]:
        """Calcule la complexité cyclomatique, le ratio de typage et le nombre de lignes."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.debug("Erreur lecture candidat %s : %s", file_path, e, exc_info=True)
            return 10.0, 0.5, 100

        lines = content.splitlines()
        line_count = len(lines)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 15.0, 0.0, line_count

        branches = 0
        total_funcs = 0
        typed_funcs = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.BoolOp)):
                branches += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                has_return = node.returns is not None
                args_typed = all(
                    arg.annotation is not None
                    for arg in node.args.args
                    if arg.arg not in ("self", "cls")
                )
                if has_return and args_typed:
                    typed_funcs += 1

        type_ratio = (typed_funcs / total_funcs) if total_funcs > 0 else 1.0
        cc = max(1, branches)
        return float(cc), float(type_ratio), line_count

    def _evaluate_candidate(self, candidate_file: Path) -> CandidateResult:
        """Évalue un candidat face aux Hard Gates (AST, Tests) et calcule ses scores."""
        cid = candidate_file.name

        # 1. Hard Gate 1 : Linter AST
        ast_rep = check_file_ast(candidate_file)
        if not ast_rep.passed:
            reasons = ", ".join(f"{v.rule_id}: {v.message}" for v in ast_rep.violations)
            return CandidateResult(
                candidate_id=cid,
                file_path=candidate_file,
                pytest_passed=False,
                ast_passed=False,
                disqualified=True,
                disqualification_reason=f"Échec AST ({reasons})",
                robustness_score=0.0,
                simplicity_score=0.0,
                performance_score=0.0,
                pareto_score=0.0,
                execution_duration_ms=ast_rep.duration_ms,
            )

        # 2. Hard Gate 2 : Banc de Test Pytest
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        backup_content = self.target_path.read_text(encoding="utf-8") if self.target_path.exists() else None

        pytest_passed = False
        duration_ms = 0.0
        try:
            shutil.copy2(candidate_file, self.target_path)
            env = os.environ.copy()
            target_dir = str(self.target_path.parent.resolve())
            env["PYTHONPATH"] = f"{target_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

            t0 = time.perf_counter()
            res = subprocess.run(
                [sys.executable, "-m", "pytest", str(self.test_file.resolve()), "-q"],
                cwd=str(self.target_path.parent.resolve()),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            duration_ms = (time.perf_counter() - t0) * 1000
            pytest_passed = (res.returncode == 0)
        except Exception as e:
            logger.debug("Exception exécution test candidat %s : %s", cid, e, exc_info=True)
            pytest_passed = False
        finally:
            if backup_content is not None:
                self.target_path.write_text(backup_content, encoding="utf-8")
            elif self.target_path.exists():
                self.target_path.unlink(missing_ok=True)

        if not pytest_passed:
            return CandidateResult(
                candidate_id=cid,
                file_path=candidate_file,
                pytest_passed=False,
                ast_passed=True,
                disqualified=True,
                disqualification_reason="Échec du banc de test unitaire pytest",
                robustness_score=0.0,
                simplicity_score=0.0,
                performance_score=0.0,
                pareto_score=0.0,
                execution_duration_ms=duration_ms,
            )

        # 3. Calcul des Scores Pareto
        cc, type_ratio, line_count = self._compute_ast_metrics(candidate_file)
        robustness = 100.0 * (1.0 - min(cc, 15.0) / 15.0) * max(type_ratio, 0.1)
        simplicity = 100.0 * max(0.0, 1.0 - (float(line_count) / 300.0))
        performance = 100.0  # Normalisé par la suite

        return CandidateResult(
            candidate_id=cid,
            file_path=candidate_file,
            pytest_passed=True,
            ast_passed=True,
            disqualified=False,
            disqualification_reason=None,
            robustness_score=round(robustness, 2),
            simplicity_score=round(simplicity, 2),
            performance_score=performance,
            pareto_score=0.0,  # Calculé globalement
            execution_duration_ms=duration_ms,
        )

    def run_tournament(self) -> TournamentReport:
        """Exécute le tournoi complet et promeut le candidat vainqueur."""
        if not self.drafts_dir.exists():
            raise DraftFolderNotFoundError(f"Dossier de drafts introuvable : {self.drafts_dir}")

        candidates_files = sorted(self.drafts_dir.glob("candidate_*.py"))
        if not candidates_files:
            raise DraftFolderNotFoundError(f"Aucun fichier candidat sous {self.drafts_dir}")

        results: list[CandidateResult] = []
        for c_file in candidates_files:
            res = self._evaluate_candidate(c_file)
            results.append(res)

        qualified = [r for r in results if not r.disqualified]
        if not qualified:
            raise NoQualifiedCandidateError(
                f"Tous les candidats pour le récit {self.story_id} ont été disqualifiés."
            )

        # Normaliser les scores de performance relatifs
        min_dur = min(max(r.execution_duration_ms, 0.001) for r in qualified)
        for r in qualified:
            dur = max(r.execution_duration_ms, 0.001)
            r.performance_score = round(100.0 * (min_dur / dur), 2)
            # S_pareto = 0.40 * R + 0.35 * S + 0.25 * P
            r.pareto_score = round(
                0.40 * r.robustness_score + 0.35 * r.simplicity_score + 0.25 * r.performance_score,
                2
            )

        # Sélectionner le vainqueur
        qualified.sort(key=lambda x: x.pareto_score, reverse=True)
        winner = qualified[0]

        # Promotion en Golden Master
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(winner.file_path, self.target_path)

        return TournamentReport(
            story_id=self.story_id,
            winner_id=winner.candidate_id,
            winner_path=winner.file_path,
            target_path=self.target_path,
            promoted=True,
            candidates=results,
        )


def format_tournament_report(report: TournamentReport) -> str:
    """Génère la matrice comparative console du tournoi de code."""
    lines = [
        f"=== TOURNOI DE CODE MULTI-DRAFT : {report.story_id} ===",
        f"Cible : {report.target_path.as_posix()} | Promotion : {'OUI' if report.promoted else 'NON'}",
        f"Candidat vainqueur : {report.winner_id or 'AUCUN'}",
        "",
        "Matrice d'Arbitrage Pareto (ADR-0381) :",
        "| Candidat | Statut | Robustesse (40%) | Simplicité (35%) | Vitesse (25%) | Score Pareto |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ]
    for c in report.candidates:
        if c.disqualified:
            status_str = f"DISQUALIFIÉ ({c.disqualification_reason})"
            lines.append(f"| {c.candidate_id} | {status_str} | - | - | - | 0.00 |")
        else:
            is_winner = " [VAINQUEUR PROMU]" if c.candidate_id == report.winner_id else ""
            lines.append(
                f"| {c.candidate_id}{is_winner} | QUALIFIÉ | {c.robustness_score:.1f} | "
                f"{c.simplicity_score:.1f} | {c.performance_score:.1f} | {c.pareto_score:.2f} |"
            )
    return "\n".join(lines)
