# -*- coding: utf-8 -*-
"""
Tests unitaires pour MemorySupersessionEngine (ADR-0326).
"""

import unittest
import tempfile
from pathlib import Path
from src.loop_mem.supersession import MemorySupersessionEngine, SupersessionRecord


class TestMemorySupersessionEngine(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        self.adr_dir = self.base_path / "docs" / "01-architecture"
        self.adr_dir.mkdir(parents=True, exist_ok=True)
        self.engine = MemorySupersessionEngine(self.base_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_scan_and_sync_ledger(self):
        # Créer deux ADRs fictifs avec clause de remplacement
        adr_001 = self.adr_dir / "ADR-001_legacy_crawler.md"
        adr_001.write_text("# ADR-001 : Ancien Crawler\n\nStatut : Obsolète", encoding="utf-8")

        adr_0325 = self.adr_dir / "ADR-0325_semantic_crawler.md"
        adr_0325.write_text("# ADR-0325 : Nouveau Moteur\n\nRemplace : ADR-001\n\nNouveau découpage sémantique.", encoding="utf-8")

        records = self.engine.scan_adrs_for_supersessions(self.adr_dir)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].target_id, "ADR-001")
        self.assertEqual(records[0].superseded_by, "ADR-0325")

        ledger = self.engine.sync_ledger(records)
        self.assertIn("ADR-001", ledger["superseded_items"])

        # Vérifier is_superseded
        res = self.engine.is_superseded("ADR-001")
        self.assertIsNotNone(res)
        self.assertEqual(res.superseded_by, "ADR-0325")

        res_none = self.engine.is_superseded("ADR-0325")
        self.assertIsNone(res_none)


if __name__ == "__main__":
    unittest.main()
