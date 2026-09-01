# -*- coding: utf-8 -*-
import unittest
import tempfile
import yaml
from pathlib import Path
from src.core.rule_engine import RuleEngine, ValidationRule

class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.adr_dir = Path(self.tmp_dir.name)
        self.engine = RuleEngine()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_load_rules_from_adr_dir(self):
        adr_content = """---
id: ADR-TEST
title: Test Rule
validation_rules:
  - check_id: test_check
    severity: BLOCKING
    params:
      threshold: 5
---
# ADR-TEST
"""
        (self.adr_dir / "ADR-TEST.md").write_text(adr_content, encoding="utf-8")
        
        count = self.engine.load_from_adr_dir(self.adr_dir)
        self.assertEqual(count, 1)
        self.assertIn("test_check", self.engine._rules)
        rule = self.engine._rules["test_check"]
        self.assertEqual(rule.severity, "BLOCKING")
        self.assertEqual(rule.params["threshold"], 5)

    def test_validate_rule(self):
        self.engine._rules["min_len"] = ValidationRule(
            check_id='min_len',
            severity='WARNING',
            adr_id='ADR-TEST',
            params={'min': 15}
        )

        violations = self.engine.validate("min_len", "trop court")
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].check_id, "min_len")
