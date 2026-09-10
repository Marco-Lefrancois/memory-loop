# -*- coding: utf-8 -*-
"""
Tests for Bonified Fact-Search & Completion Coverage Gate (ADR-0326 / ADR-0352).
"""
import unittest
import tempfile
import shutil
import argparse
from pathlib import Path

from src.engine.fact_search.retriever import FactSearchRetriever
from src.engine.fact_search.indexer import FactSearchIndexer
from src.pipelines.completion_gate import CompletionGate, GateStatus
from src.commands.handlers.fact_search import handle_fact_search


class TestFactSearchBonified(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_name = "Bonified_Project"
        self.project_dir = self.test_dir / "Projects" / self.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.test_dir / "memory" / "loop_mem.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.docs_dir = self.project_dir / "docs"
        (self.docs_dir / "01-architecture").mkdir(parents=True, exist_ok=True)
        (self.docs_dir / "02-business-rules").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)

        # 1. Document d'architecture avec titre explicite
        arch_file = self.docs_dir / "01-architecture" / "ADR-0352_Checkpointing.md"
        arch_file.write_text(
            "# ADR-0352 : Architecture de Checkpointing In-Flight\n\n"
            "## 1. Contexte\n"
            "Les agents autonomes perdent leur état en cas de défaillance.\n\n"
            "## 2. Décision Checkpointing\n"
            "Le système mLoop déclenche un checkpointing in-flight automatique "
            "toutes les 60 à 90 secondes avec rétention FIFO des trois derniers états.\n",
            encoding="utf-8"
        )

        # 2. Document business-rules
        rule_file = self.docs_dir / "02-business-rules" / "RM-101_Gate_Validation.md"
        rule_file.write_text(
            "# RM-101 : Règle de Non-Dégénérescence\n\n"
            "## Critère d'audit\n"
            "Toute anomalie de couverture factuelle inférieure à cinquante pour cent "
            "doit générer un statut DEGENERATE_CANDIDATE exigeant confirmation HITL.\n",
            encoding="utf-8"
        )

        # Indexation dans la DB de test
        FactSearchIndexer.index_project_docs(
            project_name=self.project_name,
            docs_dir=self.docs_dir,
            db_path=self.db_path,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_anti_slop_filter(self):
        """Vérifie le filtre anti-slop sur les extraits vides et denses."""
        # Extraits vides ou sans densité
        self.assertFalse(FactSearchRetriever.is_substantive_snippet(""))
        self.assertFalse(FactSearchRetriever.is_substantive_snippet("## Table des matières\n- Section 1\n- Section 2"))
        self.assertFalse(FactSearchRetriever.is_substantive_snippet("### Introduction\n..."))
        self.assertFalse(FactSearchRetriever.is_substantive_snippet("court texte"))

        # Extrait narratif substantif
        dense_text = (
            "Le système mLoop déclenche un checkpointing in-flight automatique "
            "toutes les 60 à 90 secondes avec rétention FIFO des savepoints."
        )
        self.assertTrue(FactSearchRetriever.is_substantive_snippet(dense_text))

    def test_02_title_boost_and_layer_filtering(self):
        """Vérifie que la correspondance de titre booste le score et que le filtre de couche opère."""
        results = FactSearchRetriever.search(
            query="checkpointing",
            project_name=self.project_name,
            limit=5,
            db_path=self.db_path,
            log_audit=False,
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("01-architecture", top["ssot_layer"])
        self.assertTrue(top["is_substantive"])
        self.assertGreater(top["relevance_score"], 0.0)

        # Filtrage par couche 02-business-rules : checkpointing ne doit pas apparaître sous 02
        results_layer_02 = FactSearchRetriever.search(
            query="checkpointing",
            project_name=self.project_name,
            limit=5,
            db_path=self.db_path,
            log_audit=False,
            layer="02-business-rules",
        )
        self.assertEqual(len(results_layer_02), 0)

    def test_03_completion_gate_story_coverage_fail(self):
        """Vérifie que la gate émet DEGENERATE_CANDIDATE quand la couverture est basse."""
        uncited_story = self.project_dir / "backlog" / "stories" / "US-UNCITED.md"
        uncited_story.write_text(
            "# US-UNCITED : Story sans fondement SSOT\n\n"
            "## Scénarios de test\n"
            "- Intégrer un système de paiement par cryptomonnaie Solana non documenté.\n"
            "- Permettre le minage de bitcoins en arrière-plan pendant l'exécution.\n"
            "- Émettre des tokens NFT à chaque commit Git non validé.\n"
            "- Envoyer des notifications par télégraphe optique sous-marin.\n",
            encoding="utf-8"
        )

        result = CompletionGate.validate_story_coverage(
            story_path=uncited_story,
            project_name=self.project_name,
            db_path=self.db_path,
            min_coverage_ratio=0.5,
        )

        self.assertEqual(result.status, GateStatus.DEGENERATE_CANDIDATE)
        self.assertTrue(result.is_degenerate)
        self.assertTrue(result.requires_hitl)
        self.assertGreater(len(result.reasons), 0)

    def test_04_completion_gate_story_coverage_pass(self):
        """Vérifie que la gate émet PASS quand la couverture est documentée."""
        valid_story = self.project_dir / "backlog" / "stories" / "US-VALID.md"
        valid_story.write_text(
            "# US-VALID : Checkpointing conforme\n\n"
            "## Scénarios de test\n"
            "- Le checkpointing in-flight est déclenché selon ADR-0352 toutes les 60 secondes.\n"
            "- La validation de couverture applique la règle RM-101 avec confirmation HITL.\n",
            encoding="utf-8"
        )

        result = CompletionGate.validate_story_coverage(
            story_path=valid_story,
            project_name=self.project_name,
            db_path=self.db_path,
            min_coverage_ratio=0.5,
        )

        self.assertEqual(result.status, GateStatus.PASS)
        self.assertFalse(result.is_degenerate)
        self.assertFalse(result.requires_hitl)

    def test_05_cli_handler_fact_search(self):
        """Vérifie le fonctionnement du handler CLI fact-search."""
        # Requête vide -> échec code 1
        args_bad = argparse.Namespace(query="", project=self.project_name, limit=5, layer=None, no_synonyms=False)
        self.assertEqual(handle_fact_search(args_bad), 1)

        # Requête valide -> succès code 0
        args_good = argparse.Namespace(
            query="checkpointing in-flight",
            project=self.project_name,
            limit=5,
            layer="01-architecture",
            no_synonyms=False
        )
        self.assertEqual(handle_fact_search(args_good), 0)


if __name__ == "__main__":
    unittest.main()
