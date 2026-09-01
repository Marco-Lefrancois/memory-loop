"""
Moteur de Goal-Cascading & Alignement Stratégique (Inspiré d'Obsidian PKM).

Assure la traçabilité descendante et ascendante :
  Vision Stratégique (3 Ans / Wayfinder)
       ↓
  Initiatives & Décisions (ADR-XXX)
       ↓
  Epics & Thématiques (backlog/epics/)
       ↓
  User Stories INVEST (backlog/stories/)
"""
from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class GoalCascadeEngine:
    """Moteur d'alignement hiérarchique et de traçabilité des objectifs."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)
        self.backlog_dir = self.project_root / "backlog"
        self.stories_dir = self.backlog_dir / "stories"
        self.docs_dir = self.project_root / "docs"

    def audit_cascade_alignment(self) -> Dict[str, Any]:
        """
        Vérifie que chaque User Story est correctement rattachée à une Epic,
        et qu'un arbre d'alignement complet existe.
        """
        stories = list(self.stories_dir.glob("**/*.md")) if self.stories_dir.exists() else []
        
        aligned_count = 0
        orphaned_stories: List[str] = []
        epic_distribution: Dict[str, List[str]] = {}

        for story_path in stories:
            if story_path.name in {"README.md", "TEMPLATE.md"}:
                continue
            
            frontmatter = self._extract_frontmatter(story_path)
            epic_key = frontmatter.get("epic_key") or frontmatter.get("epic") or "UNASSIGNED"
            
            if epic_key != "UNASSIGNED":
                aligned_count += 1
                epic_distribution.setdefault(epic_key, []).append(story_path.stem)
            else:
                orphaned_stories.append(story_path.stem)

        cascade_report = {
            "total_stories": len(stories),
            "aligned_stories": aligned_count,
            "orphaned_stories": orphaned_stories,
            "epic_distribution": epic_distribution,
            "alignment_score": round((aligned_count / max(1, len(stories))) * 100, 1),
        }

        # Génération du rapport de synthèse sous memory/
        self._write_alignment_report(cascade_report)
        return cascade_report

    def _extract_frontmatter(self, file_path: Path) -> Dict[str, Any]:
        """Extrait le Frontmatter YAML d'une story."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    data = yaml.safe_load(parts[1])
                    return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _write_alignment_report(self, report: Dict[str, Any]) -> None:
        """Écrit le rapport d'alignement stratégique sous memory/GOAL_CASCADE_ALIGNMENT.md."""
        memory_dir = self.project_root / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        report_file = memory_dir / "GOAL_CASCADE_ALIGNMENT.md"

        lines = [
            "# 🎯 Rapport d'Alignement Stratégique (Goal Cascading)",
            "",
            f"- **Score d'Alignement Global** : `{report['alignment_score']}%`",
            f"- **Total Récits (INVEST Stories)** : `{report['total_stories']}`",
            f"- **Récits Rattachés à une Epic** : `{report['aligned_stories']}`",
            f"- **Récits Orphelins (Sans Epic)** : `{len(report['orphaned_stories'])}`",
            "",
            "## 📊 Répartition par Epic / Thématique",
            "",
        ]

        for epic, story_list in report["epic_distribution"].items():
            lines.append(f"### 🏷️ Epic : `{epic}` ({len(story_list)} stories)")
            for s in sorted(story_list):
                lines.append(f"- [[{s}]]")
            lines.append("")

        if report["orphaned_stories"]:
            lines.append("## ⚠️ Récits Orphelins à Réaligner")
            lines.append("")
            for s in report["orphaned_stories"]:
                lines.append(f"- ⚠️ `{s}`")
            lines.append("")

        lines.extend([
            "---",
            "*Généré automatiquement par `GoalCascadeEngine` (Memory Loop 2.0).* ",
        ])

        report_file.write_text("\n".join(lines), encoding="utf-8")


def run_goal_cascade(project_root: Path | str) -> Dict[str, Any]:
    """Exécute l'analyse d'alignement Goal-Cascading."""
    engine = GoalCascadeEngine(project_root)
    return engine.audit_cascade_alignment()
