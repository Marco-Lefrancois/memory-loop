"""
Skill Impact Tracker & Negative Constraints Registry (WikiSkill Framework).

Consigne l'historique des mutations de compétences (.agents/skills/*/SKILL.md) et des règles RHO :
- Enregistre chaque proposition avec son diff, le score delta obtenu, le verdict (ACCEPTED/REJECTED) et le motif.
- Fournit la liste des contraintes négatives (anti-patterns invalidés) pour interdire au proposant
  de re-tenter des modifications déjà rejetées (Élimination de l'Optimization Amnesia).
- Assure la persistance immuable sous memory/skill_impact.jsonl (Zéro Rollback du journal).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger("core.skill_impact_tracker")


@dataclass
class SkillImpactRecord:
    """Enregistrement unitaire d'un essai de mutation de compétence."""
    timestamp: str
    target_skill: str
    proposed_diff: str
    score_delta: float
    verdict: str  # 'ACCEPTED' | 'REJECTED'
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SkillImpactRecord:
        return cls(
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            target_skill=data.get("target_skill", "unknown"),
            proposed_diff=data.get("proposed_diff", ""),
            score_delta=float(data.get("score_delta", 0.0)),
            verdict=data.get("verdict", "REJECTED"),
            reason=data.get("reason", ""),
            metadata=data.get("metadata", {}),
        )


class SkillImpactTracker:
    """Moteur de traçabilité d'impact et de mémoire négative pour l'évolution de compétences."""

    def __init__(self, workspace_root: Optional[Path | str] = None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    def get_storage_path(self, project_name: Optional[str] = None) -> Path:
        """Retourne le chemin du fichier skill_impact.jsonl (scope projet ou workspace)."""
        if project_name and project_name != "global":
            proj_dir = self.workspace_root / "Projects" / project_name / "memory"
            proj_dir.mkdir(parents=True, exist_ok=True)
            return proj_dir / "skill_impact.jsonl"
        
        global_dir = self.workspace_root / "memory"
        global_dir.mkdir(parents=True, exist_ok=True)
        return global_dir / "skill_impact.jsonl"

    def record_attempt(
        self,
        target_skill: str,
        proposed_diff: str,
        score_delta: float,
        verdict: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        project_name: Optional[str] = None,
    ) -> SkillImpactRecord:
        """
        Enregistre un essai de mutation dans le journal JSONL immuable.
        Le verdict doit être 'ACCEPTED' ou 'REJECTED'.
        """
        verdict_clean = verdict.upper().strip()
        if verdict_clean not in {"ACCEPTED", "REJECTED"}:
            verdict_clean = "REJECTED"

        record = SkillImpactRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            target_skill=target_skill.strip(),
            proposed_diff=proposed_diff.strip(),
            score_delta=float(score_delta),
            verdict=verdict_clean,
            reason=reason.strip(),
            metadata=metadata or {},
        )

        storage_path = self.get_storage_path(project_name)
        with open(storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

        return record

    def get_negative_constraints(
        self,
        target_skill: str,
        limit: int = 10,
        project_name: Optional[str] = None,
    ) -> List[str]:
        """
        Extrait les motifs de rejet et contraintes négatives pour une compétence donnée.
        Permet d'injecter ces anti-patterns dans le prompt d'optimisation (Anti-Amnesia).
        """
        history = self.get_history(
            target_skill=target_skill,
            verdict_filter="REJECTED",
            limit=limit * 2,
            project_name=project_name,
        )

        constraints: List[str] = []
        seen = set()

        for item in reversed(history):  # Du plus récent au plus ancien
            reason = item.get("reason", "").strip()
            diff_summary = item.get("proposed_diff", "").strip()
            if not reason:
                continue

            constraint_text = f"Échec passé (Δscore={item.get('score_delta', 0.0):+.2f}) : {reason}"
            if diff_summary and len(diff_summary) < 120:
                constraint_text += f" [Tentative : {diff_summary}]"

            if constraint_text not in seen:
                seen.add(constraint_text)
                constraints.append(constraint_text)
                if len(constraints) >= limit:
                    break

        return constraints

    def get_history(
        self,
        target_skill: Optional[str] = None,
        verdict_filter: Optional[str] = None,
        limit: int = 50,
        project_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lit l'historique des mutations avec filtres optionnels."""
        storage_path = self.get_storage_path(project_name)
        if not storage_path.exists():
            return []

        results: List[Dict[str, Any]] = []
        try:
            with open(storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if target_skill and entry.get("target_skill") != target_skill:
                            continue
                        if verdict_filter and entry.get("verdict") != verdict_filter.upper():
                            continue
                        results.append(entry)
                    except json.JSONDecodeError as e:
                        logger.debug(
                            "Ligne JSON illisible du registre d'impact skill ignorée",
                            exc_info=True,
                            extra={
                                "component": "core.skill_impact_tracker",
                                "operation": "query_skill_impacts",
                                "error": str(e),
                            },
                        )
        except Exception:
            return []

        return results[-limit:]

    def format_negative_prompt_block(
        self,
        target_skill: str,
        limit: int = 5,
        project_name: Optional[str] = None,
    ) -> str:
        """Formate un bloc Markdown prêt à être injecté dans un prompt de TextGrad/SkillProposer."""
        constraints = self.get_negative_constraints(
            target_skill=target_skill,
            limit=limit,
            project_name=project_name,
        )
        if not constraints:
            return ""

        block = "### 🚫 Contraintes Négatives & Hypothèses Rejetées Passées (WikiSkill Anti-Amnesia) :\n"
        block += "Ne PAS reproduire les modifications suivantes ayant déjà causé des régressions :\n"
        for c in constraints:
            block += f"- {c}\n"
        return block
