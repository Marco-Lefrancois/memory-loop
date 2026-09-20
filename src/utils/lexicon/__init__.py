# -*- coding: utf-8 -*-
"""
Package lexicon — Résolveur Lexical Modulaire (ADR-0202 / MLOOP-101-BE).

Façade ré-exportant SemanticLexiconResolver pour transparence totale des imports.
Les 16 sites d'import `from src.utils.lexicon_resolver import SemanticLexiconResolver`
restent inchangés ; ce package ne les concerne pas directement.
"""

from src.utils.lexicon.entity_matcher import EntityMatcher
from src.utils.lexicon.project_resolver import ProjectResolver

__all__ = ["EntityMatcher", "ProjectResolver"]
