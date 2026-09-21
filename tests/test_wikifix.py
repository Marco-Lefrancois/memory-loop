from pathlib import Path
import pytest
from src.pipelines.wikifix import WikiFixAgent, os_relative_path


def test_wikifix_normalize_callout():
    agent = WikiFixAgent()
    assert agent._normalize_callout("note") == "NOTE"
    assert agent._normalize_callout("info") == "NOTE"
    assert agent._normalize_callout("tip") == "TIP"
    assert agent._normalize_callout("hint") == "TIP"
    assert agent._normalize_callout("warning") == "WARNING"
    assert agent._normalize_callout("danger") == "WARNING"
    assert agent._normalize_callout("error") == "WARNING"
    assert agent._normalize_callout("important") == "IMPORTANT"
    assert agent._normalize_callout("caution") == "CAUTION"
    assert agent._normalize_callout("inconnu") is None


def test_wikifix_heal_callout():
    agent = WikiFixAgent()
    healed, alerts = [], []
    line = "> [!note] Remarque importante"
    new_line, mod = agent._heal_line_callout(line, 1, "test.md", healed, alerts)
    assert mod is True
    assert new_line == "> [!NOTE] Remarque importante"
    assert len(healed) == 1
    assert healed[0]["from"] == "note"
    assert healed[0]["to"] == "NOTE"


def test_wikifix_heal_link(tmp_path: Path):
    agent = WikiFixAgent()
    doc1 = tmp_path / "docs" / "guide.md"
    doc2 = tmp_path / "docs" / "sub" / "target.md"
    doc1.parent.mkdir(parents=True, exist_ok=True)
    doc2.parent.mkdir(parents=True, exist_ok=True)
    doc1.write_text("dummy", encoding="utf-8")
    doc2.write_text("target content", encoding="utf-8")

    basename_map = {"target.md": [doc2]}
    ref_files = set()
    h_links, b_alerts = [], []

    line = "Consulter le [lien vers cible](target.md) pour plus d'infos."
    new_line, mod = agent._heal_line_links(
        line, 1, doc1, "docs/guide.md", basename_map, ref_files, h_links, b_alerts
    )
    assert mod is True
    assert "sub/target.md" in new_line
    assert len(h_links) == 1


def test_wikifix_audit_technical_leakage(tmp_path: Path):
    agent = WikiFixAgent()
    backlog_dir = tmp_path / "backlog" / "stories"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    bad_story = backlog_dir / "STORY-001.md"
    bad_story.write_text("Installation: `npm install axios` et `import * from 'redux'`", encoding="utf-8")

    leakages = agent._audit_technical_leakage(tmp_path, [bad_story])
    assert len(leakages) >= 2
    keywords = {leak["keyword"] for leak in leakages}
    assert "npm install" in keywords
    assert "import *" in keywords


def test_wikifix_detect_orphans(tmp_path: Path):
    agent = WikiFixAgent()
    f1 = tmp_path / "docs" / "page1.md"
    f2 = tmp_path / "docs" / "page2.md"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("contenu 1", encoding="utf-8")
    f2.write_text("contenu 2", encoding="utf-8")

    referenced = {f1.resolve()}
    orphans = agent._detect_orphans(tmp_path, [f1, f2], referenced)
    assert len(orphans) == 1
    assert "page2.md" in orphans[0]
