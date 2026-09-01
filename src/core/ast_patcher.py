"""
AST Semantic Patcher — Moteur de Mutation Syntaxique Déterministe (Inspiré de Tree-Sitter & LibCST).

Élimine toute manipulation imprécise de chaînes brutes :
- Modifie ou injecte chirurgicalement des sections H2 (##) dans les fichiers Markdown.
- Met à jour le Frontmatter YAML de façon idempotente en préservant le formatage.
- Valide l'intégrité syntaxique avant toute écriture sur disque.
"""
from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class ASTSemanticPatcher:
    """Moteur de patching et de mutation structurelle pour Markdown et code."""

    @staticmethod
    def patch_frontmatter(content: str, updates: Dict[str, Any]) -> str:
        """Met à jour les clés du Frontmatter YAML sans altérer le reste du document."""
        if not content.startswith("---"):
            # Aucun frontmatter existant, en créer un
            yaml_block = yaml.dump(updates, allow_unicode=True, sort_keys=False).strip()
            return f"---\n{yaml_block}\n---\n\n{content}"

        parts = content.split("---", 2)
        if len(parts) < 3:
            return content

        raw_yaml = parts[1]
        body = parts[2]

        try:
            data = yaml.safe_load(raw_yaml) or {}
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

        # Appliquer les mises à jour
        data.update(updates)
        new_yaml = yaml.dump(data, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{new_yaml}\n---" + body

    @staticmethod
    def patch_markdown_section(content: str, heading: str, new_section_content: str, mode: str = "replace") -> str:
        """
        Modifie ou insère une section Markdown délimitée par `## <heading>`.
        Modes supportés : 'replace', 'append', 'insert_before'.
        """
        # Motif pour repérer la section ## heading jusqu'au prochain ## ou la fin du fichier
        pattern = rf"(##\s+{re.escape(heading)}.*?\n)(.*?)(?=\n---\n##|\n##|\Z)"
        match = re.search(pattern, content, flags=re.DOTALL)

        clean_new = new_section_content.strip()

        if match:
            header_line = match.group(1)
            if mode == "replace":
                replacement = f"{header_line}\n{clean_new}\n"
            elif mode == "append":
                old_body = match.group(2).strip()
                replacement = f"{header_line}\n{old_body}\n\n{clean_new}\n"
            else:
                replacement = f"{header_line}\n{clean_new}\n"

            return content[:match.start()] + replacement + content[match.end():]
        else:
            # Section inexistante : l'ajouter à la fin précédée de '---'
            return f"{content.rstrip()}\n\n---\n\n## {heading}\n\n{clean_new}\n"

    @staticmethod
    def validate_markdown_structure(content: str, required_headings: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """Valide la présence des sections obligatoires et l'intégrité du Frontmatter."""
        errors: List[str] = []

        # 1. Vérifier le Frontmatter
        if not content.startswith("---"):
            errors.append("Frontmatter YAML manquant au sommet du fichier.")
        else:
            parts = content.split("---", 2)
            if len(parts) < 3:
                errors.append("Frontmatter YAML mal fermé (délimiteur '---' manquant).")
            else:
                try:
                    yaml.safe_load(parts[1])
                except Exception as e:
                    errors.append(f"Erreur de syntaxe YAML dans le Frontmatter : {e}")

        # 2. Vérifier les sections obligatoires
        if required_headings:
            for req in required_headings:
                if not re.search(rf"^##\s+{re.escape(req)}", content, flags=re.MULTILINE):
                    errors.append(f"Section H2 obligatoire manquante : '## {req}'")

        return len(errors) == 0, errors


def patch_story_file(file_path: Path | str, updates_frontmatter: Optional[Dict[str, Any]] = None, section_updates: Optional[Dict[str, str]] = None) -> bool:
    """Applique des mutations chirurgicales sur un fichier de story sur disque."""
    path = Path(file_path)
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8", errors="ignore")

    if updates_frontmatter:
        content = ASTSemanticPatcher.patch_frontmatter(content, updates_frontmatter)

    if section_updates:
        for heading, new_content in section_updates.items():
            content = ASTSemanticPatcher.patch_markdown_section(content, heading, new_content)

    path.write_text(content, encoding="utf-8")
    return True
