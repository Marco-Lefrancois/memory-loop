import unittest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path

root = Path.cwd()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.engine.fact_search import (
    FactSearchIndexer,
    FactSearchRetriever,
    FactSearchCoverageEvaluator,
    index_project_docs_to_fts5,
    fact_search_query,
    calculate_story_fact_coverage,
)
from src.loop_mem.db import upsert_lexicon_term


class TestFactSearchEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_name = "TestProject_FS"
        self.project_dir = self.test_dir / "Projects" / self.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.test_dir / "memory" / "loop_mem.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Créer les dossiers docs/
        self.docs_dir = self.project_dir / "docs"
        (self.docs_dir / "01-architecture").mkdir(parents=True, exist_ok=True)
        (self.docs_dir / "02-business-rules").mkdir(parents=True, exist_ok=True)
        (self.docs_dir / "03-models").mkdir(parents=True, exist_ok=True)
        (self.docs_dir / "00-ingested").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "memory").mkdir(parents=True, exist_ok=True)

        # 1. Règle métier sous docs/02
        rm_file = self.docs_dir / "02-business-rules" / "RM-042_Cart_Timeout.md"
        rm_file.write_text(
            "# RM-042 : Règle d'Expiration des Paniers d'Achat\n\n"
            "## Contexte & Périmètre\n"
            "Cette règle régit la durée de réservation d'inventaire pour tout panier actif.\n\n"
            "## Spécification de la Durée\n"
            "Tout panier d'achat expire automatiquement après 15 minutes d'inactivité de l'utilisateur.\n"
            "En cas d'expiration, les articles réservés sont remis en stock immédiatement.\n",
            encoding="utf-8"
        )

        # 2. Modèle sous docs/03
        model_file = self.docs_dir / "03-models" / "Cart_Schema.md"
        model_file.write_text(
            "# Modèle de Données : Cart & CartItems\n\n"
            "## Structure de la Table Cart\n"
            "- `cart_id` : UUID unique du panier\n"
            "- `user_id` : UUID utilisateur\n"
            "- `status` : ACTIVE | EXPIRED | CHECKED_OUT\n",
            encoding="utf-8"
        )

        # 3. Document ingéré sous docs/00
        ingested_file = self.docs_dir / "00-ingested" / "Cahier_Des_Charges_Client.md"
        ingested_file.write_text(
            "# Spécifications Fonctionnelles Générales\n\n"
            "## Module Paiement\n"
            "Le système supporte Stripe et Moneris pour les transactions par carte de crédit.\n"
            "Les devises acceptées sont CAD et USD.\n",
            encoding="utf-8"
        )

        # 4. User Story sous backlog/stories
        self.story_file = self.project_dir / "backlog" / "stories" / "US-042.md"
        self.story_file.write_text(
            "---\n"
            "id: US-042\n"
            "title: Expiration Automatique du Panier\n"
            "layer: fullstack\n"
            "status: IN_ANALYZE\n"
            "---\n\n"
            "# Expiration Automatique du Panier\n\n"
            "## Contexte métier\n"
            "Libération de stock selon la règle RM-042.\n\n"
            "## Scénarios de test\n\n"
            "### 1. Nominal\n"
            "- Le panier expire après 15 minutes d'inactivité et libère l'inventaire selon RM-042.\n\n"
            "### 2. Exceptions\n"
            "- Le paiement Stripe échoue en cas de carte refusée.\n\n"
            "### 3. Résilience\n"
            "- L'état du panier est persisté en cas de coupure réseau.\n\n"
            "### 4. UX\n"
            "- Une modale informe l'utilisateur que son panier a expiré.\n",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_index_project_docs_to_fts5(self):
        count = FactSearchIndexer.index_project_docs(
            project_name=self.project_name,
            docs_dir=self.docs_dir,
            db_path=self.db_path,
        )
        self.assertGreater(count, 0, "L'indexation FTS5 doit retourner au moins 1 chunk")

    def test_02_fact_search_query_with_synonyms(self):
        FactSearchIndexer.index_project_docs(
            project_name=self.project_name,
            docs_dir=self.docs_dir,
            db_path=self.db_path,
        )

        results = FactSearchRetriever.search(
            query="cart timeout 15 minutes",
            project_name=self.project_name,
            expand_synonyms=True,
            limit=5,
            db_path=self.db_path,
            log_audit=False,
        )
        self.assertTrue(len(results) > 0, "La recherche avec synonyme étendu doit retourner des résultats")
        
        # Au moins un des résultats doit cibler RM-042 et mentionner 15 minutes
        rm_results = [r for r in results if "RM-042" in r["breadcrumb"]]
        self.assertTrue(len(rm_results) > 0, "Doit trouver un chunk de RM-042")
        self.assertIn("business-rules", rm_results[0]["ssot_layer"])
        self.assertGreater(rm_results[0]["relevance_score"], 0.0)
        has_minutes = any("15 minutes" in r["snippet"] for r in rm_results)
        self.assertTrue(has_minutes, "Le snippet doit contenir '15 minutes'")

    def test_03_calculate_story_fact_coverage(self):
        FactSearchIndexer.index_project_docs(
            project_name=self.project_name,
            docs_dir=self.docs_dir,
            db_path=self.db_path,
        )

        coverage_report = FactSearchCoverageEvaluator.evaluate_story_coverage(
            story_path=self.story_file,
            project_name=self.project_name,
            db_path=self.db_path,
        )
        self.assertEqual(coverage_report["total_criteria"], 4, "Doit extraire exactement 4 critères de test")
        self.assertGreaterEqual(coverage_report["covered_criteria"], 2, "Doit couvrir au moins 2 critères")
        self.assertGreaterEqual(coverage_report["coverage_ratio"], 0.5)


if __name__ == "__main__":
    unittest.main()
