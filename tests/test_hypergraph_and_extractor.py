"""
Tests Unitaires TDD : DeclarativeExtractor & HypergraphKnowledgeAbstract (ADR-0342 & ADR-0343)
Inspiré par Hyper-Extract.
"""

import json
from pathlib import Path
import tempfile
import unittest

from src.core.declarative_extractor import DeclarativeExtractor, KnowledgeAbstract
from src.core.hypergraph_engine import HypergraphKnowledgeAbstract, HyperNode, HyperEdge


class TestDeclarativeExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = DeclarativeExtractor()

    def test_list_templates(self):
        templates = self.extractor.list_templates()
        self.assertIn("business_rules", templates)
        self.assertIn("data_models", templates)
        self.assertIn("api_contracts", templates)
        self.assertIn("ui_matrix", templates)

    def test_load_template(self):
        tmpl = self.extractor.load_template("business_rules")
        self.assertEqual(tmpl["extractor_id"], "business_rules")
        self.assertEqual(tmpl["id_prefix"], "BR-")

    def test_extract_business_rules(self):
        sample_text = """
# Spécification Authentification

## Règles de validation
- Règle de mot de passe : Le mot de passe doit obligatoirement comporter au moins 12 caractères et un symbole alors le compte est sécurisé.
- Règle d'inactivité : Si l'utilisateur est inactif pendant plus de 15 minutes alors la session est invalidée.
        """
        tmpl = self.extractor.load_template("business_rules")
        ka = self.extractor.extract_from_text(sample_text, tmpl, source_file="auth_spec.md")
        self.assertGreaterEqual(len(ka.entities), 2)
        self.assertEqual(ka.entities[0].id, "BR-001")
        self.assertEqual(ka.entities[0].entity_type, "BusinessRule")
        self.assertIn("VALIDATION", ka.entities[0].data["category"])

        # Test formatting
        md = self.extractor.format_markdown(ka.entities[0], tmpl)
        self.assertIn("BR-001", md)
        self.assertIn("Condition d'activation", md)

    def test_extract_data_models(self):
        sample_text = """
# Modèle User Profile

| Champ | Type | Obligatoire | Description |
| :--- | :--- | :--- | :--- |
| user_id | UUID | Oui | Identifiant unique |
| email | string | Oui | Adresse courriel |
| is_active | boolean | Non | Statut du compte |
        """
        tmpl = self.extractor.load_template("data_models")
        ka = self.extractor.extract_from_text(sample_text, tmpl, source_file="model_spec.md")
        self.assertEqual(len(ka.entities), 1)
        entity = ka.entities[0]
        self.assertEqual(entity.entity_type, "DataModel")
        self.assertEqual(len(entity.data["attributes"]), 3)

        md = self.extractor.format_markdown(entity, tmpl)
        self.assertIn("user_id", md)
        self.assertIn("UUID", md)

    def test_extract_api_contracts(self):
        sample_text = """
# Endpoints Authentification

POST /api/v1/auth/login
GET /api/v1/users/me
        """
        tmpl = self.extractor.load_template("api_contracts")
        ka = self.extractor.extract_from_text(sample_text, tmpl, source_file="api_spec.md")
        self.assertEqual(len(ka.entities), 2)
        self.assertEqual(ka.entities[0].data["http_method"], "POST")
        self.assertEqual(ka.entities[0].data["route_path"], "/api/v1/auth/login")


class TestHypergraphEngine(unittest.TestCase):
    def setUp(self):
        self.ka = HypergraphKnowledgeAbstract(project_name="TestProject")

    def test_create_hyper_story_unit(self):
        edge = self.ka.create_story_unit(
            story_id="STORY-001",
            title="Connexion Utilisateur",
            persona="Utilisateur Authentifié",
            api_contracts=["POST /api/v1/auth/login"],
            business_rules=["BR-001", "BR-002"],
            data_models=["MDL-001"],
            adrs=["ADR-0001"],
            gherkin_scenarios=["Scénario 1: Authentification réussie"],
            status="READY_FOR_DEV"
        )
        self.assertIsNotNone(edge)
        self.assertEqual(edge.edge_type, "STORY_UNIT")
        self.assertIn("STORY:STORY-001", edge.node_ids)
        self.assertIn("BR:BR-001", edge.node_ids)
        self.assertIn("API:POST /api/v1/auth/login", edge.node_ids)

        # Test query Story Unit
        unit = self.ka.get_hyper_story_unit("STORY-001")
        self.assertIsNotNone(unit)
        self.assertEqual(unit["story_id"], "STORY-001")
        self.assertIn("BusinessRule", unit["nodes_by_type"])
        self.assertEqual(len(unit["nodes_by_type"]["BusinessRule"]), 2)

    def test_find_related_nodes(self):
        self.ka.create_story_unit(
            story_id="STORY-001",
            title="Connexion",
            persona="Client",
            business_rules=["BR-001"],
            adrs=["ADR-0001"]
        )
        related = self.ka.find_related_nodes("BR:BR-001")
        related_ids = [r.node_id for r in related]
        self.assertIn("STORY:STORY-001", related_ids)
        self.assertIn("ADR:ADR-0001", related_ids)
        self.assertIn("PERSONA:client", related_ids)

    def test_incremental_merge(self):
        self.ka.create_story_unit(story_id="STORY-001", title="Initial", business_rules=["BR-001"])
        
        ka_update = HypergraphKnowledgeAbstract(project_name="TestProject")
        ka_update.create_story_unit(story_id="STORY-001", title="Updated", business_rules=["BR-001", "BR-002"])
        ka_update.create_story_unit(story_id="STORY-002", title="New Story")

        report = self.ka.merge_with(ka_update)
        self.assertTrue(report.has_changes)
        self.assertIn("STORY:STORY-002", report.added_nodes)
        self.assertIn("EDGE_STORY_STORY-001", report.updated_edges)

        unit = self.ka.get_hyper_story_unit("STORY-001")
        self.assertEqual(len(unit["nodes_by_type"]["BusinessRule"]), 2)

    def test_serialization_and_obsidian_export(self):
        self.ka.create_story_unit(
            story_id="REC-001",
            title="Réception de Marchandises",
            persona="Opérateur",
            business_rules=["BR-010"],
            adrs=["ADR-0100"]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # JSON serialization
            json_file = tmp_path / "hypergraph.json"
            self.ka.save_to_file(json_file)
            self.assertTrue(json_file.exists())
            
            loaded_ka = HypergraphKnowledgeAbstract.load_from_file(json_file)
            self.assertEqual(len(loaded_ka.nodes), len(self.ka.nodes))
            self.assertEqual(len(loaded_ka.edges), len(self.ka.edges))

            # Obsidian Vault Export
            vault_dir = tmp_path / "obsidian_vault"
            self.ka.export_obsidian_vault(vault_dir)
            self.assertTrue((vault_dir / "Stories" / "EDGE_STORY_REC-001.md").exists())
            self.assertTrue((vault_dir / "Entities" / "BR_BR-010.md").exists())


if __name__ == "__main__":
    unittest.main()
