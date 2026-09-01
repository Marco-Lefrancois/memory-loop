import re
from pathlib import Path
from src.cli import ZeroFluffConsole

class StoryEditorEngine:
    """
    Moteur d'édition AST / Section-Aware pour récits Markdown (ADR-0303).
    Permet de modifier une section H2 spécifique d'une story sans dégrader
    le formatage, le YAML frontmatter ou les séparateurs '---'.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def update_section(self, story_rel_path: str, section_title: str, new_section_content: str) -> bool:
        story_file = self.project_path / story_rel_path
        if not story_file.exists():
            ZeroFluffConsole.error(f"Fichier récit introuvable : {story_rel_path}")
            return False

        content = story_file.read_text(encoding="utf-8")
        
        # Normaliser le titre de la section (ex: '## Description' ou 'Description')
        clean_title = section_title.strip()
        if not clean_title.startswith("##"):
            clean_title = f"## {clean_title}"

        # Rechercher la section cible
        pattern = re.compile(rf"(?m)^(---(?:\r?\n)+)?({re.escape(clean_title)}\s*[\s\S]*?)(?=(?:(?:\r?\n)+---(?:\r?\n)+##|\Z))")
        match = pattern.search(content)

        formatted_section = f"\n---\n\n{clean_title}\n{new_section_content.strip()}\n"

        if match:
            # Remplacement déterministe de la section existante
            start_pos = match.start()
            end_pos = match.end()
            updated_content = content[:start_pos] + formatted_section + content[end_pos:]
        else:
            # Ajout en fin de document selon le gabarit
            updated_content = content.rstrip() + "\n" + formatted_section

        story_file.write_text(updated_content, encoding="utf-8")
        ZeroFluffConsole.success(f"Section '{clean_title}' mise à jour de façon AST-déterministe dans {story_file.name}")

        # Auto-healing WikiFix synchrone
        from src.pipelines.wikifix import WikiFixAgent
        from src.state import LoopState
        state = LoopState(project_name=self.project_path.name)
        wikifix = WikiFixAgent()
        wikifix.execute(state, verbose=False)

        return True
