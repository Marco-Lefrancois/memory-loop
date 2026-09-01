import pytest
from src.bridges.mcp_loop_mem import (
    preload_story_context,
    clear_preloaded_context,
    _PRELOAD_CACHE
)

def test_preload_story_context():
    # Test preloading a story context
    result = preload_story_context("MLOOP-013-BE", "mLoop")
    assert result["status"] == "preloaded"
    assert result["story_id"] == "MLOOP-013-BE"
    assert "MLOOP-013-BE" in _PRELOAD_CACHE
    assert _PRELOAD_CACHE["MLOOP-013-BE"]["project"] == "mLoop"

def test_clear_preloaded_context():
    # Preload and then clear
    preload_story_context("MLOOP-013-BE", "mLoop")
    assert "MLOOP-013-BE" in _PRELOAD_CACHE
    
    res = clear_preloaded_context("MLOOP-013-BE")
    assert res["status"] == "cleared"
    assert "MLOOP-013-BE" not in _PRELOAD_CACHE

def test_clear_all_preloaded_context():
    preload_story_context("STORY-A", "mLoop")
    preload_story_context("STORY-B", "mLoop")
    assert len(_PRELOAD_CACHE) >= 2
    
    clear_preloaded_context()
    assert len(_PRELOAD_CACHE) == 0
