"""
Unit Tests for mLoop Runnable Gates & Depth Tree Engine (ADR-0341).
"""

import sys
import tempfile
import unittest
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.core.gates import (
    Gate,
    GateLedger,
    claim_lease,
    compute_path_fingerprint,
    compute_sha256,
    execute_single_gate,
    lint_ledger,
    parse_expect_pattern,
    parse_gates,
    patterns_overlap,
    release_lease,
    render_depth_tree_visual,
    render_progress_bar,
    verify_ledger,
)


class TestGatesEngine(unittest.TestCase):

    def test_compute_sha256_and_path_fingerprint(self):
        digest = compute_sha256("test output data")
        self.assertEqual(len(digest), 64)
        fp = compute_path_fingerprint()
        self.assertIn("dirs", fp)

    def test_parse_expect_pattern(self):
        kind, pat, ci = parse_expect_pattern("hello world")
        self.assertEqual(kind, "text")
        self.assertEqual(pat, "hello world")
        self.assertFalse(ci)

        kind, pat, ci = parse_expect_pattern("/1 passed/i")
        self.assertEqual(kind, "regex")
        self.assertEqual(pat, "1 passed")
        self.assertTrue(ci)

    def test_parse_valid_ledger(self):
        sample = """# Gates: Authentication Module
OWNS: src/auth/**, tests/auth/**
Scope: JWT verification

- [ ] G1: Valid token returns 200
  CHECK: python -c "print('status: 200 OK')"
  EXPECT: 200 OK
  EVIDENCE: pending

- [x] G2: Expired token returns 401
  CHECK: python -c "print('status: 401 Unauthorized')"
  EXPECT: /401/
  CWD: .
  EVIDENCE: met | exit:0

- [ ] G3: Review UI copy
  EVIDENCE: pending
"""
        ledger = parse_gates(sample)
        self.assertTrue(ledger.is_valid)
        self.assertEqual(len(ledger.gates), 3)
        self.assertEqual(ledger.owns, ["src/auth/**", "tests/auth/**"])
        self.assertEqual(ledger.title, "Gates: Authentication Module")
        self.assertEqual(ledger.scope, "JWT verification")

        g1 = ledger.gates[0]
        self.assertEqual(g1.id, "G1")
        self.assertEqual(g1.title, "Valid token returns 200")
        self.assertTrue(g1.is_runnable)
        self.assertFalse(g1.checked)

        g3 = ledger.gates[2]
        self.assertEqual(g3.id, "G3")
        self.assertTrue(g3.is_manual)

    def test_parse_strict_errors(self):
        # 1. No IDs
        bad_sample1 = "- [ ] Missing id"
        l1 = parse_gates(bad_sample1)
        self.assertFalse(l1.is_valid)
        self.assertTrue(any("ID explicite" in e for e in l1.errors))

        # 2. Duplicate IDs
        bad_sample2 = """- [ ] G1: First
- [ ] G1: Second"""
        l2 = parse_gates(bad_sample2)
        self.assertFalse(l2.is_valid)
        self.assertTrue(any("dupliqué" in e for e in l2.errors))

        # 3. Indented ABANDON
        bad_sample3 = """- [ ] G1: First
  ABANDON: G1 impossible"""
        l3 = parse_gates(bad_sample3)
        self.assertFalse(l3.is_valid)
        self.assertTrue(any("ABANDON indenté" in e for e in l3.errors))

    def test_abandon_handling(self):
        sample = """- [ ] G1: API endpoint works
  CHECK: python -c "print('ok')"
  EXPECT: ok
  EVIDENCE: pending

ABANDON: G1 Service externe indisponible
"""
        ledger = parse_gates(sample)
        self.assertTrue(ledger.is_valid)
        self.assertIn("G1", ledger.abandoned)
        self.assertEqual(ledger.abandoned["G1"], "Service externe indisponible")

        status = verify_ledger(ledger, root_dir=Path.cwd(), update_file=False)
        self.assertFalse(status.all_met)
        self.assertTrue(status.handoff_required)

    def test_execute_single_gate_success(self):
        gate = Gate(
            line_no=1,
            id="G1",
            title="Python version check",
            check='python -c "print(\'Python 3 ready\')"',
            expect="Python 3 ready"
        )
        res = execute_single_gate(gate, root_dir=Path.cwd())
        self.assertTrue(res.passed)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(res.expect_matched)
        self.assertIn("met", res.evidence_text)
        self.assertIn("sha256:", res.evidence_text)

    def test_execute_single_gate_failure(self):
        gate = Gate(
            line_no=1,
            id="G2",
            title="Non-matching expectation",
            check='python -c "print(\'error happened\')"',
            expect="all good"
        )
        res = execute_single_gate(gate, root_dir=Path.cwd())
        self.assertFalse(res.passed)
        self.assertIn("failed", res.evidence_text)

    def test_linter_anti_tautology(self):
        sample = """- [ ] G1: Fake check
  CHECK: echo ok
  EXPECT: ok
  EVIDENCE: pending

- [ ] G2: Lancer la vérification
  CHECK: python -c "print('test passed')"
  EXPECT: test passed
  EVIDENCE: pending
"""
        ledger = parse_gates(sample)
        issues = lint_ledger(ledger)
        self.assertTrue(any("tautologique" in i.message for i in issues))
        self.assertTrue(any("activité" in i.message for i in issues))

    def test_atomic_file_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "test.gates.md"
            content = """# Gates: File Update
- [ ] G1: Success gate
  CHECK: python -c "print('unit test pass')"
  EXPECT: unit test pass
  EVIDENCE: pending
"""
            tmp_path.write_text(content, encoding="utf-8")
            ledger = parse_gates(tmp_path.read_text(encoding="utf-8"), file_path=tmp_path)
            status = verify_ledger(ledger, root_dir=Path(tmpdir), update_file=True)

            self.assertTrue(status.all_met)
            updated_text = tmp_path.read_text(encoding="utf-8")
            self.assertIn("- [x] G1: Success gate", updated_text)
            self.assertIn("EVIDENCE: met |", updated_text)

    def test_lease_locking_and_overlap(self):
        self.assertTrue(patterns_overlap("src/auth/**", "src/auth/jwt.py"))
        self.assertTrue(patterns_overlap("src/**", "src/api/**"))
        self.assertFalse(patterns_overlap("src/auth/**", "src/billing/**"))

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir_path = Path(tmpdir)
            ok, msg = claim_lease("scope_a", "leaf_1", ["src/auth/**"], tmp_dir_path)
            self.assertTrue(ok)

            # Conflicting claim
            ok2, msg2 = claim_lease("scope_a", "leaf_2", ["src/auth/jwt.py"], tmp_dir_path)
            self.assertFalse(ok2)
            self.assertIn("Collision OWNS", msg2)

            # Non-conflicting claim
            ok3, msg3 = claim_lease("scope_a", "leaf_3", ["src/billing/**"], tmp_dir_path)
            self.assertTrue(ok3)

            # Release
            release_lease("scope_a", "leaf_1", tmp_dir_path)
            ok4, msg4 = claim_lease("scope_a", "leaf_2", ["src/auth/jwt.py"], tmp_dir_path)
            self.assertTrue(ok4)

    def test_visual_tree_rendering(self):
        sample = """# Gates: Demo Tree
OWNS: src/core/**
Scope: Visual Demo

- [ ] G1: Step 1
  CHECK: python -c "print('step1 ok')"
  EXPECT: step1 ok
  EVIDENCE: pending
"""
        ledger = parse_gates(sample)
        status = verify_ledger(ledger, root_dir=Path.cwd(), update_file=False)
        tree = render_depth_tree_visual(ledger.title, status, scope="test", owns=ledger.owns)
        self.assertIn("MLOOP DEPTH TREE & RUNNABLE GATES", tree)
        self.assertIn("Scope : test", tree)
        self.assertIn("PROGRESS:", tree)


if __name__ == "__main__":
    unittest.main()
