import time
from pathlib import Path
from src.pipelines.crawler import (
    strip_tracking_params,
    normalize_url,
    is_path_allowed,
    is_domain_allowed,
    is_external_link_allowed,
    WebCrawlerAgent,
)

def test_strip_tracking_params():
    url = 'https://example.com/docs/api?utm_source=twitter&utm_medium=cpc&ref=ml&id=123'
    cleaned = strip_tracking_params(url)
    assert 'utm_source' not in cleaned
    assert 'utm_medium' not in cleaned
    assert 'ref' not in cleaned
    assert 'id=123' in cleaned

def test_normalize_url():
    base = 'https://docs.firecrawl.dev'
    rel = '/features/crawl?utm_campaign=launch#section'
    normalized = normalize_url(rel, base)
    assert normalized == 'https://docs.firecrawl.dev/features/crawl'

    ignored = normalize_url('https://example.com/search?q=test&sort=desc', ignore_query=True)
    assert ignored == 'https://example.com/search'

def test_is_path_allowed():
    include = [r'^/docs/.*', r'^/api/.*']
    exclude = [r'.*\.pdf$', r'.*/draft/.*']

    assert is_path_allowed('https://example.com/docs/intro', include, exclude) is True
    assert is_path_allowed('https://example.com/api/v2/users', include, exclude) is True
    assert is_path_allowed('https://example.com/blog/news', include, exclude) is False
    assert is_path_allowed('https://example.com/docs/spec.pdf', include, exclude) is False
    assert is_path_allowed('https://example.com/docs/draft/item', include, exclude) is False

def test_is_domain_allowed():
    base = 'https://firecrawl.dev'
    assert is_domain_allowed('https://firecrawl.dev/docs', base, allow_subdomains=False) is True
    assert is_domain_allowed('https://docs.firecrawl.dev/intro', base, allow_subdomains=True) is True
    assert is_domain_allowed('https://docs.firecrawl.dev/intro', base, allow_subdomains=False) is False
    assert is_domain_allowed('https://other.dev/intro', base, allow_subdomains=True) is False

def test_is_external_link_allowed():
    base = 'https://firecrawl.dev'
    # External homepage should be skipped
    assert is_external_link_allowed('https://github.com', base, allow_external=True) is False
    assert is_external_link_allowed('https://github.com/', base, allow_external=True) is False
    # Deep external link allowed
    assert is_external_link_allowed('https://github.com/google/skills', base, allow_external=True) is True
    assert is_external_link_allowed('https://github.com/google/skills', base, allow_external=False) is False

def test_check_max_age_cache(tmp_path):
    agent = WebCrawlerAgent(max_age=3600)
    test_file = tmp_path / 'crawl_test.md'
    test_file.write_text('content', encoding='utf-8')

    assert agent._check_max_age_cache(test_file) is True

    # Expired cache
    agent_expired = WebCrawlerAgent(max_age=0)
    assert agent_expired._check_max_age_cache(test_file) is False
