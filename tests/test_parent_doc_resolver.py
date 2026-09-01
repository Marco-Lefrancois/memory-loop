# -*- coding: utf-8 -*-
"""
Tests unitaires pour ParentDocumentResolver (ADR-0328).
"""

import unittest
from src.utils.parent_doc_resolver import ParentDocumentResolver, ParentContextBlock


class TestParentDocumentResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = ParentDocumentResolver()
        self.sample_md = """# Architecture Globale

Introduction générale du système.

## Module Gestion des Témoins (OneTrust)

Ce module gère le consentement utilisateur et la bannière légale.

- Règle 1 : La bannière doit s'afficher avant tout dépôt de cookie.
- Règle 2 : Le bouton Accepter tout doit enregistrer le consentement immédiatement.
- Règle 3 : Le verrouillage anti-rebond est actif pendant 500ms sur tous les boutons.

## Module Profil Utilisateur

Gestion des préférences et de l'historique de navigation.
- Règle 4 : Le profil est synchronisé via GraphQL.
"""

    def test_resolve_parent_section(self):
        """Vérifie la remontée de la section parent englobante et des règles soeurs."""
        snippet = "Le verrouillage anti-rebond est actif pendant 500ms"
        block = self.resolver.resolve_from_text(self.sample_md, snippet, document_name="spec_cookies.md")

        self.assertIsNotNone(block)
        self.assertEqual(block.parent_heading, "Module Gestion des Témoins (OneTrust)")
        self.assertEqual(block.section_path, "Architecture Globale > Module Gestion des Témoins (OneTrust)")
        self.assertIn("Ce module gère le consentement utilisateur", block.full_parent_content)
        
        # Vérifier que les règles soeurs sont présentes
        self.assertTrue(len(block.sibling_rules) >= 2)
        self.assertTrue(any("bannière doit s'afficher" in r for r in block.sibling_rules))
        self.assertTrue(any("Accepter tout" in r for r in block.sibling_rules))

    def test_snippet_not_found(self):
        """Vérifie qu'un extrait inexistant retourne None."""
        block = self.resolver.resolve_from_text(self.sample_md, "Texte totalement inexistant")
        self.assertIsNone(block)


if __name__ == "__main__":
    unittest.main()
