# -*- coding: utf-8 -*-
"""
Tests unitaires pour le pipeline AgenticDocExtractor (ADR-0323).
"""

import unittest
from src.pipelines.agentic_doc_extractor import AgenticDocExtractor, AgenticExtractionReport


class TestAgenticDocExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = AgenticDocExtractor()

    def test_multi_pass_extraction(self):
        sample_md = """# Spécification API Synchrone

## Exigences Métier

- Le système doit répondre en moins de 200ms.
- Les requêtes doivent obligatoirement inclure un jeton Bearer.
- Interdiction stricte de stocker les fichiers bruts sur le disque temporaire.

## Schéma des Données

| Champ | Type | Obligatoire |
| :--- | :--- | :--- |
| user_id | string | Oui |
| max_budget | float | Non |
"""
        report = self.extractor.process_text(sample_md, document_name="test_spec")
        
        self.assertIsInstance(report, AgenticExtractionReport)
        self.assertTrue(report.total_chunks >= 1)
        self.assertTrue(report.total_facts_extracted >= 3)
        
        # Vérifier que les règles sont détectées
        rules = [f for f in report.facts if f.category == "rule"]
        self.assertTrue(len(rules) >= 1)
        self.assertTrue(any("200ms" in r.statement for r in rules))
        self.assertTrue(any("Bearer" in r.statement for r in rules))


if __name__ == "__main__":
    unittest.main()
