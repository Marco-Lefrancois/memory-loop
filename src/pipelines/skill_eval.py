# -*- coding: utf-8 -*-
"""
skill_eval.py — Moteur d'Évaluation des Compétences Agentiques mLoop.
Aligne sur le standard Google Agents CLI Eval (Harness Engineering & Outcome-Based Evals).
Matrice 5 dimensions : Contraintes physiques Système 1 + Rubrique 100 pts + Golden Dataset.
Conforme ADR-0202 (<= 300 lignes), ADR-0369 (Python Senior) et ADR-0389.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from src.utils.logger import get_logger
from src.pipelines._skill_eval_golden import evaluate_golden_dataset, resolve_cases_file
from src.pipelines._skill_eval_report import persist_reports

logger = get_logger("pipelines.skill_eval")

# Compétences d'orchestration ou de décision lourdes devant désactiver l'auto-invocation
HEAVY_META_SKILLS = {
    "zero-blindspot-spec",
    "handoff",
    "router",
    "sentinel",
    "rubber-duck",
    "calibrate",
    "obsidian-canvas",
    "visual-excalidraw",
    "visual-mermaid",
}


@dataclass
class SkillEvalResult:
    """Résultat d'évaluation d'une compétence agentique."""
    skill_name: str
    file_path: str
    verdict: str  # "PASS", "WARNING", "FAIL"
    total_score: float
    scores_breakdown: Dict[str, Any]
    token_stats: Dict[str, int]
    deterministic_checks: Dict[str, bool]
    blocking_flaws: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    golden_dataset_detail: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SkillEvalEngine:
    """Moteur d'audit déterministe et sémantique des manifestes .agents/skills/*/SKILL.md."""

    PASS_THRESHOLD: float = 80.0

    def __init__(self, workspace_root: Path | str = ".", pass_threshold: float = 80.0) -> None:
        self.workspace_root = Path(workspace_root)
        self.skills_dir = self.workspace_root / ".agents" / "skills"
        self.pass_threshold = pass_threshold

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estime les jetons (1 jeton ~ 3.7 caractères pour Markdown/bilingue)."""
        return max(1, int(len(text.strip()) / 3.7)) if text and text.strip() else 0

    @classmethod
    def _run_deterministic_checks(
        cls, content: str, metadata: Dict[str, str], skill_file: Path
    ) -> Tuple[Dict[str, bool], List[str]]:
        """Système 1 : Assertions mécaniques strictes (plancher qualité)."""
        checks: Dict[str, bool] = {}
        flaws: List[str] = []

        lines = content.splitlines()
        byte_size = len(content.encode("utf-8"))
        desc = metadata.get("description", "")
        skill_name = metadata.get("name", skill_file.parent.name)

        checks["frontmatter_valid"] = bool(metadata.get("name") and desc)
        if not checks["frontmatter_valid"]:
            flaws.append("[DÉTERMINISTE] Frontmatter YAML incomplet (name ou description manquante).")

        checks["max_lines_300"] = len(lines) <= 300
        if not checks["max_lines_300"]:
            flaws.append(f"[DÉTERMINISTE] Dépassement ADR-0202 : {len(lines)} lignes (plafond : 300).")

        checks["max_bytes_15k"] = byte_size <= 15_360
        if not checks["max_bytes_15k"]:
            flaws.append(f"[DÉTERMINISTE] Poids excessif : {byte_size} octets (plafond : 15 Ko).")

        has_absolute_paths = bool(re.search(r"file:///[a-zA-Z]:", content, re.IGNORECASE))
        checks["zero_local_hardcoded_paths"] = not has_absolute_paths
        if not checks["zero_local_hardcoded_paths"]:
            flaws.append("[DÉTERMINISTE] Présence d'hyperliens absolus locaux 'file:///C:' au lieu de chemins relatifs.")

        desc_tokens = cls.estimate_tokens(desc)
        checks["description_budget"] = desc_tokens <= 150
        if not checks["description_budget"]:
            flaws.append(f"[BUDGET JETONS] Description trop verbeuse : {desc_tokens} jetons (max recommandé : 150).")

        dis_inv = metadata.get("disable-model-invocation", "false").lower() == "true"
        if skill_name in HEAVY_META_SKILLS:
            checks["disable_invocation_policy"] = dis_inv
            if not dis_inv:
                flaws.append(f"[SURACTIVATION] Méta-skill lourd '{skill_name}' doit déclarer 'disable-model-invocation: true'.")
        else:
            checks["disable_invocation_policy"] = True

        return checks, flaws

    @classmethod
    def _compute_rubric_scores(
        cls, content: str, metadata: Dict[str, str], det_checks: Dict[str, bool]
    ) -> Tuple[float, Dict[str, float], List[str]]:
        """Calcule les scores pondérés sur la rubrique 100 points Google Agents CLI Eval."""
        recs: List[str] = []
        desc = metadata.get("description", "")
        body = content.split("---", 2)[2] if content.startswith("---") and len(content.split("---")) >= 3 else content

        # Axe 1 : Clarté du Déclencheur & Anti-Suractivation (25 pts)
        a1_score = 25.0
        has_trigger = bool(re.search(r"(?:use when|trigger|quand utiliser|utiliser lorsque|déclencher)", desc, re.IGNORECASE))
        if not has_trigger:
            a1_score -= 10.0
            recs.append("Ajouter une clause de déclenchement explicite ('Use when...') dans la description.")
        if len(desc) < 30:
            a1_score -= 10.0
            recs.append("Description trop succincte pour permettre un routage sémantique précis.")

        # Axe 2 : Rigueur Directive & Déterminisme des Règles (25 pts)
        a2_score = 25.0
        has_ordered_steps = bool(re.search(r"(?:étape|step|\d+\.\s+\*\*|\d+\.\s+`|pipeline)", body, re.IGNORECASE))
        has_rules_or_guards = bool(re.search(r"(?:règle|garde-fou|interdit|obligatoire|rule|do not|never)", body, re.IGNORECASE))
        if not has_ordered_steps:
            a2_score -= 10.0
            recs.append("Structurer le corps du skill avec des étapes séquentielles ordonnées (1, 2, 3).")
        if not has_rules_or_guards:
            a2_score -= 10.0
            recs.append("Formaliser des règles prescriptives et garde-fous explicites.")

        # Axe 3 : Ancrage Vérité Terrain & Zéro Hallucination (25 pts)
        a3_score = 25.0
        has_anchoring = bool(re.search(r"(?:standards/|docs/|Projects/|memory/|tests/|adr-system/|blueprints/)", body))
        has_fact_check = bool(re.search(r"(?:vérité terrain|verbatim|fact-check|preuve|evidence|ssot)", body, re.IGNORECASE))
        if not has_anchoring:
            a3_score -= 12.0
            recs.append("Ancrer le skill sur les chemins canoniques du dépôt (standards/, Projects/, memory/).")
        if not has_fact_check:
            a3_score -= 8.0
            recs.append("Mentionner les sources de vérité terrain et exigences de traçabilité factuelle.")

        # Axe 4 : Confinement, Portabilité & Résilience (25 pts)
        a4_score = 25.0
        if not det_checks.get("zero_local_hardcoded_paths", True):
            a4_score -= 15.0
            recs.append("Remplacer les chemins machine absolus 'file:///C:' par des chemins relatifs au projet.")
        has_fallback_or_errors = bool(re.search(r"(?:erreur|fallback|timeout|échec|si absent|exception|dégradation)", body, re.IGNORECASE))
        if not has_fallback_or_errors:
            a4_score -= 10.0
            recs.append("Spécifier le comportement attendu en cas d'erreur, d'outil absent ou de données manquantes.")

        total_score = round(max(0.0, a1_score) + max(0.0, a2_score) + max(0.0, a3_score) + max(0.0, a4_score), 1)
        breakdown = {
            "trigger_clarity": round(max(0.0, a1_score), 1),
            "rule_determinism": round(max(0.0, a2_score), 1),
            "ground_truth_anchoring": round(max(0.0, a3_score), 1),
            "resilience_and_confinement": round(max(0.0, a4_score), 1),
        }
        return total_score, breakdown, recs

    def evaluate_skill(
        self, skill_file: Path, cases_path: Optional[Path | str] = None
    ) -> SkillEvalResult:
        """Évalue une compétence unique avec couplage Golden Dataset Système 1."""
        content = skill_file.read_text(encoding="utf-8", errors="ignore")
        metadata: Dict[str, str] = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].splitlines():
                    if ":" in line and not line.strip().startswith("#"):
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip().strip("\"'")

        skill_name = metadata.get("name", skill_file.parent.name)
        is_heavy = skill_name in HEAVY_META_SKILLS
        det_checks, flaws = self._run_deterministic_checks(content, metadata, skill_file)
        rubric_score, breakdown, recs = self._compute_rubric_scores(content, metadata, det_checks)

        # Résolution et évaluation du Golden Dataset (ADR-0389)
        resolved_cases = cases_path if isinstance(cases_path, Path) else (
            Path(cases_path) if cases_path else resolve_cases_file(skill_name, self.workspace_root)
        )
        golden_score, golden_detail, golden_flaws, golden_recs = evaluate_golden_dataset(
            skill_name=skill_name,
            manifest_content=content,
            metadata=metadata,
            cases_path=resolved_cases,
            is_heavy_meta=is_heavy,
        )

        flaws.extend(golden_flaws)
        recs.extend(golden_recs)

        # Calcul du score final pondéré (80% Rubrique + 20% Golden Dataset, ou 100% Statique pour méta-skills)
        if is_heavy or golden_score is None:
            final_score = rubric_score
            breakdown["golden_dataset"] = None
        else:
            final_score = round(0.8 * rubric_score + 0.2 * golden_score, 1)
            breakdown["golden_dataset"] = golden_score

        # Détermination du verdict
        if flaws:
            verdict = "FAIL"
        elif final_score >= self.pass_threshold:
            verdict = "PASS"
        elif final_score >= 65.0:
            verdict = "WARNING"
        else:
            verdict = "FAIL"

        token_stats = {
            "description_tokens": self.estimate_tokens(metadata.get("description", "")),
            "body_tokens": self.estimate_tokens(content),
            "line_count": len(content.splitlines()),
            "byte_size": len(content.encode("utf-8")),
        }

        rel_path = skill_file.relative_to(self.workspace_root) if skill_file.is_relative_to(self.workspace_root) else skill_file

        return SkillEvalResult(
            skill_name=skill_name,
            file_path=str(rel_path),
            verdict=verdict,
            total_score=final_score,
            scores_breakdown=breakdown,
            token_stats=token_stats,
            deterministic_checks=det_checks,
            blocking_flaws=flaws,
            recommendations=recs,
            golden_dataset_detail=golden_detail,
        )

    def evaluate_with_golden_dataset(
        self, skill_name: str, cases_path: Optional[Path | str] = None
    ) -> SkillEvalResult:
        """Évalue une compétence spécifique par son nom avec injection du Golden Dataset."""
        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if not skill_file.exists():
            candidates = list(self.skills_dir.glob(f"*{skill_name}*/SKILL.md"))
            if candidates:
                skill_file = candidates[0]
            else:
                raise FileNotFoundError(f"Compétence '{skill_name}' introuvable sous {self.skills_dir}")
        return self.evaluate_skill(skill_file, cases_path=cases_path)

    def evaluate_all_skills(self, skills_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Évalue l'ensemble des compétences sous .agents/skills/."""
        target_dir = Path(skills_dir) if skills_dir else self.skills_dir
        if not target_dir.exists():
            return {"total_skills": 0, "average_score": 0.0, "passed": 0, "warning": 0, "failed": 0, "results": []}

        skill_files = sorted(list(target_dir.glob("*/SKILL.md")))
        results: List[SkillEvalResult] = []
        for sf in skill_files:
            try:
                res = self.evaluate_skill(sf)
                results.append(res)
            except Exception as e:
                logger.error(f"Échec d'évaluation sur {sf} : {e}", exc_info=True)

        passed_count = sum(1 for r in results if r.verdict == "PASS")
        warning_count = sum(1 for r in results if r.verdict == "WARNING")
        failed_count = sum(1 for r in results if r.verdict == "FAIL")
        total = len(results)
        avg_score = round(sum(r.total_score for r in results) / total, 1) if total else 0.0

        return {
            "total_skills": total,
            "average_score": avg_score,
            "pass_threshold": self.pass_threshold,
            "passed": passed_count,
            "warning": warning_count,
            "failed": failed_count,
            "results": [r.to_dict() for r in results],
        }

    def save_reports(self, summary: Dict[str, Any], output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
        """Génère les rapports JSON et Markdown exécutifs sous memory/evals/ (ADR-0389)."""
        out_dir = Path(output_dir) if output_dir else (self.workspace_root / "Projects" / "mLoop" / "memory" / "evals")
        s_json, s_md, _l_json, _l_md = persist_reports(summary, out_dir)
        return s_json, s_md
