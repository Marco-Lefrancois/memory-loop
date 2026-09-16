"""
Ticket Pipeline - mLoop
Gestion de la distillation de conversations/analyses en spécification (to-spec)
et du découpage en stories tracer-bullet (to-tickets).
"""

from pathlib import Path
from typing import Dict, List, Optional
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

    def decompose_to_tickets(self, spec_path: Path, stories: List[Dict[str, str]]) -> List[Path]:
        """Découpe une spécification en récits tracer-bullet dans backlog/stories/."""
        self.stories_dir.mkdir(parents=True, exist_ok=True)
        created_paths = []

        for idx, story in enumerate(stories, 1):
            story_id = f"REC-{idx:03d}"
            filename = f"{story_id}_{story['title'].lower().replace(' ', '_')}.md"
            story_path = self.stories_dir / filename
            
            blockers = story.get("blocked_by", [])
            blockers_yaml = f"[{', '.join(blockers)}]" if blockers else "[]"
            
            story_content = BlueprintLoader.render(
                "project_tracer_bullet_story_template.md",
                {
                    "STORY_ID": story_id,
                    "TITLE": story["title"],
                    "TYPE": story.get("type", "BE"),
                    "BLOCKERS": blockers_yaml,
                    "CREATED_AT": datetime.date.today().isoformat(),
                    "GIVEN": story.get("given", "un état initial valide et des pré-conditions respectées"),
                    "WHEN": story.get("when", "la transaction métier est exécutée"),
                    "THEN": story.get("then", "le résultat est sauvegardé avec succès et la réponse est confirmée"),
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
            rel_link = f"- [ ] [{s.name}](./stories/{s.name})"
            if rel_link not in content:
                content += f"\n{rel_link}"
        with open(sprint_file, "w", encoding="utf-8") as f:
            f.write(content)
