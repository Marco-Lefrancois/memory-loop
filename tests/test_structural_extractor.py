# -*- coding: utf-8 -*-
from pathlib import Path
import pytest

from src.engine.fact_search.structural_extractor import StructuralWikilinkExtractor
from src.loop_mem.db import search_lexicon_terms


def test_infer_relation_from_context():
    # Dépendance
    line1 = "Ce composant dépend de [[AUTH-001]] pour la validation du jeton."
    assert StructuralWikilinkExtractor.infer_relation_from_context(line1) == "depends_on"

    # Implémentation
    line2 = "Le service réalise et implémente [[ADR-0320]] pour le contrat déclaratif."
    assert StructuralWikilinkExtractor.infer_relation_from_context(line2) == "implements"

    # Responsabilité
    line3 = "L'équipe Core est responsable de [[MODULE-PAYMENTS]]."
    assert StructuralWikilinkExtractor.infer_relation_from_context(line3) == "responsible_for"

    # Fallback
    line4 = "Consultez également [[GLOSSARY]] pour plus d'informations."
    assert StructuralWikilinkExtractor.infer_relation_from_context(line4) == "references"


def test_extract_from_file_and_frontmatter(tmp_path: Path):
    sample_file = tmp_path / "STORY-101.md"
    content = """---
id: REC-015
jira_key: COUVBOIRE-990
epic_key: EPIC-CORE
status: READY_FOR_DEV
dependencies:
  - REC-012
  - REC-014
tags:
  - backend
  - auth
---

# Titre Métier de la Story

Cette tâche dépend de [[REC-012]] et utilise [[PostgreSQL]].
Elle implémente également [[ADR-0042]].
"""
    sample_file.write_text(content, encoding="utf-8")

    triples, frontmatter = StructuralWikilinkExtractor.extract_from_file(sample_file)

    # Vérification frontmatter
    assert ("STORY-101", "belongs_to_epic", "EPIC-CORE") in triples
    assert ("STORY-101", "has_status", "READY_FOR_DEV") in triples
    assert ("STORY-101", "depends_on", "REC-012") in triples
    assert ("STORY-101", "depends_on", "REC-014") in triples
    assert ("STORY-101", "has_tag", "backend") in triples

    # Vérification wikilinks avec inférence
    assert ("STORY-101", "depends_on", "REC-012") in triples
    assert ("STORY-101", "uses", "PostgreSQL") in triples
    assert ("STORY-101", "implements", "ADR-0042") in triples


def test_sync_project_structural_relations(tmp_path: Path):
    proj_dir = tmp_path / "Projects" / "test_struct_proj"
    stories_dir = proj_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_md = stories_dir / "COUVBOIRE-100.md"
    story_md.write_text("""---
id: STORY-100
jira_key: COUVBOIRE-100
epic_key: EPIC-SYNC
status: DRAFT
---

# Sync Story
Ce module bloque [[COUVBOIRE-101]] jusqu'à validation.
""", encoding="utf-8")

    synced_count = StructuralWikilinkExtractor.sync_project_structural_relations(
        project_name="test_struct_proj",
        project_dir=proj_dir,
    )

    assert synced_count >= 2

    # Recherche dans le lexique projet
    lex_results = search_lexicon_terms("COUVBOIRE-100", project_name="test_struct_proj")
    assert len(lex_results) >= 1
    terms = [r["term"] for r in lex_results]
    assert any("COUVBOIRE-100" in t for t in terms)
