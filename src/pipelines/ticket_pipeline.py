"""
Ticket Pipeline - mLoop
Gestion de la distillation de conversations/analyses en spécification (to-spec)
et du découpage en stories tracer-bullet (to-tickets).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import datetime
from src.state import ProjectLayout
from src.utils.blueprints import BlueprintLoader


class TicketPipelineEngine:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.backlog_dir = project_path / ProjectLayout.BACKLOG
        self.stories_dir = self.backlog_dir / "stories"

    def create_spec(self, title: str, overview: str, scope: str, architecture: str, acceptance_criteria: str) -> Path:
        """Génère un fichier de spécification technique dans docs/01-architecture/."""
        docs_dir = self.project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"spec_{title.lower().replace(' ', '_')}.md"
        spec_path = docs_dir / filename
        
        date_str = datetime.date.today().isoformat()
        content = BlueprintLoader.render(
            "project_spec_template.md",
            {
                "TITLE": title,
                "OVERVIEW": overview,
                "SCOPE": scope,
                "ARCHITECTURE": architecture,
                "ACCEPTANCE_CRITERIA": acceptance_criteria,
                "DATE": date_str,
            },
        )
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(content)
        return spec_path

    def decompose_to_tickets(self, spec_path: Path, stories: List[Dict[str, Any]]) -> List[Path]:
        """Découpe une spécification ou document amont en ébauches de récits (Palier 1 DRAFT) dans backlog/stories/."""
        self.stories_dir.mkdir(parents=True, exist_ok=True)
        created_paths = []

        for idx, story in enumerate(stories, 1):
            story_id = f"REC-{idx:03d}"
            clean_title = (
                story["title"].lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
            )
            filename = f"{story_id}_{clean_title}.md"
            story_path = self.stories_dir / filename
            
            blockers = story.get("blocked_by", [])
            blockers_yaml = f"[{', '.join(blockers)}]" if blockers else "[]"
            spec_name = spec_path.name if spec_path else "SPEC_SLICING"
            
            story_content = BlueprintLoader.render(
                "story_draft_template.md",
                {
                    "STORY_ID": story_id,
                    "EPIC_KEY": story.get("epic_key", '""'),
                    "TYPE": story.get("type", "BE"),
                    "TITLE": story["title"],
                    "ORIGIN": story.get("origin", "SPEC_SLICING"),
                    "SOURCE_REF": story.get("source_ref", spec_name),
                    "MACRO_SIZE": story.get("macro_size", "M"),
                    "LAYER": story.get("layer", "backend" if story.get("type", "BE") == "BE" else "fullstack"),
                    "BLOCKERS": blockers_yaml,
                    "CREATED_AT": datetime.date.today().isoformat(),
                    "PERSONA": story.get("persona", "utilisateur ou composant amont"),
                    "WANT": story.get("want", story.get("when", "exécuter la transaction métier")),
                    "SO_THAT": story.get("so_that", story.get("then", "obtenir la valeur métier attendue")),
                    "SOURCE_DOC": story.get("source_doc", spec_name),
                    "ESTIMATE_ASSUMPTION": story.get("estimate_assumption", "Implémentation nominale selon spécification"),
                    "DAYS_RANGE": story.get("days_range", "1-3"),
                    "MACRO_IN_SCOPE": story.get("in_scope", story.get("given", "Composants principaux de la tranche")),
                    "MACRO_OUT_OF_SCOPE": story.get("out_of_scope", "Cas d'usage non critiques hors jalon immédiat"),
                    "SUCCESS_CRITERIA_1": story.get("criteria_1", story.get("then", "Le résultat est sauvegardé avec succès")),
                    "SUCCESS_CRITERIA_2": story.get("criteria_2", "Gestion d'erreur et résilience conformes"),
                    "OPEN_QUESTION_1": story.get("oq_1", "Quelles sont les règles de validation strictes des entrées ?"),
                    "OPEN_QUESTION_2": story.get("oq_2", "Quelles sont les dépendances externes à figer ?"),
                },
            )
            with open(story_path, "w", encoding="utf-8") as f:
                f.write(story_content)
            created_paths.append(story_path)
            
        # Mise à jour du sprint backlog
        self._update_sprint_backlog(created_paths)
        return created_paths

    def _update_sprint_backlog(self, new_stories: List[Path]):
        sprint_file = self.backlog_dir / "sprint_backlog.md"
        if not sprint_file.exists():
            with open(sprint_file, "w", encoding="utf-8") as f:
                f.write("# 🏃 Sprint Backlog\n\n## Stories\n")
            
        with open(sprint_file, "r", encoding="utf-8") as f:
            content = f.read()
        for s in new_stories:
            rel_link = f"- [ ] [DRAFT] [{s.name}](./stories/{s.name})"
            if s.name not in content:
                content += f"\n{rel_link}"
        with open(sprint_file, "w", encoding="utf-8") as f:
            f.write(content)
