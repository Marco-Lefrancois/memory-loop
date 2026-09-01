# -*- coding: utf-8 -*-
"""
Tests unitaires pour ContextMonitor (ADR-0326).
"""

import unittest
from src.utils.context_monitor import ContextMonitor, ContextHealthReport


class TestContextMonitor(unittest.TestCase):

    def setUp(self):
        # Utiliser une petite fenêtre pour tester les seuils
        self.monitor = ContextMonitor(max_context_tokens=1000)

    def test_smart_zone(self):
        small_text = "a" * 800  # ~200 tokens (20%)
        report = self.monitor.evaluate_text(small_text)
        self.assertEqual(report.zone, "SMART_ZONE")
        self.assertTrue(report.occupancy_pct < 40.0)

    def test_caution_zone(self):
        medium_text = "a" * 2000  # ~500 tokens (50%)
        report = self.monitor.evaluate_text(medium_text)
        self.assertEqual(report.zone, "CAUTION_ZONE")
        self.assertTrue(40.0 <= report.occupancy_pct <= 60.0)

    def test_dumb_zone_alert(self):
        large_text = "a" * 3200  # ~800 tokens (80%)
        report = self.monitor.evaluate_text(large_text)
        self.assertEqual(report.zone, "DUMB_ZONE")
        self.assertTrue(report.occupancy_pct > 60.0)
        self.assertIn("ALERTE DÉROCHAGE", report.recommendation)

    def test_render_ascii_gauge(self):
        report = self.monitor.evaluate_text("a" * 1000)
        gauge = self.monitor.render_ascii_gauge(report)
        self.assertIn("Context Meter:", gauge)
        self.assertIn("Zone:", gauge)


if __name__ == "__main__":
    unittest.main()
