"""
Convertisseur Multimodal MarkPDFdown — Ingestion Visuelle Haute-Fidélité.

Inspiré de MarkPDFdown (LiteLLM / Vision Models) :
- Convertit les PDFs d'architecture, diagrammes, wireframes et schémas en Markdown structuré.
- Conserve les tableaux complexes, arbres de décisions et formules.
- Fallback automatique transparent vers Microsoft MarkItDown / PyPDF si le mode vision est indisponible.
"""
from __future__ import annotations

import os
import io
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


SUPPORTED_VISION_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".svg"}


class MarkPDFdownConverter:
    """Moteur d'ingestion visuelle haute fidélité pour documents de référence complexes."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("MLOOP_VISION_MODEL", "gemini-3.8-flash")
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    def is_supported(self, file_path: Path | str) -> bool:
        """Vérifie si l'extension du fichier est prise en charge pour l'ingestion multimodale."""
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_VISION_EXTENSIONS

    def convert_file(self, file_path: Path | str) -> str:
        """
        Convertit un fichier PDF ou image en Markdown structuré.
        Utilise la vision si disponible, avec fallback local résilient.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier cible introuvable pour conversion : {path}")

        ext = path.suffix.lower()

        # Si c'est un PDF et qu'une clé API vision est présente, tenter l'extraction multimodale
        if ext == ".pdf" and self.api_key:
            try:
                return self._convert_pdf_multimodal(path)
            except Exception as e:
                # Fallback sur extraction locale en cas d'indisponibilité de l'API
                print(f"[MarkPDFdown] Note: Fallback local suite à exception vision: {e}")
                return self._convert_pdf_local_fallback(path)

        elif ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            if self.api_key:
                try:
                    return self._convert_image_multimodal(path)
                except Exception as e:
                    print(f"[MarkPDFdown] Note: Fallback image descriptif: {e}")
                    return f"# Image : {path.name}\n\n*Image binaire non analysable sans vision API active.*"
            return f"# Image : {path.name}\n\n*Image binaire ingérée sous référence.*"

        # Fallback local général
        return self._convert_pdf_local_fallback(path)

    def _convert_pdf_multimodal(self, path: Path) -> str:
        """Conversion PDF multimodale via LiteLLM ou client vision."""
        try:
            import litellm
            # Envoi du PDF pour transcription visuelle structurée
            response = litellm.completion(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Convertis ce document en Markdown ultra-propre et fidèle. "
                                    "Conserve tous les tableaux, diagrammes, légendes, flux et listes. "
                                    "Utilise des blocs mermaid pour les schémas d'architecture et de flux si possible."
                                ),
                            },
                            {
                                "type": "file",
                                "file_path": str(path.resolve()),
                            },
                        ],
                    }
                ],
            )
            content = response.choices[0].message.content
            # Journalisation dans TokenLedger
            try:
                from src.utils.token_ledger import TokenLedger
                usage = getattr(response, "usage", None)
                p_tok = getattr(usage, "prompt_tokens", 2000) if usage else 2000
                c_tok = getattr(usage, "completion_tokens", len(content) // 4) if usage else len(content) // 4
                TokenLedger.record_interaction(
                    action="markpdfdown_pdf",
                    target=path.name,
                    model=self.model_name,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    context_files=[str(path)],
                )
            except Exception:
                pass
            return content
        except Exception:
            # Si litellm n'est pas installé ou échoue, fallback local
            return self._convert_pdf_local_fallback(path)

    def _convert_image_multimodal(self, path: Path) -> str:
        """Conversion d'une image de diagramme/schéma en Markdown/Mermaid via vision."""
        try:
            import litellm
            response = litellm.completion(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Décris et transcris ce schéma/diagramme d'architecture en Markdown structuré. "
                                    "Génère un bloc Mermaid correspondant exactement aux relations et composants observés."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/{path.suffix[1:]};base64,{self._encode_image(path)}"},
                            },
                        ],
                    }
                ],
            )
            content = response.choices[0].message.content
            # Journalisation dans TokenLedger
            try:
                from src.utils.token_ledger import TokenLedger
                usage = getattr(response, "usage", None)
                p_tok = getattr(usage, "prompt_tokens", 1500) if usage else 1500
                c_tok = getattr(usage, "completion_tokens", len(content) // 4) if usage else len(content) // 4
                TokenLedger.record_interaction(
                    action="markpdfdown_image",
                    target=path.name,
                    model=self.model_name,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    context_files=[str(path)],
                )
            except Exception:
                pass
            return content
        except Exception:
            return f"# Diagramme : {path.stem}\n\n*Image {path.name} présente sous reference/.*"

    def _convert_pdf_local_fallback(self, path: Path) -> str:
        """Fallback local déterministe via pypdf ou markitdown."""
        # 1. Tentative avec markitdown si présent
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            res = md.convert(str(path))
            if res and res.text_content:
                return res.text_content
        except Exception:
            pass

        # 2. Tentative avec pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(f"## Page {i + 1}\n\n{text.strip()}")
            if pages_text:
                return f"# Document : {path.stem}\n\n" + "\n\n---\n\n".join(pages_text)
        except Exception:
            pass

        # 3. Fallback texte brut
        return f"# {path.stem}\n\n*Document ingéré depuis {path.name}. Contenu binaire indexé sous reference/.*"

    @staticmethod
    def _encode_image(image_path: Path) -> str:
        import base64
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")


def convert_document(file_path: Path | str) -> str:
    """Fonction utilitaire principale d'ingestion documentaire mLoop."""
    converter = MarkPDFdownConverter()
    return converter.convert_file(file_path)


def convert_and_split_chapters(
    file_path: Path | str,
    output_dir: Path | str,
    min_chars_per_chapter: int = 1500
) -> List[Path]:
    """Convertit un document volumineux et le découpe en chapitres avec sidecars LOD (ADR-0335)."""
    from src.core.lod_generator import LODGenerator

    path = Path(file_path)
    out_d = Path(output_dir)
    out_d.mkdir(parents=True, exist_ok=True)

    raw_md = convert_document(path)
    temp_full = out_d / f"_full_{path.stem}.md"
    temp_full.write_text(raw_md, encoding="utf-8")

    created = LODGenerator.split_markdown_chapters(temp_full, out_d, min_chars_per_chapter=min_chars_per_chapter)
    if temp_full.exists():
        temp_full.unlink()

    return created

