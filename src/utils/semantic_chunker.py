# -*- coding: utf-8 -*-
"""
Semantic Chunker Engine (mLoop Core - ADR-0323).

Découpeur sémantique conscient de la structure documentaire Markdown :
- Préserve l'intégrité absolue des tableaux Markdown (|---|---|).
- Préserve les blocs de code et admonitions GitHub ([!NOTE], [!WARNING]).
- Conserve le fil d'Ariane hiérarchique (Header Breadcrumb Path : H1 > H2 > H3).
- Évite les ruptures arbitraires par caractères ou par lignes fixes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class SemanticChunk:
    """Représente un fragment sémantique unitaire avec son contexte structurel."""
    chunk_id: str
    content: str
    header_path: str
    section_title: str
    chunk_type: str  # "text", "table", "code", "admonition"
    char_count: int
    token_estimate: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "header_path": self.header_path,
            "section_title": self.section_title,
            "chunk_type": self.chunk_type,
            "char_count": self.char_count,
            "token_estimate": self.token_estimate,
            "metadata": self.metadata,
        }


class MarkdownSemanticChunker:
    """Moteur de découpage sémantique Markdown respectant la hiérarchie et les blocs atomiques."""

    def __init__(
        self,
        max_chunk_chars: int = 1500,
        min_chunk_chars: int = 150,
        overlap_chars: int = 100,
    ) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_file(self, file_path: str | Path) -> List[SemanticChunk]:
        """Découpe un fichier Markdown physique en chunks sémantiques."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")
        text = path.read_text(encoding="utf-8")
        return self.chunk_text(text, source_name=path.stem)

    def chunk_text(self, text: str, source_name: str = "document") -> List[SemanticChunk]:
        """Découpe un texte Markdown en une séquence ordonnée de SemanticChunk."""
        if not text or not text.strip():
            return []

        lines = text.splitlines()
        raw_blocks = self._parse_blocks(lines)
        
        chunks: List[SemanticChunk] = []
        current_chunk_blocks: List[Dict[str, Any]] = []
        current_char_count = 0
        current_header_path = ""
        current_section_title = source_name
        chunk_counter = 1

        def flush_chunk():
            nonlocal chunk_counter, current_chunk_blocks, current_char_count
            if not current_chunk_blocks:
                return

            # Détermination du type prédominant
            types = [b["type"] for b in current_chunk_blocks]
            predominant_type = "text"
            if "table" in types and len(types) == 1:
                predominant_type = "table"
            elif "code" in types and len(types) == 1:
                predominant_type = "code"
            elif "admonition" in types and len(types) == 1:
                predominant_type = "admonition"

            combined_text = "\n\n".join(b["content"] for b in current_chunk_blocks).strip()
            
            if combined_text:
                chunk = SemanticChunk(
                    chunk_id=f"{source_name}_chunk_{chunk_counter:03d}",
                    content=combined_text,
                    header_path=current_header_path or source_name,
                    section_title=current_section_title,
                    chunk_type=predominant_type,
                    char_count=len(combined_text),
                    token_estimate=max(1, len(combined_text) // 4),
                    metadata={
                        "blocks_count": len(current_chunk_blocks),
                        "source": source_name,
                    },
                )
                chunks.append(chunk)
                chunk_counter += 1

            current_chunk_blocks = []
            current_char_count = 0

        for block in raw_blocks:
            b_type = block["type"]
            b_content = block["content"]
            b_len = len(b_content)
            b_path = block.get("header_path", current_header_path)
            b_title = block.get("section_title", current_section_title)

            # Si le bloc est un en-tête H1 ou H2 majeur et qu'on a déjà du contenu, on flush
            if b_type == "header" and block.get("level", 3) <= 2 and current_chunk_blocks:
                flush_chunk()
                current_header_path = b_path
                current_section_title = b_title
                continue
            elif b_type == "header":
                current_header_path = b_path
                current_section_title = b_title
                # On ajoute le titre au début du prochain chunk
                current_chunk_blocks.append(block)
                current_char_count += b_len
                continue

            # Si le bloc est un tableau ou un bloc de code atomique
            if b_type in ("table", "code"):
                # Si le bloc seul dépasse max_chunk_chars, on le conserve tout de même entier (atomicité)
                if current_char_count + b_len > self.max_chunk_chars and current_chunk_blocks:
                    flush_chunk()
                current_chunk_blocks.append(block)
                current_char_count += b_len
                # Si c'est un gros tableau, on flush immédiatement pour ne pas l'amalgamer avec d'autres blocs
                if b_len >= self.min_chunk_chars:
                    flush_chunk()
                continue

            # Paragraphe ou liste standard
            if current_char_count + b_len > self.max_chunk_chars and current_chunk_blocks:
                flush_chunk()

            current_chunk_blocks.append(block)
            current_char_count += b_len
            current_header_path = b_path
            current_section_title = b_title

        flush_chunk()
        return chunks

    def _parse_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse les lignes Markdown en blocs structurels (headers, tables, code, admonitions, paragraphes)."""
        blocks: List[Dict[str, Any]] = []
        i = 0
        n = len(lines)
        
        header_stack: List[str] = []

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # 1. Ligne vide
            if not stripped:
                i += 1
                continue

            # 2. En-tête Markdown (#, ##, ###)
            header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                # Mise à jour du fil d'Ariane
                if level <= len(header_stack):
                    header_stack = header_stack[:level - 1]
                header_stack.append(title)
                current_path = " > ".join(header_stack)

                blocks.append({
                    "type": "header",
                    "level": level,
                    "title": title,
                    "header_path": current_path,
                    "section_title": title,
                    "content": line,
                })
                i += 1
                continue

            current_path = " > ".join(header_stack) if header_stack else ""
            current_title = header_stack[-1] if header_stack else ""

            # 3. Bloc de Code (```)
            if stripped.startswith("```"):
                code_lines = [line]
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                if i < n:
                    code_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": "code",
                    "content": "\n".join(code_lines),
                    "header_path": current_path,
                    "section_title": current_title,
                })
                continue

            # 4. Tableau Markdown (|...|)
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines = [line]
                i += 1
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": "table",
                    "content": "\n".join(table_lines),
                    "header_path": current_path,
                    "section_title": current_title,
                })
                continue

            # 5. Admonition GitHub (> [!NOTE], > [!WARNING], etc.)
            if stripped.startswith("> [!"):
                admon_lines = [line]
                i += 1
                while i < n and (lines[i].strip().startswith(">") or lines[i].strip() == ""):
                    if lines[i].strip() == "" and (i + 1 < n and not lines[i+1].strip().startswith(">")):
                        break
                    admon_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": "admonition",
                    "content": "\n".join(admon_lines),
                    "header_path": current_path,
                    "section_title": current_title,
                })
                continue

            # 6. Paragraphe standard / Liste
            para_lines = [line]
            i += 1
            while i < n:
                next_stripped = lines[i].strip()
                if not next_stripped:
                    break
                if next_stripped.startswith(("#", "```", "> [!")) or (next_stripped.startswith("|") and next_stripped.endswith("|")):
                    break
                para_lines.append(lines[i])
                i += 1

            blocks.append({
                "type": "text",
                "content": "\n".join(para_lines),
                "header_path": current_path,
                "section_title": current_title,
            })

        return blocks
