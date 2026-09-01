"""
Tests unitaires pour AsyncLLMClient.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.core.llm_client import AsyncLLMClient


@pytest.mark.asyncio
async def test_async_llm_client_caching():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_llm_cache.sqlite"
        client = AsyncLLMClient(
            base_url="https://api-ia.nmedia.ca/v1",
            api_key="test-key",
            cache_db_path=db_path,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = '{"analysis": "success"}'
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 20

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        with patch.object(
            client._openai_client.chat.completions,
            "create",
            new=AsyncMock(return_value=mock_response),
        ) as mock_create:
            # 1. Premier appel : Réseau (Mock)
            res1 = await client.complete(
                model="nmedia_cloud/claude-sonnet-4.6",
                system_prompt="System Prompt",
                user_prompt="User Prompt",
                response_schema={"type": "object"},
            )

            assert res1["cached"] is False
            assert res1["json"] == {"analysis": "success"}
            assert mock_create.call_count == 1

            # 2. Deuxième appel identique : Hit de Cache Déterministe
            res2 = await client.complete(
                model="nmedia_cloud/claude-sonnet-4.6",
                system_prompt="System Prompt",
                user_prompt="User Prompt",
                response_schema={"type": "object"},
            )

            assert res2["cached"] is True
            assert res2["json"] == {"analysis": "success"}
            # L'appel réseau n'a pas été refait !
            assert mock_create.call_count == 1
