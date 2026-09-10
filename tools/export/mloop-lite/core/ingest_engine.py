#!/usr/bin/env python3
"""
mLoop Lite Ingest Engine — Conversion Intelligente Multi-Formats
Prend en charge : Markdown, Textes, Office (Word, Excel, PPTX), PDFs et OCR d'images.
"""
import sys
import os
import shutil
from pathlib import Path

def convert_with_markitdown(src_file: Path, dest_file: Path) -> bool:
    try:
        from markitdown import MarkItDown
        md_engine = MarkItDown()
        result = md_engine.convert(str(src_file))
        if result and result.text_content:
            dest_file.write_text(f"# {src_file.stem}\n\n> **Fichier Source** : {src_file.name}\n\n---\n\n" + result.text_content, encoding="utf-8")
            return True
    except Exception:
        pass
    return False

def convert_with_rapidocr(src_file: Path, dest_file: Path) -> bool:
    try:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR()
        res, _ = engine(str(src_file))
        if res:
            lines = [line[1] for line in res if line[1].strip()]
            content = f"# {src_file.stem} (Transcription OCR)\n\n> **Image Source** : {src_file.name}\n\n---\n\n" + "\n\n".join(lines)
            dest_file.write_text(content, encoding="utf-8")
            return True
    except Exception:
        pass
    return False

def run_ingestion_pipeline(src_dir: Path, dest_dir: Path) -> dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    stats = {"copied": 0, "converted_markitdown": 0, "converted_ocr": 0, "skipped": 0}
    
    if not src_dir.exists():
        return stats
        
    for root, _, files in os.walk(src_dir):
        for file in files:
            src_file = Path(root) / file
            suffix = src_file.suffix.lower()
            rel_name = src_file.relative_to(src_dir).with_suffix(".md")
            dest_file = dest_dir / rel_name
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Si déjà plus récent, on passe
            if dest_file.exists() and os.path.getmtime(dest_file) >= os.path.getmtime(src_file):
                stats["skipped"] += 1
                continue
                
            # Cas 1 : Fichiers textes directs
            if suffix in [".md", ".markdown", ".txt", ".json", ".dbml", ".csv"]:
                shutil.copy2(src_file, dest_file)
                stats["copied"] += 1
                
            # Cas 2 : Formats Office & PDFs complexes
            elif suffix in [".pdf", ".docx", ".xlsx", ".pptx"]:
                success = convert_with_markitdown(src_file, dest_file)
                if success:
                    stats["converted_markitdown"] += 1
                else:
                    # Fallback copie si échec
                    stats["skipped"] += 1
                    
            # Cas 3 : Images et Scans (OCR)
            elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
                success = convert_with_rapidocr(src_file, dest_file)
                if success:
                    stats["converted_ocr"] += 1
                else:
                    stats["skipped"] += 1
                    
    return stats
