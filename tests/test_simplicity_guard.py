"""
Tests unitaires pour SimplicityGuard (ADR-0354).
"""

import pytest
from src.engine.gates.simplicity_guard import SimplicityGuard, SimplicityBudget


def test_compute_budget():
    fix_budget = SimplicityGuard.compute_budget("bugfix")
    assert fix_budget.task_scope == "PATCH"
    assert fix_budget.max_modified_files == 2
    assert fix_budget.max_added_lines == 50

    feat_budget = SimplicityGuard.compute_budget("feature")
    assert feat_budget.task_scope == "STANDARD"
    assert feat_budget.max_modified_files == 4
    assert feat_budget.max_added_lines == 180

    rewrite_budget = SimplicityGuard.compute_budget("feature", explicit_full_rewrite=True)
    assert rewrite_budget.task_scope == "EXPANSION"
    assert rewrite_budget.allow_new_packages is True


def test_evaluate_diff_within_budget():
    budget = SimplicityBudget(max_modified_files=2, max_added_lines=20)
    diff = """
diff --git a/src/utils.py b/src/utils.py
--- a/src/utils.py
+++ b/src/utils.py
+def helper():
+    return True
"""
    report = SimplicityGuard.evaluate_diff(diff, budget)
    assert report.passed
    assert report.modified_files_count == 1
    assert report.added_lines_count == 2
    assert report.violations == []


def test_evaluate_diff_exceeding_budget():
    budget = SimplicityBudget(max_modified_files=1, max_added_lines=3)
    diff = """
diff --git a/src/file1.py b/src/file1.py
--- a/src/file1.py
+++ b/src/file1.py
+1
+2
+3
+4
+5
diff --git a/src/file2.py b/src/file2.py
--- a/src/file2.py
+++ b/src/file2.py
+1
"""
    report = SimplicityGuard.evaluate_diff(diff, budget)
    assert not report.passed
    assert len(report.violations) >= 2  # Trop de fichiers ET trop de lignes
    assert report.pruning_suggestion is not None
    assert "Single-Shot Pruning" in report.pruning_suggestion


def test_evaluate_diff_unauthorized_dependencies():
    budget = SimplicityBudget(allow_new_dependencies=False)
    diff = """
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
+heavy-library>=2.0.0
"""
    report = SimplicityGuard.evaluate_diff(diff, budget)
    assert not report.passed
    assert any("dépendances" in v for v in report.violations)
