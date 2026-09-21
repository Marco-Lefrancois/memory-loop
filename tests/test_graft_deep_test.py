"""
Tests unitaires pour le pipeline Graft Deep Build (MLOOP-132-BE).
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipelines.graft_deep_test import (
    AskResult,
    DeepTestReport,
    Metrics,
    _aggregate_metrics,
    _extract_files_from_json,
    compute_metrics,
    format_report,
    run_graft_ask,
    run_graft_build_deep,
    run_deep_test_suite,
)


# --- compute_metrics ---


def test_compute_metrics_perfect_match():
    m = compute_metrics(["a.py", "b.py"], ["a.py", "b.py"])
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.f1 == 1.0
    assert m.tp == 2
    assert m.fp == 0
    assert m.fn == 0


def test_compute_metrics_partial_match():
    m = compute_metrics(["a.py", "b.py", "c.py"], ["a.py", "b.py"])
    assert m.tp == 2
    assert m.fp == 1
    assert m.fn == 0
    assert m.precision == pytest.approx(2 / 3, abs=0.01)
    assert m.recall == 1.0


def test_compute_metrics_no_match():
    m = compute_metrics(["x.py"], ["a.py"])
    assert m.recall == 0.0
    assert m.precision == 0.0
    assert m.f1 == 0.0
    assert m.fn == 1


def test_compute_metrics_empty_ground_truth():
    m = compute_metrics(["a.py"], [])
    assert m.precision == 0.0
    assert m.recall == 0.0


def test_compute_metrics_empty_found():
    m = compute_metrics([], ["a.py"])
    assert m.recall == 0.0
    assert m.precision == 0.0
    assert m.fn == 1


# --- _extract_files_from_json ---


def test_extract_files_from_json_pointer():
    stdout = json.dumps({"hits": [{"symbol": {"pointer": "src/click/core.py:L100-L200"}}]})
    assert _extract_files_from_json(stdout) == ["src/click/core.py"]


def test_extract_files_from_json_path():
    stdout = json.dumps({"hits": [{"path": "tests/test_basic.py"}]})
    assert _extract_files_from_json(stdout) == ["tests/test_basic.py"]


def test_extract_files_from_json_fallback_regex():
    stdout = "Some error mentioning src/click/core.py and tests/test_basic.py"
    files = _extract_files_from_json(stdout)
    assert "src/click/core.py" in files
    assert "tests/test_basic.py" in files


def test_extract_files_from_json_empty():
    assert _extract_files_from_json("") == []
    assert _extract_files_from_json("not json at all") == []


# --- _aggregate_metrics ---


def test_aggregate_metrics():
    results = [
        {"precision": 0.5, "recall": 1.0, "f1": 0.67, "tp": 2, "fp": 2, "fn": 0},
        {"precision": 1.0, "recall": 0.5, "f1": 0.67, "tp": 1, "fp": 0, "fn": 1},
    ]
    agg = _aggregate_metrics(results)
    assert agg.precision == pytest.approx(0.75, abs=0.01)
    assert agg.recall == pytest.approx(0.75, abs=0.01)
    assert agg.tp == 3


def test_aggregate_metrics_empty():
    agg = _aggregate_metrics([])
    assert agg.precision == 0.0
    assert agg.recall == 0.0


# --- run_graft_build_deep ---


@patch("src.pipelines.graft_deep_test._run_graft_command")
def test_run_graft_build_deep_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    ok, exit_code, stderr = run_graft_build_deep("/tmp/corpus", timeout=60)
    assert ok is True
    assert exit_code == 0
    mock_run.assert_called_once_with(
        ["build", "--deep"],
        cwd="/tmp/corpus",
        timeout=60,
    )


@patch("src.pipelines.graft_deep_test._run_graft_command")
def test_run_graft_build_deep_failure(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr="some error")
    ok, exit_code, stderr = run_graft_build_deep("/tmp/corpus")
    assert ok is False
    assert exit_code == 1
    assert "some error" in stderr


# --- run_graft_ask ---


@patch("src.pipelines.graft_deep_test._run_graft_command")
def test_run_graft_ask_deep(mock_run):
    stdout = json.dumps({"hits": [{"symbol": {"pointer": "src/click/core.py:L50"}}]})
    mock_run.return_value = MagicMock(returncode=0, stdout=stdout)
    result = run_graft_ask("How does X work?", "/tmp/corpus", deep=True)
    assert result.files == ["src/click/core.py"]
    assert result.exit_code == 0
    args = mock_run.call_args[0][0]
    assert "--no-graph-rank" not in args


@patch("src.pipelines.graft_deep_test._run_graft_command")
def test_run_graft_ask_lexical(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout='{"hits": []}')
    result = run_graft_ask("test", "/tmp/corpus", deep=False)
    args = mock_run.call_args[0][0]
    assert "--no-graph-rank" in args


# --- test_graft_deep_build (integration with mocks) ---


@patch("src.pipelines.graft_deep_test.run_graft_ask")
@patch("src.pipelines.graft_deep_test.run_graft_build_deep")
def test_run_deep_test_suite_full(mock_build, mock_ask):
    mock_build.return_value = (True, 0, "")
    mock_ask.return_value = AskResult(files=["a.py"], exit_code=0)
    bugs = [{"id": "BUG-01", "question": "test?", "ground_truth": ["a.py"]}]
    report = run_deep_test_suite("/tmp/corpus", bugs=bugs, timeout=60)
    assert report.build_success is True
    assert len(report.lexical_results) == 1
    assert len(report.deep_results) == 1
    assert report.recall_delta == 0.0


@patch("src.pipelines.graft_deep_test.run_graft_build_deep")
def test_run_deep_test_suite_build_failure(mock_build):
    mock_build.return_value = (False, 1, "build error")
    report = run_deep_test_suite("/tmp/corpus")
    assert report.build_success is False
    assert report.lexical_results == []


# --- format_report ---


def test_format_report_basic():
    report = DeepTestReport(
        corpus_path="/tmp/corpus",
        build_success=True,
        build_stderr="",
        lexical_results=[{"bug_id": "B1", "recall": 0.4, "exit_code": 0}],
        deep_results=[{"bug_id": "B1", "recall": 0.5, "files": ["a.py"], "exit_code": 0}],
        lexical_agg=Metrics(precision=0.3, recall=0.4, f1=0.35),
        deep_agg=Metrics(precision=0.6, recall=0.7, f1=0.65),
        recall_delta=0.3,
        timestamp="2026-09-21T00:00:00Z",
    )
    md = format_report(report)
    assert "MLOOP-132-BE" in md
    assert "OK" in md
    assert "0.3" in md
    assert "B1" in md


def test_format_report_build_failure():
    report = DeepTestReport(
        corpus_path="/tmp/corpus",
        build_success=False,
        build_stderr="timeout",
        timestamp="2026-09-21T00:00:00Z",
    )
    md = format_report(report)
    assert "FAILED" in md
    assert "timeout" in md


# --- Dataclass defaults ---


def test_ask_result_defaults():
    r = AskResult()
    assert r.files == []
    assert r.exit_code == -1


def test_deep_test_report_defaults():
    r = DeepTestReport()
    assert r.build_success is False
    assert r.recall_delta == 0.0
