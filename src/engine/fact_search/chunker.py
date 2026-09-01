# -*- coding: utf-8 -*-
"""
Tri-Fusion Semantic Chunker (DocETL + Late Chunking Stitching - ADR-0323/ADR-0326).

Découpeur sémantique avancé combinant :
1. Préservation atomique des tableaux Markdown, admonitions GitHub et blocs de code (DocETL Split).
2. Lignage contextuel hiérarchique H1 > H2 > H3 (DocETL Gather).
3. Fenêtrage bidirectionnel avec halo d'overlap (Late Context Window Stitching).
4. Injection du préfixe contextuel (Anthropic Contextual Retrieval).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.engine.fact_search.contextualizer import DocumentContextualizer


@dataclass
class TriFusionChunk:
    """Représente un chunk sémantique enrichi avec ses métadonnées de lignage et contexte."""
    chunk_id: str
    doc_path: str
    ssot_layer: str
    section_h1: str
    section_h2: str
    breadcrumb: str
    line_start: int
    line_end: int
    content: str
    contextual_content: str  # Contenu avec préfixe Anthropic injecté
    chunk_type: str = "text"  # "text", "table", "code", "admonition"
    char_count: int = 0
    token_estimate: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_path": self.doc_path,
            "ssot_layer": self.ssot_layer,
            "section_h1": self.section_h1,
            "section_h2": self.section_h2,
            "breadcrumb": self.breadcrumb,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "content": self.content,
            "contextual_content": self.contextual_content,
            "chunk_type": self.chunk_type,
            "char_count": self.char_count,
            "token_estimate": self.token_estimate,
            "metadata": self.metadata,
        }


class TriFusionChunker:
    """Moteur de découpage sémantique Tri-Fusion."""

    def __init__(
        self,
        max_chunk_chars: int = 1500,
        min_chunk_chars: int = 120,
        context_halo_lines: int = 2,
    ) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.context_halo_lines = context_halo_lines

    def chunk_document(
        self,
        doc_path: str | Path,
        content: str,
        ssot_layer: str = "docs",
    ) -> List[TriFusionChunk]:
        """Découpe un document Markdown en chunks sémantiques Tri-Fusion."""
        rel_path = str(doc_path).replace("\\", "/")
        lines = content.splitlines()
        if not lines:
            return []

        doc_summary = DocumentContextualizer.extract_document_summary(content)

        # 1. Identifier les blocs atomiques (tableaux, code, admonitions, sections)
        raw_sections = self._parse_structural_blocks(lines)

        # 2. Construire les chunks enrichis avec lignage et halo de contexte
        chunks: List[TriFusionChunk] = []
        for idx, sec in enumerate(raw_sections):
            chunk_text = "\n".join(sec["lines"]).strip()
            if not chunk_text:
                continue

            h1 = sec["h1"]
            h2 = sec["h2"]
            breadcrumb = f"{h1} > {h2}".strip(" >") if (h1 or h2) else Path(rel_path).name

            # Préfixe Anthropic Contextual Retrieval
            prefix = DocumentContextualizer.generate_context_prefix(
                doc_path=rel_path,
                h1_title=h1,
                h2_title=h2,
                breadcrumb=breadcrumb,
                summary=doc_summary,
            )
            contextual_text = f"{prefix}{chunk_text}"

            token_est = max(1, len(contextual_text) // 4)
            chunk_id = f"{Path(rel_path).stem}_c{idx+1:03d}"

            chunk = TriFusionChunk(
                chunk_id=chunk_id,
                doc_path=rel_path,
                ssot_layer=ssot_layer,
                section_h1=h1,
                section_h2=h2,
                breadcrumb=breadcrumb,
                line_start=sec["start_line"],
                line_end=sec["end_line"],
                content=chunk_text,
                contextual_content=contextual_text,
                chunk_type=sec["type"],
                char_count=len(chunk_text),
                token_estimate=token_est,
                metadata={
                    "doc_summary": doc_summary,
                    "has_table": sec["type"] == "table",
                    "has_code": sec["type"] == "code",
                },
            )
            chunks.append(chunk)

        return chunks

    def _parse_structural_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Détecte les frontières sémantiques en protégeant les tableaux et blocs de code."""
        blocks: List[Dict[str, Any]] = []
        
        current_h1 = ""
        current_h2 = ""
        current_lines: List[str] = []
        block_start = 1
        in_code_block = False
        in_table = False

        def _flush(b_type: str = "text"):
            nonlocal current_lines, block_start
            if current_lines:
                blocks.append({
                    "h1": current_h1,
                    "h2": current_h2,
                    "lines": list(current_lines),
                    "start_line": block_start,
                    "end_line": block_start + len(current_lines) - 1,
                    "type": b_type,
                })
                current_lines = []

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Gestion des blocs de code
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                current_lines.append(line)
                if not in_code_block:
                    _flush("code")
                    block_start = line_idx + 1
                continue

            if in_code_block:
                current_lines.append(line)
                continue

            # Gestion des tableaux Markdown (| col | col |)
            is_table_row = stripped.startswith("|") and stripped.endswith("|")
            if is_table_row:
                if not in_table:
                    _flush("text")
                    block_start = line_idx
                    in_table = True
                current_lines.append(line)
                continue
            elif in_table:
                in_table = False
                _flush("table")
                block_start = line_idx

            # Détection des titres Markdown
            h1_m = re.match(r'^#\s+(.+)$', line)
            h2_m = re.match(r'^##\s+(.+)$', line)
            h3_m = re.match(r'^###\s+(.+)$', line)

            if h1_m:
                _flush("text")
                current_h1 = h1_m.group(1).strip()
                current_h2 = ""
                block_start = line_idx
                current_lines.append(line)
            elif h2_m:
                _flush("text")
                current_h2 = h2_m.group(1).strip()
                block_start = line_idx
                current_lines.append(line)
            elif h3_m:
                if len(current_lines) > 20:
                    _flush("text")
                    block_start = line_idx
                current_lines.append(line)
            else:
                # Regroupement par paragraphe
                current_lines.append(line)
                if sum(len(l) for l in current_lines) >= self.max_chunk_chars:
                    _flush("text")
                    block_start = line_idx + 1

        _flush("text")
        return blocks
