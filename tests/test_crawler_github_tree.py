"""
Tests déterministes pour l'exploration d'arborescence GitHub et le filtre multi-tenant du crawler.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.pipelines.crawler import WebCrawlerAgent


@pytest.mark.asyncio
async def test_crawler_github_tree_priority(tmp_path):
    """Vérifie que les compétences SKILL.md sont toujours aspirées avant la documentation générale."""
    crawler = WebCrawlerAgent(max_github_files=3)
    
    fake_tree = [
        {"type": "blob", "path": "docs/general/intro.md"},
        {"type": "blob", "path": "docs/architecture/adr-001.md"},
        {"type": "blob", "path": "skills/engineering/deep-skill/SKILL.md"},
        {"type": "blob", "path": "AGENTS.md"},
        {"type": "blob", "path": "skills/productivity/grill/SKILL.md"},
    ]

    mock_client = AsyncMock()
    mock_tree_res = MagicMock()
    mock_tree_res.status_code = 200
    mock_tree_res.json.return_value = {"tree": fake_tree}
    
    mock_raw_res = MagicMock()
    mock_raw_res.status_code = 200
    mock_raw_res.text = "# Mock Content"
    
    mock_client.get.side_effect = [mock_tree_res, mock_raw_res, mock_raw_res, mock_raw_res]

    discovered = await crawler._fetch_github_repo_tree(
        client=mock_client,
        url="https://github.com/test-user/test-repo",
        docs_cache_dir=tmp_path,
        headers={},
    )

    discovered_names = [p.name for p in discovered]
    # Comme max_github_files=3, tous les 3 slots doivent être occupés par les fichiers Tier 1
    assert len(discovered) == 3
    assert "SKILL.md" in discovered_names
    assert "AGENTS.md" in discovered_names


@pytest.mark.asyncio
async def test_crawler_llms_txt_multi_tenant_protection(tmp_path):
    """Vérifie que llms.txt n'est pas sondé sur la racine pour les URLs GitHub/GitLab."""
    crawler = WebCrawlerAgent()
    mock_client = AsyncMock()

    res = await crawler._fetch_llms_txt(
        client=mock_client,
        url="https://github.com/mattpocock/skills",
        docs_cache_dir=tmp_path,
        headers={},
    )
    assert res is None
    # Aucun appel réseau ne doit avoir été déclenché
    assert mock_client.get.call_count == 0
