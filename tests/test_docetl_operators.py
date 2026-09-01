"""
Tests unitaires pour la suite d'opérateurs DocETL (Split, Gather, Gleaning, Resolve).
"""

from unittest.mock import AsyncMock, patch
import pytest
from src.pipelines.operators.split_gather import split_document, gather_context
from src.pipelines.operators.entity_resolver import EntityResolver
from src.pipelines.operators.gleaning import GleaningEngine
from src.core.llm_client import AsyncLLMClient


def test_split_and_gather_operators():
    sample_text = """Paragraph 1: Introduction to architecture rules.

Paragraph 2: Data models and entity relations.

Paragraph 3: Business logic constraints and validations.

Paragraph 4: Conclusion and deployment notes."""

    # 1. Test Split
    chunks = split_document(sample_text, chunk_size=20, method="token_count", doc_id="DOC-001")
    assert len(chunks) >= 2
    assert chunks[0]["doc_id"] == "DOC-001"
    assert chunks[0]["chunk_num"] == 1
    assert chunks[0]["total_chunks"] == len(chunks)

    # 2. Test Gather
    summaries = ["Résumé chunk 1", "Résumé chunk 1-2"]
    gathered = gather_context(
        chunks,
        prev_count=1,
        summaries=summaries,
        doc_metadata={"title": "Spécification Système", "author": "mLoop Architecture"}
    )

    assert len(gathered) == len(chunks)
    assert "Document Metadata: title: Spécification Système" in gathered[0]["contextualized_text"]
    assert "=== CHUNK CIBLE" in gathered[0]["contextualized_text"]
    
    # Le 2e chunk doit contenir le résumé précédent ou le chunk précédent
    if len(gathered) > 1:
        assert "[Chunk 1 Excerpt]" in gathered[1]["contextualized_text"] or "[Résumé des chunks" in gathered[1]["contextualized_text"]


def test_entity_resolver_blocking():
    resolver = EntityResolver()
    entities = [
        "Officer Smith",
        "J. Smith",
        "Officer J. Smith",
        "Captain Rogers",
        "Steve Rogers",
        "Database Engine",
    ]

    clusters = resolver.find_candidate_clusters(entities, blocking_threshold=0.3)
    
    # Doit regrouper les variantes de Smith ensemble
    smith_cluster = next((c for c in clusters if "Officer Smith" in c), None)
    assert smith_cluster is not None
    assert "J. Smith" in smith_cluster or "Officer J. Smith" in smith_cluster


@pytest.mark.asyncio
async def test_entity_resolver_resolution():
    mock_client = AsyncLLMClient(enable_cache=False)
    
    mock_response = {
        "text": '{"canonical_name": "Officier John Smith", "aliases": ["J. Smith", "Officer Smith"]}',
        "json": {"canonical_name": "Officier John Smith", "aliases": ["J. Smith", "Officer Smith"]},
        "cached": False,
    }

    with patch.object(mock_client, "batch_complete", new=AsyncMock(return_value=[mock_response])):
        resolver = EntityResolver(client=mock_client)
        entities = ["Officer Smith", "J. Smith"]
        res_map = await resolver.resolve(entities)

        assert res_map["Officer Smith"] == "Officier John Smith"
        assert res_map["J. Smith"] == "Officier John Smith"


@pytest.mark.asyncio
async def test_gleaning_engine_workflow():
    mock_client = AsyncLLMClient(enable_cache=False)
    gleaning = GleaningEngine(client=mock_client)

    # Scénario : Passe 1 incomplète -> Validation échoue avec critique -> Passe 2 de raffinement réussit
    step_responses = [
        # 1. Map_init
        {"text": "Extrait partiel sans date", "json": None, "cached": False},
        # 2. Validator (Pass 1)
        {
            "text": '{"is_satisfactory": false, "critique": "Manque la date d\'effet", "missing_elements": ["Date"]}',
            "json": {"is_satisfactory": False, "critique": "Manque la date d'effet", "missing_elements": ["Date"]},
            "cached": False,
        },
        # 3. Refiner (Pass 1)
        {"text": "Extrait complet avec Date : 2026-08-30", "json": None, "cached": False},
        # 4. Validator (Pass 2)
        {
            "text": '{"is_satisfactory": true, "critique": "Conforme", "missing_elements": []}',
            "json": {"is_satisfactory": True, "critique": "Conforme", "missing_elements": []},
            "cached": False,
        },
    ]

    mock_complete = AsyncMock(side_effect=step_responses)

    with patch.object(mock_client, "complete", new=mock_complete):
        result = await gleaning.execute(
            model="nmedia_cloud/claude-sonnet-4.6",
            system_prompt="Extrais les clauses.",
            user_prompt="Contrat du 2026-08-30.",
            validator_criteria="Exige la date et l'objet.",
            max_iterations=2,
        )

        assert "Date : 2026-08-30" in result["final_text"]
        assert result["refinements_count"] == 1
        assert result["validation_rounds"] == 2
        assert len(result["audit_trail"]) == 4
