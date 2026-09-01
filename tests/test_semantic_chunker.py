# -*- coding: utf-8 -*-
"""
Tests unitaires pour le moteur MarkdownSemanticChunker (ADR-0323).
"""

import unittest
from src.utils.semantic_chunker import MarkdownSemanticChunker, SemanticChunk


class TestMarkdownSemanticChunker(unittest.TestCase):

    def setUp(self):
        self.chunker = MarkdownSemanticChunker(max_chunk_chars=500, min_chunk_chars=50)

    def test_table_atomicity(self):
        """Vérifie qu'un tableau Markdown n'est jamais scindé en morceaux."""
        sample_md = """# Document Test

Voici une introduction.

| Col 1 | Col 2 | Col 3 |
| :--- | :--- | :--- |
| Valeur A | Valeur B | Valeur C |
| Valeur D | Valeur E | Valeur F |
| Valeur G | Valeur H | Valeur I |

Voici un paragraphe de conclusion.
"""
        chunks = self.chunker.chunk_text(sample_md, source_name="test_doc")
        
        # Trouver le chunk contenant le tableau
        table_chunks = [c for c in chunks if c.chunk_type == "table" or "| Col 1 |" in c.content]
        self.assertTrue(len(table_chunks) >= 1)
        
        # Le tableau complet doit être intact dans un seul chunk
        table_text = table_chunks[0].content
        self.assertIn("| Col 1 | Col 2 | Col 3 |", table_text)
        self.assertIn("| Valeur G | Valeur H | Valeur I |", table_text)

    def test_header_breadcrumb_tracking(self):
        """Vérifie que la hiérarchie des en-têtes (H1 > H2 > H3) est fidèlement préservée."""
        sample_md = """# Architecture Système

## Module Ingestion

### Composant Semantic Chunker

Le semantic chunker découpe les documents selon la structure.

### Composant Agentic Extractor

L'agentic extractor raisonne en mode multi-passes.
"""
        chunks = self.chunker.chunk_text(sample_md, source_name="doc_archi")
        
        self.assertTrue(len(chunks) >= 1)
        # Vérifier que le header_path reflète l'arbre
        paths = [c.header_path for c in chunks]
        has_full_hierarchy = any("Architecture Système > Module Ingestion > Composant" in p for p in paths)
        self.assertTrue(has_full_hierarchy, f"Chemins générés: {paths}")

    def test_admonition_preservation(self):
        """Vérifie que les blocs admonition GitHub ([!NOTE]) restent groupés."""
        sample_md = """## Règles de Sécurité

> [!WARNING]
> Ceci est une alerte critique de sécurité.
> Ne jamais commiter de clés API privées.

Texte régulier après l'alerte.
"""
        chunks = self.chunker.chunk_text(sample_md, source_name="sec_doc")
        admon_chunks = [c for c in chunks if "[!WARNING]" in c.content]
        self.assertEqual(len(admon_chunks), 1)
        self.assertIn("Ne jamais commiter de clés API privées.", admon_chunks[0].content)

    def test_code_block_preservation(self):
        """Vérifie que les blocs de code ``` restent atomiques."""
        sample_md = """## Code Exemple

```python
def calculate_budget(spend: float, max_budget: float) -> float:
    return max_budget - spend
```

Fin de section.
"""
        chunks = self.chunker.chunk_text(sample_md, source_name="code_doc")
        code_chunks = [c for c in chunks if "def calculate_budget" in c.content]
        self.assertEqual(len(code_chunks), 1)
        self.assertIn("```python", code_chunks[0].content)
        self.assertIn("return max_budget - spend", code_chunks[0].content)


if __name__ == "__main__":
    unittest.main()
