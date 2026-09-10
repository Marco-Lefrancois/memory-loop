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

def test_extract_markdown_links():
    agent = WebCrawlerAgent(include_paths=[r'.*\.md$'])
    md_content = """
# Reference
Check the [Skill](https://github.com/nanzhipro/Karpathy-llm-wiki-bootstrap-skill/blob/main/skill/SKILL.md)
and [Schema](./SCHEMA.md) or [Ignore Image](https://example.com/pic.png).
    """
    links = agent._extract_markdown_links(md_content, "https://github.com/nanzhipro/Karpathy-llm-wiki-bootstrap-skill/blob/main/README.md")
    assert any("SKILL.md" in l for l in links)
    assert any("SCHEMA.md" in l for l in links)
    assert not any("pic.png" in l for l in links)

def test_all_sources_initialization():
    agent_default = WebCrawlerAgent()
    assert agent_default.all_sources is False

    agent_all = WebCrawlerAgent(all_sources=True)
    assert agent_all.all_sources is True


def test_crawler_domain_quota_and_dedup():
    agent = WebCrawlerAgent(max_domain_requests=2)
    assert agent.max_domain_requests == 2
    assert agent.domain_request_counts == {}
    assert len(agent.seen_content_hashes) == 0

    # Simulate domain tracking
    agent.domain_request_counts["example.com"] = 2
    assert agent.domain_request_counts["example.com"] >= agent.max_domain_requests


def test_is_empty_spa_shell():
    from src.pipelines.crawler import is_empty_spa_shell

    spa_html = '<html><body><div id="root"></div><script src="/bundle.js"></script></body></html>'
    assert is_empty_spa_shell(spa_html, "") is True

    next_html = '<html><body><div id="__next"></div><noscript>You need to enable JavaScript</noscript></body></html>'
    assert is_empty_spa_shell(next_html, "Loading...") is True

    full_html = '<html><body><h1>Real Article</h1><p>' + ('This is substantive content with lots of facts. ' * 30) + '</p></body></html>'
    assert is_empty_spa_shell(full_html, "This is substantive content with lots of facts. " * 30) is False


def test_crawler_render_js_and_github_tree_options():
    agent = WebCrawlerAgent(render_js=True, github_tree=False)
    assert agent.render_js is True
    assert agent.github_tree is False

    agent_default = WebCrawlerAgent()
    assert agent_default.render_js is False
    assert agent_default.github_tree is True
