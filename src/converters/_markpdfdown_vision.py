"""Méthodes vision multimodale MarkPDFdown (MLOOP-145-BE — extraction ADR-0202).

Mixin consommé par MarkPDFdownConverter — accède à self.model_name / self.api_key
et aux méthodes de fallback via héritage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class VisionMixin:
    """Conversions multimodales PDF/Image via LiteLLM (vision models)."""

    model_name: str
    api_key: str | None

    # Fournis par MarkPDFdownConverter (classe concrète)
    _convert_pdf_local_fallback: Any
    _encode_image: Any

    def _convert_pdf_multimodal(self, path: Path) -> str:
        """Conversion PDF multimodale via LiteLLM ou client vision."""
        from src.utils.logger import get_logger

        logger = get_logger("converters.markpdfdown")
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
                c_tok = (
                    getattr(usage, "completion_tokens", len(content) // 4)
                    if usage
                    else len(content) // 4
                )
                TokenLedger.record_interaction(
                    action="markpdfdown_pdf",
                    target=path.name,
                    model=self.model_name,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    context_files=[str(path)],
                )
            except Exception as e:
                logger.debug(
                    "Enregistrement TokenLedger (PDF multimodal) échoué (comptabilité partielle)",
                    exc_info=True,
                    extra={
                        "component": "converters.markpdfdown",
                        "operation": "_convert_pdf_multimodal",
                        "target": path.name,
                        "error": str(e),
                    },
                )
            return content
        except Exception as e:
            # Si litellm n'est pas installé ou échoue, fallback local
            logger.warning(
                "Conversion PDF multimodale (litellm) indisponible, repli sur extraction locale",
                exc_info=True,
                extra={
                    "component": "converters.markpdfdown",
                    "operation": "_convert_pdf_multimodal",
                    "input_path": str(path),
                    "error": str(e),
                },
            )
            return self._convert_pdf_local_fallback(path)

    def _convert_image_multimodal(self, path: Path) -> str:
        """Conversion d'une image de diagramme/schéma en Markdown/Mermaid via vision."""
        from src.utils.logger import get_logger

        logger = get_logger("converters.markpdfdown")
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
                                "image_url": {
                                    "url": f"data:image/{path.suffix[1:]};base64,{self._encode_image(path)}"
                                },
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
                c_tok = (
                    getattr(usage, "completion_tokens", len(content) // 4)
                    if usage
                    else len(content) // 4
                )
                TokenLedger.record_interaction(
                    action="markpdfdown_image",
                    target=path.name,
                    model=self.model_name,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    context_files=[str(path)],
                )
            except Exception as e:
                logger.debug(
                    "Enregistrement TokenLedger (image multimodale) échoué (comptabilité partielle)",
                    exc_info=True,
                    extra={
                        "component": "converters.markpdfdown",
                        "operation": "_convert_image_multimodal",
                        "target": path.name,
                        "error": str(e),
                    },
                )
            return content
        except Exception as e:
            logger.warning(
                "Conversion image multimodale (litellm) indisponible, repli sur référence descriptive",
                exc_info=True,
                extra={
                    "component": "converters.markpdfdown",
                    "operation": "_convert_image_multimodal",
                    "input_path": str(path),
                    "error": str(e),
                },
            )
            return f"# Diagramme : {path.stem}\n\n*Image {path.name} présente sous reference/.*"
