# -*- coding: utf-8 -*-
"""
Tests unitaires pour AutoEvalHarvester (ADR-0326).
"""

import unittest
import tempfile
from pathlib import Path
from src.pipelines.eval_harvester import AutoEvalHarvester, EvalTestCase


class TestAutoEvalHarvester(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.harvester = AutoEvalHarvester(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_harvest_from_markdown(self):
        sample_report = """# Rapport d'Audit WikiFix

### Fichier : `Projects/mLoop/backlog/stories/US-01.md`
- [REJET] Le récit ne contient pas les 4 piliers Gherkin obligatoires.
- [AVERTISSEMENT] Critère INVEST 'Small' incertain (trop de scénarios).

### Fichier : `Projects/mLoop/backlog/stories/US-02.md`
- [GUARDRAIL TECH] Présence de code C# MauiProgram.cs dans le récit.
"""
        evals = self.harvester.harvest_from_markdown(sample_report, source="test")

        self.assertEqual(len(evals), 3)
        self.assertEqual(evals[0].severity, "BLOCKING")
        self.assertEqual(evals[0].category, "gherkin_4_pillars")
        self.assertEqual(evals[0].target_file, "Projects/mLoop/backlog/stories/US-01.md")
        
        self.assertEqual(evals[1].severity, "WARNING")
        self.assertEqual(evals[1].category, "invest_criteria")

        self.assertEqual(evals[2].severity, "BLOCKING")
        self.assertEqual(evals[2].category, "technical_leak")

    def test_save_eval_pack(self):
        evals = [
            EvalTestCase(
                eval_id="EVAL-001",
                target_file="US-01.md",
                category="gherkin_4_pillars",
                issue_description="Scénario incomplet",
                expected_rule="4 Piliers Gherkin",
                severity="BLOCKING",
                discovered_at="2026-08-18",
            )
        ]
        out_file = self.harvester.save_eval_pack(evals, filename="test_evals.json")
        self.assertTrue(out_file.exists())
        self.assertIn("EVAL-001", out_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
