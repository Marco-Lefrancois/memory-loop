"""Découpe Markdown en chapitres LOD (MLOOP-145-BE — extraction ADR-0202 depuis lod_generator)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple


def split_markdown_chapters(
    file_path: Path,
    output_dir: Path,
    min_chars_per_chapter: int = 1200,
) -> List[Path]:
    """
    Découpe un document Markdown massif par chapitres (# ou ##) sous output_dir.
    La génération des sidecars LOD est déléguée à l'appelant (LODGenerator).
    """
    if not file_path.exists() or not file_path.is_file():
        return []

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    chapters: List[Tuple[str, List[str]]] = []
    current_title = "00_Introduction"
    current_lines: List[str] = []

    for line in lines:
        # Détection d'un titre de chapitre de niveau 1 ou 2
        if re.match(r"^#{1,2}\s+[A-Za-z0-9]", line.strip()):
            if current_lines and len("\n".join(current_lines)) >= min_chars_per_chapter:
                chapters.append((current_title, current_lines))
                current_title = line.strip().lstrip("#").strip()
                current_lines = [line]
            else:
                if not current_lines:
                    current_title = line.strip().lstrip("#").strip()
                current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines:
        chapters.append((current_title, current_lines))

    output_dir.mkdir(parents=True, exist_ok=True)
    created_files: List[Path] = []

    for idx, (title, ch_lines) in enumerate(chapters, start=1):
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", title).strip("_").lower()
        if not clean_name:
            clean_name = f"section_{idx}"
        file_name = f"{idx:02d}_{clean_name}.md"
        out_file = output_dir / file_name
        out_file.write_text("\n".join(ch_lines) + "\n", encoding="utf-8")
        created_files.append(out_file)

    return created_files
