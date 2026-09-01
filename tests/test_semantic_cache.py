"""
Tests unitaires pour le cache déterministe SemanticCache.
"""

import tempfile
from pathlib import Path
import pytest
from src.core.semantic_cache import SemanticCache


def test_semantic_cache_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cache.sqlite"
        cache = SemanticCache(db_path)

        model = "nmedia_cloud/claude-sonnet-4.6"
        sys_prompt = "Tu es un assistant utile."
        user_prompt = "Résume ce texte en 3 points."
        response_text = "Point 1, Point 2, Point 3."
        response_json = {"summary": ["Point 1", "Point 2", "Point 3"]}

        key = cache.compute_key(model, sys_prompt, user_prompt, response_schema={"type": "object"})

        # Initialement non trouvé
        assert cache.get(key) is None

        # Enregistrement
        cache.set(
            cache_key=key,
            model=model,
            response_text=response_text,
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            response_json=response_json,
            prompt_tokens=150,
            completion_tokens=45,
        )

        # Récupération (Hit 1)
        res = cache.get(key)
        assert res is not None
        assert res["response_text"] == response_text
        assert res["response_json"] == response_json
        assert res["hit_count"] == 1
        assert res["prompt_tokens"] == 150

        # Deuxième récupération (Hit 2)
        res2 = cache.get(key)
        assert res2["hit_count"] == 2

        # Statistiques
        stats = cache.stats()
        assert stats["total_entries"] == 1
        assert stats["total_hits"] == 2
        assert stats["saved_tokens_est"] == (150 + 45) * 2

        # Invalidation
        cache.clear()
        assert cache.get(key) is None
        assert cache.stats()["total_entries"] == 0


def test_deterministic_key_hash_consistency():
    key1 = SemanticCache.compute_key(
        model="nmedia_cloud/claude-sonnet-4.6",
        system_prompt="System Prompt",
        user_prompt="User Prompt",
        response_schema={"type": "object", "properties": {"a": {"type": "string"}}},
        temperature=0.0,
    )

    # Clé identique malgré l'ordre des clés dans le schéma
    key2 = SemanticCache.compute_key(
        model="nmedia_cloud/claude-sonnet-4.6",
        system_prompt="System Prompt",
        user_prompt="User Prompt",
        response_schema={"properties": {"a": {"type": "string"}}, "type": "object"},
        temperature=0.0,
    )

    assert key1 == key2

    # Clé différente si prompt change
    key3 = SemanticCache.compute_key(
        model="nmedia_cloud/claude-sonnet-4.6",
        system_prompt="System Prompt 2",
        user_prompt="User Prompt",
    )
    assert key1 != key3
