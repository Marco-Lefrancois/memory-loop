# -*- coding: utf-8 -*-
"""
Parent Document Resolver Engine (mLoop Core - ADR-0328).

Inspiré du Parent Document Retrieval (Decoding AI / Aug 2026) :
Permet de résoudre le bloc parent englobant (Section H2/H3 complète,
paragraphes d'introduction et règles soeurs) à partir d'un fragment ou d'une règle isolée.
Évite la perte de contexte dans le RAG Graphify et les EvidencePacks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class ParentContextBlock:
    """Bloc de contexte parent résolu avec sa hiérarchie complète."""
    document_name: str
    section_path: str
    parent_heading: str
    full_parent_content: str
    target_snippet: str
    sibling_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_name": self.document_name,
            "section_path": self.section_path,
            "parent_heading": self.parent_heading,
            "full_parent_content": self.full_parent_content,
            "target_snippet": self.target_snippet,
            "sibling_rules": self.sibling_rules,
            "metadata": self.metadata,
        }


class ParentDocumentResolver:
    """Moteur de résolution et de remontée de contexte parent."""

    def __init__(self, project_path: Optional[Path | str] = None) -> None:
        self.project_path = Path(project_path) if project_path else Path(".")

    def resolve_from_file(self, file_path: Path | str, target_snippet: str) -> Optional[ParentContextBlock]:
        """Résout le bloc parent d'un extrait dans un fichier Markdown physique."""
        path = Path(file_path)
        if not path.is_absolute() and self.project_path:
            alt = self.project_path / file_path
            if alt.exists():
                path = alt
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8", errors="ignore")
        return self.resolve_from_text(content, target_snippet, document_name=path.name)

    def resolve_from_text(self, document_text: str, target_snippet: str, document_name: str = "document") -> Optional[ParentContextBlock]:
        """Parse le texte Markdown en sections hiérarchiques et localise le parent du snippet."""
        if not document_text or not target_snippet:
            return None

        lines = document_text.splitlines()
        sections = self._parse_sections(lines, document_name)

        # Chercher la section qui contient le snippet cible
        clean_target = target_snippet.strip().lower()
        
        for sec in sections:
            sec_content_lower = sec["content"].lower()
            if clean_target in sec_content_lower or any(clean_target in line.lower() for line in sec["lines"]):
                # Extraire les règles soeurs (puces ou paragraphes numérotés)
                siblings = []
                for l in sec["lines"]:
                    stripped = l.strip()
                    if stripped.startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5.")):
                        clean_l = stripped.lstrip("-*• 0123456789.").strip()
                        if clean_l and clean_l.lower() != clean_target:
                            siblings.append(clean_l)

                return ParentContextBlock(
                    document_name=document_name,
                    section_path=sec["path"],
                    parent_heading=sec["title"],
                    full_parent_content=sec["content"],
                    target_snippet=target_snippet,
                    sibling_rules=siblings,
                    metadata={"level": sec["level"], "lines_count": len(sec["lines"])},
                )

        return None

    def _parse_sections(self, lines: List[str], doc_name: str) -> List[Dict[str, Any]]:
        """Découpe les lignes en sections hiérarchiques (H1, H2, H3)."""
        sections: List[Dict[str, Any]] = []
        current_section = {
            "title": doc_name,
            "path": doc_name,
            "level": 0,
            "lines": [],
            "content": "",
        }
        header_stack: List[str] = []

        for line in lines:
            stripped = line.strip()
            header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            
            if header_match:
                # Flush la section précédente si elle contient des lignes
                if current_section["lines"]:
                    current_section["content"] = "\n".join(current_section["lines"])
                    sections.append(current_section)

                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                if level <= len(header_stack):
                    header_stack = header_stack[:level - 1]
                header_stack.append(title)
                current_path = " > ".join(header_stack)

                current_section = {
                    "title": title,
                    "path": current_path,
                    "level": level,
                    "lines": [line],
                    "content": "",
                }
            else:
                current_section["lines"].append(line)

        if current_section["lines"]:
            current_section["content"] = "\n".join(current_section["lines"])
            sections.append(current_section)

        return sections
