"""Tests pour TokenCounter (MLOOP-134-BE)."""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.pipelines.token_counter import (
    TokenCounter,
    TokenUsage,
    _hash_token,
    get_token_counter,
    reset_token_counter,
)


def _fake_response(prompt_tokens=100, completion_tokens=50, model="gpt-5.4"):
    """Crée une fausse réponse API avec usage."""
    resp = MagicMock()
    resp.model = model
    resp.usage = MagicMock()
    resp.usage.prompt_tokens = prompt_tokens
    resp.usage.completion_tokens = completion_tokens
    resp.usage.prompt_tokens_details = None
    return resp


def _fake_response_cached(prompt_tokens=80, completion_tokens=30, model="gpt-5.4"):
    resp = MagicMock()
    resp.model = model
    resp.usage = MagicMock()
    resp.usage.prompt_tokens = prompt_tokens
    resp.usage.completion_tokens = completion_tokens
    resp.usage.prompt_tokens_details = {"cached_tokens": 60}
    return resp


class TestTokenUsage:
    def test_to_dict(self):
        u = TokenUsage(
            engine="codegraph",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model="gpt-5.4",
        )
        d = u.to_dict()
        assert d["engine"] == "codegraph"
        assert d["prompt_tokens"] == 100
        assert d["total_tokens"] == 150

    def test_frozen(self):
        u = TokenUsage(engine="x", prompt_tokens=1, completion_tokens=0, total_tokens=1)
        with pytest.raises(AttributeError):
            u.engine = "y"  # type: ignore[misc]


class TestHashToken:
    def test_returns_16_chars(self):
        h = _hash_token("hello world")
        assert len(h) == 16

    def test_deterministic(self):
        assert _hash_token("abc") == _hash_token("abc")

    def test_different_inputs(self):
        assert _hash_token("abc") != _hash_token("def")


class TestTokenCounter:
    def test_record_basic(self):
        c = TokenCounter(project_name="Test")
        usage = c.record(
            engine="codegraph",
            prompt_tokens=100,
            completion_tokens=50,
            model="gpt-5.4",
        )
        assert usage.total_tokens == 150
        assert c.total_tokens == 150
        assert c.total_calls == 1

    def test_record_from_response(self):
        c = TokenCounter()
        resp = _fake_response(prompt_tokens=200, completion_tokens=80)
        usage = c.record_from_response(engine="graphify", response=resp, model="gpt-5.4")
        assert usage.prompt_tokens == 200
        assert usage.completion_tokens == 80

    def test_record_cached(self):
        c = TokenCounter()
        resp = _fake_response_cached()
        usage = c.record_from_response(engine="graphify", response=resp)
        assert usage.cached is True

    def test_engine_summary(self):
        c = TokenCounter()
        c.record(engine="codegraph", prompt_tokens=100, completion_tokens=50)
        c.record(engine="codegraph", prompt_tokens=200, completion_tokens=100, cached=True)
        c.record(engine="graphify", prompt_tokens=50, completion_tokens=25)

        summary = c.get_engine_summary()
        assert "codegraph" in summary
        assert summary["codegraph"]["call_count"] == 2
        assert summary["codegraph"]["prompt_tokens"] == 300
        assert summary["codegraph"]["cache_hits"] == 1
        assert summary["codegraph"]["cache_hit_ratio"] == 0.5
        assert "graphify" in summary

    def test_question_breakdown(self):
        c = TokenCounter()
        c.record(engine="codegraph", prompt_tokens=100, completion_tokens=50, action="fact_search")
        c.record(engine="graphify", prompt_tokens=80, completion_tokens=30, action="fact_search")
        c.record(engine="codegraph", prompt_tokens=200, completion_tokens=100, action="graph_query")

        bd = c.get_question_breakdown()
        assert bd["fact_search"]["total_tokens"] == 260
        assert bd["fact_search"]["call_count"] == 2
        assert bd["graph_query"]["total_tokens"] == 300

    def test_max_entries_truncation(self):
        c = TokenCounter()
        for i in range(5100):
            c.record(engine="e", prompt_tokens=1, completion_tokens=0)
        assert c.total_calls < 5100

    def test_reset(self):
        c = TokenCounter()
        c.record(engine="e", prompt_tokens=10, completion_tokens=5)
        c.reset()
        assert c.total_tokens == 0
        assert c.total_calls == 0


class TestTrackLLMCall:
    @pytest.mark.asyncio
    async def test_records_tokens(self):
        c = TokenCounter()

        async def fake_complete(**kwargs):
            return _fake_response(prompt_tokens=120, completion_tokens=40)

        async with c.track_llm_call(
            engine="test",
            client_complete=fake_complete,
            model="gpt-5.4",
            action="unit_test",
            user_prompt="test prompt",
        ) as ctx:
            assert ctx["result"] is not None
            assert ctx["elapsed_ms"] >= 0

        assert c.total_tokens == 160
        assert c.total_calls == 1

    @pytest.mark.asyncio
    async def test_timeout_handled(self, monkeypatch):
        import src.pipelines.token_counter as tc_mod

        monkeypatch.setattr(tc_mod, "_COMPLETION_TIMEOUT_S", 0.05)
        c = TokenCounter()

        async def slow_complete(**kwargs):
            await asyncio.sleep(10)
            return _fake_response()

        with pytest.raises(asyncio.TimeoutError):
            async with c.track_llm_call(
                engine="test",
                client_complete=slow_complete,
                model="gpt-5.4",
            ):
                pass

    @pytest.mark.asyncio
    async def test_exception_propagated(self):
        c = TokenCounter()

        async def failing_complete(**kwargs):
            raise RuntimeError("API error")

        with pytest.raises(RuntimeError):
            async with c.track_llm_call(
                engine="test",
                client_complete=failing_complete,
                model="gpt-5.4",
            ):
                pass


class TestReport:
    def test_generate_report(self, tmp_path: Path):
        c = TokenCounter(project_name="ReportTest")
        c.record(engine="codegraph", prompt_tokens=100, completion_tokens=50, action="search")
        c.record(engine="graphify", prompt_tokens=200, completion_tokens=100, action="query")

        out = tmp_path / "report.json"
        report = c.generate_report(output_path=out)

        assert report["project"] == "ReportTest"
        assert report["summary"]["total_tokens"] == 450
        assert report["summary"]["total_calls"] == 2
        assert "codegraph" in report["by_engine"]
        assert "search" in report["by_question"]
        assert len(report["entries"]) == 2

        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["project"] == "ReportTest"


class TestSingleton:
    def test_get_token_counter_returns_same(self):
        c1 = get_token_counter()
        c2 = get_token_counter()
        assert c1 is c2

    def test_reset_creates_new(self):
        c1 = get_token_counter()
        c1.record(engine="x", prompt_tokens=1, completion_tokens=0)
        c2 = reset_token_counter()
        assert c2.total_calls == 0
        assert c2 is not get_token_counter() or c2.total_calls == 0
