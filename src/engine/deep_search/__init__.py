"""
Module Deep Search mLoop (Sovereign Multi-Hop Autonomous Research - ADR-0335).
Combine Fact-Search FTS5 interne, Web Search multi-provider et WebCrawlerAgent.
"""
from .pipeline import run_deep_search, DeepSearchResult

__all__ = ["run_deep_search", "DeepSearchResult"]
