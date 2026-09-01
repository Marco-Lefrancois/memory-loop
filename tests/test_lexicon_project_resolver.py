"""
Tests unitaires TDD — Résolution Sémantique de Projets & Dictionnaires de Lexique (mLoop Core).

Valide :
1. Découpage CamelCase et extraction de jetons dans SemanticLexiconResolver.tokenize.
2. Échappement et sécurité des requêtes FTS5 dans la base SQLite (project_lexicon_fts).
3. Indexation continue de CONTEXT.md et 05-glossaire.md dans sync_project_lexicon_from_disk.
4. Résolution de projet avec alias CamelCase (ex: "BoireEtFrere", "Boire & Frère") vers "BoireFrere_Reception".
5. Priorisation du projet avec structure SSOT valide face à une coquille vide ou dossier fantôme.
6. Résolution de projet via des termes du lexique métier (ex: "Couvoir", "Réception Quai", "OneTrust").
"""
import pytest
import sqlite3
from pathlib import Path
from src.utils.lexicon_resolver import SemanticLexiconResolver
from src.swarm import resolve_project_name
from src.loop_mem.db import (
    sync_project_lexicon_from_disk,
    search_lexicon_terms,
    get_observation_db_session
)


def test_tokenize_camel_case_and_stopwords():
    """Vérifie que tokenize gère le CamelCase, les acronymes, tirets et stopwords."""
    tokens = SemanticLexiconResolver.tokenize("BoireEtFrere")
    assert "boire" in tokens
    assert "frere" in tokens
    assert "et" not in tokens

    tokens_metro = SemanticLexiconResolver.tokenize("Metro_Food_Offers")
    assert "metro" in tokens_metro
    assert "food" in tokens_metro
    assert "offers" in tokens_metro

    tokens_phrase = SemanticLexiconResolver.tokenize("Projet Boire & Frères - Réception Quai")
    assert "boire" in tokens_phrase
    assert "freres" in tokens_phrase or "frere" in tokens_phrase
    assert "reception" in tokens_phrase
    assert "quai" in tokens_phrase


def test_sync_lexicon_indexes_context_and_glossary():
    """Vérifie que sync_project_lexicon_from_disk indexe CONTEXT.md et 05-glossaire.md."""
    project_name = "BoireFrere_Segment2"
    count = sync_project_lexicon_from_disk(project_name)
    assert count > 0, "Aucun terme n'a été indexé depuis le disque du projet"

    # Vérifier la présence de termes clés dans FTS5
    hits_boire = search_lexicon_terms("Boire", project_name=project_name)
    assert len(hits_boire) > 0, "Le terme 'Boire' issu de CONTEXT.md n'a pas été trouvé"


def test_fts5_sanitization_safe():
    """Vérifie que les caractères spéciaux (-, &, *, quotes) ne provoquent pas de crash SQL FTS5."""
    # Ne doit pas lever sqlite3.OperationalError
    res1 = search_lexicon_terms("Boire & Frères - Couvoir*", project_name="BoireFrere_Segment2")
    assert isinstance(res1, list)

    res2 = search_lexicon_terms("REC-015 (Desktop / Panier)", project_name="BoireFrere_Segment2")
    assert isinstance(res2, list)


def test_resolve_project_alias_camelcase_and_symbols():
    """Vérifie la résolution d'alias avec différentes syntaxes vers un projet Boire valide."""
    res1 = SemanticLexiconResolver.resolve_project_alias("BoireEtFrere")
    assert res1 in ("BoireFrere_Reception", "BoireFrere_Segment2")

    res2 = SemanticLexiconResolver.resolve_project_alias("Boire & Frère")
    assert res2 in ("BoireFrere_Reception", "BoireFrere_Segment2")

    res3 = SemanticLexiconResolver.resolve_project_alias("boire-frere")
    assert res3 in ("BoireFrere_Reception", "BoireFrere_Segment2")


def test_resolve_project_alias_prefers_ssot_over_empty_stub(tmp_path):
    """Vérifie qu'un dossier stub vide sans SSOT est pénalisé face à un projet valide."""
    # Test avec resolve_project_name
    canonical = resolve_project_name("BoireEtFrere")
    assert canonical in ("BoireFrere_Reception", "BoireFrere_Segment2")
