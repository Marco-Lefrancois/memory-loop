# -*- coding: utf-8 -*-
"""
Contextualizer Engine (Anthropic Contextual Retrieval Pattern - ADR-0326).

Génère un préfixe documentaire synthétique et concis (50-100 tokens)
injecté en tête de chaque chunk avant indexation FTS5 / BM25 / Vectorielle.
Permet d'éliminer l'amnésie des chunks isolés lors des recherches plein texte.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, Optional


class DocumentContextualizer:
    """Générateur de signatures contextuelles documentaires (Anthropic Pattern)."""

    LAYER_NAMES = {
        "01-architecture": "Architecture Système & Spécifications",
        "02-business-rules": "Règles Métier & Contrats d'Affaires",
        "03-models": "Modèles de Données & Schémas",
        "00-ingested": "Documents Sources Ingérés",
        "05-assets": "Maquettes & Spécifications Visuelles",
        "06-knowledge": "Bibliothèque du Savoir & ADRs",
    }

    @classmethod
    def generate_context_prefix(
        cls,
        doc_path: str | Path,
        h1_title: str = "",
        h2_title: str = "",
        breadcrumb: str = "",
        summary: str = "",
    ) -> str:
        """
        Produit un préfixe contextuel normalisé pour enrichir un chunk.
        Exemple:
        [CONTEXT: Doc=RM-042_Cart_Timeout.md | Couche=Règles Métier | Section=Expiration Panier]
        """
        path_obj = Path(doc_path)
        filename = path_obj.name
        parent_dir = path_obj.parent.name
        layer_label = cls.LAYER_NAMES.get(parent_dir, parent_dir.replace("-", " ").title())

        # Nettoyage et synthèse des sections
        scope = breadcrumb if breadcrumb else (f"{h1_title} > {h2_title}".strip(" >"))
        if not scope:
            scope = filename

        prefix_parts = [
            f"Doc={filename}",
            f"Couche={layer_label}",
            f"Section={scope}",
        ]
        if summary:
            clean_summary = summary.replace("\n", " ").strip()[:120]
            prefix_parts.append(f"Synthèse={clean_summary}")

        return f"[CONTEXT: {' | '.join(prefix_parts)}]\n"

    @classmethod
    def extract_document_summary(cls, content: str, max_chars: int = 200) -> str:
        """Extrait les premières lignes significatives ou le contexte métier d'un document."""
        lines = content.splitlines()
        summary_lines = []
        for line in lines:
            stripped = line.strip()
            # Ignorer les balises Markdown H1 et frontmatter
            if stripped.startswith(("#", "---", "```", ">")):
                continue
            if len(stripped) > 20:
                summary_lines.append(stripped)
                if sum(len(l) for l in summary_lines) >= max_chars:
                    break
        return " ".join(summary_lines)[:max_chars]
