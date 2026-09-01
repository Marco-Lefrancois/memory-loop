# -*- coding: utf-8 -*-
"""
Tests unitaires pour InvestDatasetDistiller (ADR-0328).
"""

import unittest
import tempfile
from pathlib import Path
from src.pipelines.invest_dataset_distiller import InvestDatasetDistiller, DistillationExample


class TestInvestDatasetDistiller(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.distiller = InvestDatasetDistiller(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_generate_distilled_dataset(self):
        """Vérifie la génération des paires d'exemples d'entraînement conformes et contradictoires."""
        examples = self.distiller.generate_distilled_dataset()
        self.assertTrue(len(examples) >= 3)

        categories = [e.category for e in examples]
        self.assertIn("compliant", categories)
        self.assertIn("code_leak", categories)
        self.assertIn("missing_gherkin", categories)

    def test_export_jsonl(self):
        """Vérifie l'exportation au format JSONL ChatML."""
        out_file = self.distiller.export_dataset_jsonl()
        self.assertTrue(out_file.exists())

        lines = out_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("messages", lines[0])
        self.assertIn("Sentinel", lines[0])


if __name__ == "__main__":
    unittest.main()
