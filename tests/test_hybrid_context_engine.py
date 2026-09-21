"""Tests unitaires pour le pipeline hybride CodeGraph → Graft → Intersection (MLOOP-131-BE / MLOOP-133-BE)."""

from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.pipelines.hybrid_context_engine import (
    HybridResult,
    _compute_score,
    _extract_files_from_codegraph,
    _extract_files_from_graft,
    _extract_graft_exit_code,
    _normalize_path,
    hybrid_context_search,
)


# ── Helpers pour simuler les moteurs ──────────────────────────────────────


def _make_codegraph_result(files: List[str]) -> Dict[str, Any]:
    return {"symbols": [{"file": f} for f in files]}


def _make_graft_result(files: List[str]) -> Dict[str, Any]:
    return {"callers": [{"file": f} for f in files]}


def _fake_codegraph(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    return _make_codegraph_result(
        [
            "src/main.py",
            "src/utils.py",
            "src/handler.py",
        ]
    )


def _fake_graft(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    return _make_graft_result(
        [
            "src/utils.py",
            "src/handler.py",
            "src/helper.py",
        ]
    )


def _failing_codegraph(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    raise ConnectionError("CodeGraph server unreachable")


def _failing_graft(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    raise TimeoutError("Graft timeout")


def _graft_with_exit_code(files: List[str], exit_code: int) -> Dict[str, Any]:
    """Graft result with explicit exit_code field (MLOOP-133-BE)."""
    return {"callers": [{"file": f} for f in files], "exit_code": exit_code}


def _graft_exit_code_1(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    """Graft callers that returns exit_code=1 (failure)."""
    return _graft_with_exit_code(["src/utils.py"], exit_code=1)


def _graft_exit_code_0(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    """Graft callers that returns exit_code=0 (success) with partial results."""
    return _graft_with_exit_code(["src/utils.py", "src/handler.py"], exit_code=0)


def _codegraph_extended(query: str, project_path: Path, timeout: float = 30.0) -> Dict[str, Any]:
    """CodeGraph with broader results for fallback merge."""
    return _make_codegraph_result(
        [
            "src/utils.py",
            "src/handler.py",
            "src/main.py",
            "src/fallback.py",
        ]
    )


# ── Tests des helpers ─────────────────────────────────────────────────────


class TestNormalizePath:
    def test_backslash_to_slash(self):
        assert _normalize_path("src\\main.py") == "src/main.py"

    def test_lowercase(self):
        assert _normalize_path("SRC/Main.PY") == "src/main.py"

    def test_strips_whitespace(self):
        assert _normalize_path("  src/main.py  ") == "src/main.py"


class TestComputeScore:
    def test_both_engines(self):
        assert _compute_score(True, True, (0.6, 0.4)) == 1.0

    def test_codegraph_only(self):
        assert _compute_score(True, False, (0.6, 0.4)) == 0.6

    def test_graft_only(self):
        assert _compute_score(False, True, (0.6, 0.4)) == 0.4

    def test_neither(self):
        assert _compute_score(False, False, (0.6, 0.4)) == 0.0


class TestExtractFiles:
    def test_codegraph_dict_symbols(self):
        result = {"symbols": [{"file": "a.py"}, {"file": "b.py"}]}
        assert _extract_files_from_codegraph(result) == ["a.py", "b.py"]

    def test_codegraph_dict_files(self):
        result = {"files": [{"path": "x.py"}]}
        assert _extract_files_from_codegraph(result) == ["x.py"]

    def test_codegraph_strings(self):
        result = {"symbols": ["a.py", "b.py"]}
        assert _extract_files_from_codegraph(result) == ["a.py", "b.py"]

    def test_graft_callers(self):
        result = {"callers": [{"file": "c.py"}]}
        assert _extract_files_from_graft(result) == ["c.py"]

    def test_graft_strings(self):
        result = {"callers": ["d.py"]}
        assert _extract_files_from_graft(result) == ["d.py"]


# ── Tests du pipeline hybride ─────────────────────────────────────────────


class TestHybridContextSearch:
    def test_nominal_hybrid(self):
        result = hybrid_context_search(
            query="test_query",
            codegraph_fn=_fake_codegraph,
            graft_fn=_fake_graft,
        )
        assert result.mode == "hybrid"
        assert result.codegraph_count == 3
        assert result.graft_count == 3
        assert result.intersection_count == 2
        assert len(result.files) == 4
        assert result.files[0]["score"] == 1.0
        assert result.files[0]["source"] == "intersection"

    def test_fallback_codegraph_only(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=None,
        )
        assert result.mode == "fallback_codegraph"
        assert len(result.files) == 3
        assert all(f["source"] == "codegraph" for f in result.files)

    def test_fallback_graft_only(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=None,
            graft_fn=_fake_graft,
        )
        assert result.mode == "fallback_graft"
        assert len(result.files) == 3
        assert all(f["source"] == "graft" for f in result.files)

    def test_no_engines(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=None,
            graft_fn=None,
        )
        assert result.mode == "fallback_none"
        assert result.files == []

    def test_codegraph_failure_fallback_to_graft(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_failing_codegraph,
            graft_fn=_fake_graft,
        )
        assert result.mode == "fallback_graft"
        assert len(result.files) == 3
        assert any("CodeGraph indisponible" in w for w in result.warnings)

    def test_graft_failure_fallback_to_codegraph(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=_failing_graft,
        )
        assert result.mode == "fallback_graft_to_codegraph"
        assert result.fallback_triggered is True
        assert len(result.files) == 3
        assert any("Graft indisponible" in w for w in result.warnings)

    def test_weights_normalization(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=_fake_graft,
            weights=(0.7, 0.5),
        )
        assert result.warnings[0].startswith("Somme des poids")
        total = result.weights[0] + result.weights[1]
        assert abs(total - 1.0) < 0.01

    def test_custom_weights(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=_fake_graft,
            weights=(0.8, 0.2),
        )
        intersection_file = next(f for f in result.files if f["source"] == "intersection")
        assert intersection_file["score"] == 1.0
        cg_only = next(f for f in result.files if f["source"] == "codegraph_only")
        assert cg_only["score"] == 0.8

    def test_elapsed_ms_populated(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=_fake_graft,
        )
        assert result.elapsed_ms >= 0

    def test_empty_results(self):
        def empty_cg(q: str, p: Path, t: float = 30.0) -> Dict[str, Any]:
            return {"symbols": []}

        def empty_gr(q: str, p: Path, t: float = 30.0) -> Dict[str, Any]:
            return {"callers": []}

        result = hybrid_context_search(
            query="test",
            codegraph_fn=empty_cg,
            graft_fn=empty_gr,
        )
        assert result.mode == "hybrid"
        assert result.files == []
        assert result.intersection_count == 0

    # ── Tests MLOOP-133-BE : Fallback automatique Graft → CodeGraph ──────

    def test_graft_exit_code_nonzero_triggers_fallback(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_codegraph_extended,
            graft_fn=_graft_exit_code_1,
        )
        assert result.fallback_triggered is True
        assert result.mode == "fallback_graft_to_codegraph"
        assert result.graft_exit_code == 1
        assert any("Graft callers failed" in w for w in result.warnings)

    def test_graft_exit_code_nonzero_merges_partial_results(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_codegraph_extended,
            graft_fn=_graft_exit_code_1,
        )
        file_ids = {f["file"] for f in result.files}
        assert "src/utils.py" in file_ids
        assert "src/fallback.py" in file_ids

    def test_graft_exit_code_zero_no_fallback(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_codegraph_extended,
            graft_fn=_graft_exit_code_0,
        )
        assert result.fallback_triggered is False
        assert result.mode == "hybrid"
        assert result.graft_exit_code == 0

    def test_graft_exception_triggers_fallback(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=_failing_graft,
        )
        assert result.fallback_triggered is True
        assert result.mode == "fallback_graft_to_codegraph"
        assert any("Graft indisponible" in w for w in result.warnings)

    def test_graft_exit_code_without_codegraph_fallback(self):
        result = hybrid_context_search(
            query="test",
            codegraph_fn=None,
            graft_fn=_graft_exit_code_1,
        )
        assert result.fallback_triggered is True
        assert result.mode == "fallback_graft_partial"
        assert any("CodeGraph non disponible" in w for w in result.warnings)

    def test_graft_exit_code_none_treated_as_success(self):
        """When exit_code is absent from result, no fallback triggered."""

        def graft_no_exit(q: str, p: Path, t: float = 30.0) -> Dict[str, Any]:
            return {"callers": [{"file": "src/a.py"}]}

        result = hybrid_context_search(
            query="test",
            codegraph_fn=_fake_codegraph,
            graft_fn=graft_no_exit,
        )
        assert result.fallback_triggered is False
        assert result.mode == "hybrid"


class TestExtractGraftExitCode:
    def test_exit_code_field(self):
        assert _extract_graft_exit_code({"exit_code": 1}) == 1

    def test_returncode_field(self):
        assert _extract_graft_exit_code({"returncode": 2}) == 2

    def test_no_exit_code(self):
        assert _extract_graft_exit_code({"callers": []}) is None

    def test_exit_code_zero(self):
        assert _extract_graft_exit_code({"exit_code": 0}) == 0
