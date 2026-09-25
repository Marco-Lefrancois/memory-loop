# -*- coding: utf-8 -*-
"""
skill_flywheel.py — Boucle d'Amélioration Fermée des Compétences Agentiques (Eval Flywheel).
Couple SkillEvalEngine, SkillAutoTuner et SkillImpactTracker avec protection HITL inviolable.
Conforme ADR-0202 (<= 300 lignes), ADR-0348, ADR-0369 et ADR-0389.
"""

from __future__ import annotations

import difflib
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.skill_impact_tracker import SkillImpactTracker
from src.pipelines.skill_auto_tuner import SkillAutoTuner
from src.pipelines.skill_eval import SkillEvalEngine
from src.utils.logger import get_logger

logger = get_logger("pipelines.skill_flywheel")


class SkillFlywheel:
    """Orchestrateur de la boucle fermée d'auto-évaluation et d'auto-étalonnage des compétences."""

    def __init__(
        self,
        workspace_root: Path | str = ".",
        max_iterations: int = 3,
        pass_threshold: float = 80.0,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.max_iterations = max_iterations
        self.pass_threshold = pass_threshold
        self.skills_dir = self.workspace_root / ".agents" / "skills"
        self.eval_engine = SkillEvalEngine(workspace_root=self.workspace_root, pass_threshold=self.pass_threshold)
        self.auto_tuner = SkillAutoTuner(workspace_root=self.workspace_root)
        self.tracker = SkillImpactTracker(workspace_root=self.workspace_root)

    def get_pending_patches_dir(self) -> Path:
        """Résout le dossier de stockage des propositions HITL (inviolabilité de production)."""
        candidates = [
            self.workspace_root / "Projects" / "mLoop" / "memory" / "evals" / "pending_patches",
            self.workspace_root / "memory" / "evals" / "pending_patches",
        ]
        for c in candidates:
            if c.parent.exists():
                c.mkdir(parents=True, exist_ok=True)
                return c
        candidates[0].mkdir(parents=True, exist_ok=True)
        return candidates[0]

    def _propose_candidate(
        self,
        skill_name: str,
        initial_content: str,
        recs: List[str],
        negative_constraints: List[str],
    ) -> Optional[str]:
        """Génère une proposition de mutation de manifeste sans toucher au fichier physique."""
        if initial_content.startswith("---"):
            parts = initial_content.split("---", 2)
            header = f"---{parts[1]}---\n"
            body = parts[2] if len(parts) >= 3 else ""
        else:
            header, body = "", initial_content

        feedback = " ; ".join(recs) if recs else "Améliorer les règles et l'ancrage canonique."
        tuned = self.auto_tuner._apply_textgrad_refinements(body, feedback, negative_constraints)
        neg_text = " ".join(negative_constraints).lower()
        additions = []

        if any("étapes" in r.lower() or "ordonnées" in r.lower() for r in recs) and "pipeline" not in neg_text:
            additions.append("\n## Pipeline d'exécution\n1. Étape 1 : Analyse du contexte.\n2. Étape 2 : Exécution (règle obligatoire).")
        if any("règles" in r.lower() or "garde-fous" in r.lower() for r in recs) and "règles" not in neg_text:
            additions.append("\n## Règles et Garde-fous\n- Règle obligatoire : Confinement strict.\n- Garde-fou : Zéro hallucination.")
        if any("canoniques" in r.lower() or "ancrer" in r.lower() for r in recs) and "standards/" not in neg_text:
            additions.append("\n## Ancrage Canonique\n- Chemins SSOT : standards/, Projects/, memory/.")
        if any("vérité terrain" in r.lower() or "traçabilité" in r.lower() for r in recs) and "vérité" not in neg_text:
            additions.append("\n## Traçabilité Factuelle\n- Vérité terrain et preuves d'exécution exigées (verbatim).")
        if any("erreur" in r.lower() or "fallback" in r.lower() for r in recs) and "fallback" not in neg_text:
            additions.append("\n## Résilience & Mode Dégradé\n- Gestion des erreurs : fallback et dégradation gracieuse en cas de timeout.")

        if additions:
            tuned = tuned.rstrip() + "\n" + "\n".join(additions) + "\n"

        candidate = header + tuned
        return candidate if self.auto_tuner._validate_structure(candidate) else None

    def _evaluate_candidate_in_memory(self, skill_name: str, candidate_content: str) -> float:
        """Évalue une mutation candidate dans un fichier temporaire isolé."""
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tf:
            tf.write(candidate_content)
            temp_path = Path(tf.name)
        try:
            cases_path = self.workspace_root / "Projects" / "mLoop" / "memory" / "evals" / "skills" / skill_name / "cases.json"
            if not cases_path.exists():
                cases_path = self.workspace_root / "memory" / "evals" / "skills" / skill_name / "cases.json"
            res = self.eval_engine.evaluate_skill(temp_path, cases_path=cases_path if cases_path.exists() else None)
            return res.total_score
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def run_cycle_for_skill(
        self,
        skill_name: str,
        current_score: float,
        recs: List[str],
        project_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exécute les itérations d'optimisation bornées (max 3) pour une compétence."""
        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if not skill_file.exists():
            return {"skill": skill_name, "status": "NOT_FOUND"}

        initial_content = skill_file.read_text(encoding="utf-8", errors="ignore")

        for iteration in range(1, self.max_iterations + 1):
            neg_constraints = self.tracker.get_negative_constraints(
                target_skill=skill_name, limit=5, project_name=project_name
            )
            candidate = self._propose_candidate(skill_name, initial_content, recs, neg_constraints)
            if not candidate:
                self.tracker.record_attempt(
                    target_skill=skill_name,
                    proposed_diff=f"Itération {iteration}: échec structurel",
                    score_delta=-1.0,
                    verdict="REJECTED",
                    reason="Structure invalide ou frontmatter corrompu",
                    metadata={"action": "rollback", "iteration": iteration},
                    project_name=project_name,
                )
                continue

            candidate_score = self._evaluate_candidate_in_memory(skill_name, candidate)
            delta = round(candidate_score - current_score, 1)

            if delta > 0.0:
                patches_dir = self.get_pending_patches_dir()
                patch_file = patches_dir / f"{skill_name}_patch.md"
                diff_lines = list(difflib.unified_diff(
                    initial_content.splitlines(keepends=True),
                    candidate.splitlines(keepends=True),
                    fromfile="a/SKILL.md",
                    tofile="b/SKILL.md",
                ))
                diff_text = "".join(diff_lines)

                patch_document = (
                    f"---\nskill_name: {skill_name}\nscore_before: {current_score}\n"
                    f"score_after: {candidate_score}\ndelta_score: {delta}\n"
                    f"iteration: {iteration}\ntimestamp: '{datetime.now(timezone.utc).isoformat()}'\n"
                    f"status: PENDING_HITL\n---\n\n"
                    f"# Proposition de Patch HITL — `{skill_name}` (Δscore : +{delta})\n\n"
                    f"```diff\n{diff_text}\n```\n\n## Contenu Proposé\n\n```markdown\n{candidate}\n```\n"
                )
                patch_file.write_text(patch_document, encoding="utf-8")

                self.tracker.record_attempt(
                    target_skill=skill_name,
                    proposed_diff=f"Patch HITL proposé itération {iteration} (+{delta} pts)",
                    score_delta=delta,
                    verdict="ACCEPTED",
                    reason=f"Amélioration de score validée ({current_score} -> {candidate_score})",
                    metadata={"action": "patch_proposed", "status": "PENDING_HITL", "iteration": iteration, "patch_file": str(patch_file)},
                    project_name=project_name,
                )
                return {
                    "skill": skill_name,
                    "status": "PROPOSED",
                    "iteration": iteration,
                    "score_before": current_score,
                    "score_after": candidate_score,
                    "delta_score": delta,
                    "patch_file": str(patch_file),
                }

            self.tracker.record_attempt(
                target_skill=skill_name,
                proposed_diff=f"Tentative itération {iteration} (rejet Δscore={delta:+.1f})",
                score_delta=delta,
                verdict="REJECTED",
                reason="Régression ou absence de gain mesurable",
                metadata={"action": "rollback", "iteration": iteration},
                project_name=project_name,
            )

        self.tracker.record_attempt(
            target_skill=skill_name,
            proposed_diff="Seuil maximal d'itérations atteint sans gain",
            score_delta=0.0,
            verdict="REJECTED",
            reason=f"Plafond de {self.max_iterations} itérations atteint sans gain de score",
            metadata={"action": "max_iterations_reached"},
            project_name=project_name,
        )
        return {
            "skill": skill_name,
            "status": "NEEDS_HUMAN_REVIEW",
            "iterations_exhausted": self.max_iterations,
            "score_before": current_score,
        }

    def run_flywheel(
        self,
        eval_summary: Optional[Dict[str, Any]] = None,
        target_skill: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exécute la boucle Flywheel complète sur les compétences nécessitant une optimisation."""
        if not eval_summary:
            eval_summary = self.eval_engine.evaluate_all_skills()

        results_list = eval_summary.get("results", [])
        if target_skill:
            results_list = [r for r in results_list if r.get("skill_name") == target_skill]

        degraded = [
            r for r in results_list
            if r.get("verdict") in ("FAIL", "WARNING") or r.get("total_score", 0.0) < self.pass_threshold
        ]

        proposals, needs_review = [], []
        for deg in degraded:
            cycle_res = self.run_cycle_for_skill(
                deg["skill_name"], deg["total_score"], deg.get("recommendations", []), project_name=project_name
            )
            if cycle_res["status"] == "PROPOSED":
                proposals.append(cycle_res)
            elif cycle_res["status"] == "NEEDS_HUMAN_REVIEW":
                needs_review.append(cycle_res)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_degraded": len(degraded),
            "proposals_generated": proposals,
            "needs_human_review": needs_review,
        }

    def apply_pending_patch(
        self, skill_name: str, force: bool = False, project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Applique formellement une proposition HITL validée par l'humain sur le SKILL.md de production."""
        patches_dir = self.get_pending_patches_dir()
        patch_file = patches_dir / f"{skill_name}_patch.md"
        if not patch_file.exists():
            return {"success": False, "error": f"Aucun patch en attente pour '{skill_name}' : {patch_file}"}

        patch_content = patch_file.read_text(encoding="utf-8")
        match = re.search(r"## Contenu Proposé\s*\n\s*```markdown\n(.*?)\n```", patch_content, re.DOTALL)
        if not match:
            return {"success": False, "error": "Format de patch invalide : section 'Contenu Proposé' introuvable."}

        new_manifest = match.group(1).strip() + "\n"
        target_file = self.skills_dir / skill_name / "SKILL.md"
        if not target_file.exists():
            return {"success": False, "error": f"Fichier cible introuvable : {target_file}"}

        target_file.write_text(new_manifest, encoding="utf-8")
        patch_file.unlink(missing_ok=True)

        self.tracker.record_attempt(
            target_skill=skill_name,
            proposed_diff="Application formelle du patch HITL validé par l'humain",
            score_delta=1.0,
            verdict="ACCEPTED",
            reason="Patch validé et appliqué formellement par commande souveraine",
            metadata={"action": "patch_applied", "status": "APPLIED"},
            project_name=project_name,
        )
        return {"success": True, "skill": skill_name, "applied": True, "target": str(target_file)}
