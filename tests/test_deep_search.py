# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.engine.deep_search.pipeline import run_deep_search, execute_web_search, DeepSearchResult
from src.state import LoopState


def test_deep_search_result_structure():
    res = DeepSearchResult(query="test query", project_name="mLoop")
    assert res.query == "test query"
    assert res.project_name == "mLoop"
    assert res.local_facts == []
    assert res.web_sources == []
    assert res.crawled_files == []
    assert res.dossier_path is None


def test_execute_web_search_fallback():
    # Test that execute_web_search returns a list of dictionaries
    with patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(
            returncode=0,
            stdout='{"query": "taste", "results": [{"title": "Taste Result", "url": "https://example.com/taste", "snippet": "Taste snippet"}]}'
        )
        results = execute_web_search("taste", limit=2)
        assert len(results) == 1
        assert results[0]["title"] == "Taste Result"
        assert results[0]["url"] == "https://example.com/taste"


def test_run_deep_search_end_to_end(tmp_path):
    project_path = tmp_path / "Projects" / "mLoop"
    project_path.mkdir(parents=True, exist_ok=True)
    state = LoopState(project_name="mLoop")

    mock_web_results = [
        {"title": "Taste Skill Official", "url": "https://github.com/Leonxlnx/taste-skill", "snippet": "Anti-slop skill for frontend agents."}
    ]

    with patch("src.engine.deep_search.pipeline.execute_web_search", return_value=mock_web_results), \
         patch("src.pipelines.crawler.WebCrawlerAgent.execute") as mock_crawler_exec:

        result = run_deep_search(
            query="taste-skill anti-slop",
            project_name="mLoop",
            state=state,
            project_path=project_path,
            max_sources=1,
            depth=0,
        )

        assert result.query == "taste-skill anti-slop"
        assert len(result.web_sources) == 1
        assert result.dossier_path is not None
        assert result.dossier_path.exists()

        dossier_content = result.dossier_path.read_text(encoding="utf-8")
        assert "Deep Research Dossier" in dossier_content
        assert "What It Actually Proves" in dossier_content
        assert "What It Does Not Prove" in dossier_content
        assert "Taste Skill Official" in dossier_content

        sources_path = project_path / "reference" / "research" / "SOURCES.md"
        assert sources_path.exists()
        assert "https://github.com/Leonxlnx/taste-skill" in sources_path.read_text(encoding="utf-8")
