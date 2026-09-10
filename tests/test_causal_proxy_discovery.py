"""
Tests unitaires pour CausalProxyEngine (ADR-0354).
"""

import pytest
from src.engine.deep_search.causal_proxy import CausalProxyEngine, SignalType


def test_formulate_hypotheses():
    # Requête de cache / persistence
    hyps = CausalProxyEngine.formulate_hypotheses("Mettre en place un cache distribué SQLite")
    assert any(h.signal_type == SignalType.CAUSAL_PROXY for h in hyps)
    assert any("Persistence" in h.name for h in hyps)

    # Requête de crawl
    crawl_hyps = CausalProxyEngine.formulate_hypotheses("Améliorer le crawler pour pages SPA")
    assert any("HTTP" in h.name for h in crawl_hyps)


def test_score_source_provenance():
    # Autorité maximale (5.0)
    assert CausalProxyEngine.score_source_provenance("https://research.google/blog/planetary-prediction-engine/") == 5.0
    assert CausalProxyEngine.score_source_provenance("https://arxiv.org/abs/2608.26088") == 5.0
    assert CausalProxyEngine.score_source_provenance("https://docs.python.org/3/library/sqlite3.html") == 5.0
    assert CausalProxyEngine.score_source_provenance("https://www.ietf.org/rfc/rfc9110.txt") == 5.0

    # Domaines éducatifs / org (3.5)
    assert CausalProxyEngine.score_source_provenance("https://stanford.edu/paper.pdf") == 3.5
    assert CausalProxyEngine.score_source_provenance("https://inrb.org/data") == 3.5

    # Domaines génériques (1.5)
    assert CausalProxyEngine.score_source_provenance("https://medium.com/@user/my-blog-post") == 1.5


def test_rank_sources():
    sources = [
        {"title": "Random Blog", "url": "https://random-tech-blog.com/tips", "snippet": "..."},
        {"title": "Google Research Official", "url": "https://research.google/blog/ppe", "snippet": "..."},
        {"title": "University Paper", "url": "https://mit.edu/lab/research", "snippet": "..."},
    ]

    ranked = CausalProxyEngine.rank_sources(sources)
    assert len(ranked) == 3
    # Le premier doit être Google Research avec score 5.0
    assert ranked[0]["title"] == "Google Research Official"
    assert ranked[0]["provenance_score"] == 5.0
    assert ranked[0]["is_authoritative"] is True

    # Le second MIT (3.5)
    assert ranked[1]["title"] == "University Paper"
    assert ranked[1]["provenance_score"] == 3.5

    # Le dernier Blog (1.5)
    assert ranked[2]["title"] == "Random Blog"
    assert ranked[2]["is_authoritative"] is False
