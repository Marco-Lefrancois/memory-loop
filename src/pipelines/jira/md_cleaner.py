"""
Sous-module Jira : md_cleaner.py
Responsabilité : Chargement et nettoyage des descriptions Markdown locales
avant envoi vers l'API Jira Cloud.
"""
import logging
import re
from pathlib import Path
from src.state import ProjectLayout

logger = logging.getLogger(__name__)


def load_rich_description(project_path: Path, relative_path_str: str, default_desc: str) -> str:
    """
    Charge le fichier Markdown de backlog correspondant au chemin exact (qui était stocké dans description).
    """
    backlog_dir = project_path / ProjectLayout.BACKLOG
    exact_file = backlog_dir / relative_path_str
    if exact_file.exists():
        try:
            return exact_file.read_text(encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Erreur lecture {exact_file}: {exc}", exc_info=True)
    return default_desc


def clean_markdown_description(md: str) -> str:
    """
    Supprime le bloc Frontmatter YAML, les en-têtes redondants de titre de Story,
    de Statut et de titre de Description présents dans les fichiers Markdown,
    ainsi que la section réservée aux agents IA (Notes de Traçabilité).
    """
    # 0. Supprimer la section de Traçabilité / Notes réservées aux agents IA (jusqu'à la fin ou section suivante)
    md = re.sub(r'(?ms)^##\s+(?:📑\s*)?Notes de Traçabilité.*$', '', md)
    md = re.sub(r'(?ms)<!--\s*AGENT_NOTES.*?-->', '', md)

    # 1. Supprimer le Frontmatter YAML (tout ce qui est entre les premiers ---)
    if md.startswith("---"):
        parts = md.split("---", 2)
        if len(parts) >= 3:
            md = parts[2]

    lines = md.splitlines()
    cleaned_lines = []

    skip_h1 = True
    skip_statut = True
    skip_desc = True

    for line in lines:
        stripped = line.strip()

        # 1. Skip H1 Story header (ex: # [M] STORY-001 ...)
        if skip_h1 and stripped.startswith("#") and not stripped.startswith("##"):
            skip_h1 = False
            continue

        # 2. Skip Statut header (ex: ## Statut : ...)
        if skip_statut and stripped.startswith("##") and "Statut" in stripped:
            skip_statut = False
            continue

        # 3. Skip Description header (ex: ## Description)
        if skip_desc and stripped.startswith("##") and "Description" in stripped:
            skip_desc = False
            continue

        cleaned_lines.append(line)

    # Retirer les lignes vides au début et à la fin
    while cleaned_lines and cleaned_lines[0].strip() == "":
        cleaned_lines.pop(0)
    while cleaned_lines and cleaned_lines[-1].strip() == "":
        cleaned_lines.pop()

    return "\n".join(cleaned_lines)

