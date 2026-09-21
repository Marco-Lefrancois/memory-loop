"""
Tests unitaires pour MLOOP-135-BE — Benchmark Multi-Dépôts.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipelines.multi_repo_benchmark import (
    ALL,
    _agg,
    _extract,
    _load_datasets,
    _pr,
    _report,
    run_multi_repo_benchmark,
)


class TestLoadDatasets:
    def test_loads_three_repos(self):
        assert len(ALL) == 3

    def test_has_required_keys(self):
        for key in ("small", "medium", "large"):
            assert key in ALL
            repo = ALL[key]
            for field in ("name", "url", "commit", "size", "files", "bugs"):
                assert field in repo

    def test_ten_bugs_per_repo(self):
        for repo in ALL.values():
            assert len(repo["bugs"]) == 10

    def test_bug_structure(self):
        for repo in ALL.values():
            for bug in repo["bugs"]:
                for key in ("id", "commit", "desc", "q", "gt", "sym"):
                    assert key in bug

    def test_json_file_exists(self):
        json_path = Path(__file__).parent.parent / "src" / "pipelines" / "multi_repo_datasets.json"
        assert json_path.exists()


class TestExtract:
    def test_extracts_python_files(self):
        text = "Found src/click/core.py and tests/test_basic.py and httpx/_client.py"
        files = _extract(text)
        assert "src/click/core.py" in files
        assert "tests/test_basic.py" in files
        assert "httpx/_client.py" in files

    def test_deduplicates(self):
        text = "src/click/core.py src/click/core.py"
        files = _extract(text)
        assert len(files) == 1

    def test_ignores_non_python(self):
        text = "README.md src/click/core.py docs/config.json"
        files = _extract(text)
        assert files == ["src/click/core.py"]


class TestPrecisionRecall:
    def test_perfect_match(self):
        result = _pr(["a.py", "b.py"], ["a.py", "b.py"])
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0
        assert result["tp"] == 2
        assert result["fp"] == 0
        assert result["fn"] == 0

    def test_no_match(self):
        result = _pr(["x.py"], ["a.py"])
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0

    def test_partial_match(self):
        result = _pr(["a.py", "x.py"], ["a.py", "b.py"])
        assert result["tp"] == 1
        assert result["fp"] == 1
        assert result["fn"] == 1

    def test_empty_gt(self):
        result = _pr(["a.py"], [])
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0

    def test_empty_found(self):
        result = _pr([], ["a.py"])
        assert result["recall"] == 0.0
        assert result["fn"] == 1


class TestAggregate:
    def test_aggregates_runs(self):
        runs = [
            {
                "explore": {"precision": 0.8, "recall": 0.6, "f1": 0.7, "lat": 1.0, "exit": 0},
                "callers": {"precision": 0.9, "recall": 0.5, "f1": 0.6, "lat": 0.5, "exit": 0},
            },
            {
                "explore": {"precision": 0.6, "recall": 0.8, "f1": 0.7, "lat": 1.5, "exit": 0},
                "callers": {"precision": 0.7, "recall": 0.7, "f1": 0.7, "lat": 0.8, "exit": 0},
            },
        ]
        result = _agg(runs)
        assert "explore" in result
        assert "callers" in result
        assert result["explore"]["precision"] == 0.7
        assert result["explore"]["recall"] == 0.7
        assert result["explore"]["success_rate"] == 1.0

    def test_empty_runs(self):
        assert _agg([]) == {}

    def test_mixed_exit_codes(self):
        runs = [
            {"explore": {"precision": 0.5, "recall": 0.5, "f1": 0.5, "lat": 1.0, "exit": 0}},
            {"explore": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "lat": 0.0, "exit": -1}},
        ]
        result = _agg(runs)
        assert result["explore"]["success_rate"] == 0.5


class TestReport:
    def test_generates_markdown(self):
        all_r = {
            "small": {
                "aggregated": {
                    "explore": {
                        "precision": 0.5,
                        "recall": 0.7,
                        "f1": 0.6,
                        "lat": 1.0,
                        "success_rate": 1.0,
                    },
                    "callers": {
                        "precision": 0.6,
                        "recall": 0.5,
                        "f1": 0.55,
                        "lat": 0.5,
                        "success_rate": 0.8,
                    },
                }
            },
            "medium": {
                "aggregated": {
                    "explore": {
                        "precision": 0.4,
                        "recall": 0.6,
                        "f1": 0.5,
                        "lat": 2.0,
                        "success_rate": 1.0,
                    },
                }
            },
            "large": {"error": "clone_failed", "aggregated": {}},
        }
        report = _report(all_r)
        assert "# MLOOP-135-BE" in report
        assert "pallets/click" in report
        assert "encode/httpx" in report
        assert "pallets/flask" in report
        assert "Tendances" in report

    def test_report_handles_errors(self):
        all_r = {"small": {"error": "clone_failed", "aggregated": {}}}
        report = _report(all_r)
        assert "Échec" in report


class TestRunBenchmark:
    @patch("src.pipelines.multi_repo_benchmark._init_cg", return_value=True)
    @patch("src.pipelines.multi_repo_benchmark._clone", return_value=True)
    @patch("src.pipelines.multi_repo_benchmark._bench_bug")
    def test_runs_all_repos(self, mock_bench, mock_clone, mock_init, tmp_path):
        mock_bench.return_value = {
            "bug": "B01",
            "explore": {"files": [], "lat": 0, "exit": 0, "precision": 0, "recall": 0, "f1": 0},
            "callers": {"files": [], "lat": 0, "exit": 0, "precision": 0, "recall": 0, "f1": 0},
        }
        with (
            patch("src.pipelines.multi_repo_benchmark.SCRATCH", tmp_path / "scratch"),
            patch("src.pipelines.multi_repo_benchmark.RESULTS", tmp_path / "results"),
        ):
            result = run_multi_repo_benchmark(skip_clone=True)
        assert "results" in result
        assert len(result["results"]) == 3
        assert mock_bench.call_count == 30  # 3 repos x 10 bugs

    @patch("src.pipelines.multi_repo_benchmark._init_cg", return_value=True)
    @patch("src.pipelines.multi_repo_benchmark._clone", return_value=True)
    @patch("src.pipelines.multi_repo_benchmark._bench_bug")
    def test_runs_single_repo(self, mock_bench, mock_clone, mock_init, tmp_path):
        mock_bench.return_value = {
            "bug": "B01",
            "explore": {"files": [], "lat": 0, "exit": 0, "precision": 0, "recall": 0, "f1": 0},
            "callers": {"files": [], "lat": 0, "exit": 0, "precision": 0, "recall": 0, "f1": 0},
        }
        with (
            patch("src.pipelines.multi_repo_benchmark.SCRATCH", tmp_path / "scratch"),
            patch("src.pipelines.multi_repo_benchmark.RESULTS", tmp_path / "results"),
        ):
            result = run_multi_repo_benchmark(repo_labels=["small"], skip_clone=True)
        assert len(result["results"]) == 1
        assert mock_bench.call_count == 10


class TestConstraints:
    def test_module_under_300_lines(self):
        module_path = Path(__file__).parent.parent / "src" / "pipelines" / "multi_repo_benchmark.py"
        lines = module_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 300, f"Module has {len(lines)} lines, ADR-0202 max is 300"

    def test_json_dataset_exists(self):
        json_path = Path(__file__).parent.parent / "src" / "pipelines" / "multi_repo_datasets.json"
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert len(data) == 3
        for key in ("click", "httpx", "flask"):
            assert key in data
