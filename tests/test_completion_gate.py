from src.pipelines.completion_gate import CompletionGate, GateStatus

def test_completion_gate_empty_patch_claimed_success():
    res = CompletionGate.validate_patch("", claimed_status="success")
    assert res.status == GateStatus.DEGENERATE_CANDIDATE
    assert res.is_degenerate is True
    assert res.requires_hitl is True
    assert any("Patch vide" in r for r in res.reasons)

def test_completion_gate_stubs_detected():
    patch = """
--- a/file.py
+++ b/file.py
@@ -1,3 +1,6 @@
+def feature():
+    # TODO: implement this logic later
+    pass
"""
    res = CompletionGate.validate_patch(patch, claimed_status="success")
    assert res.status == GateStatus.DEGENERATE_CANDIDATE
    assert res.requires_hitl is True
    assert any("stub(s)" in w for w in res.warnings)

def test_completion_gate_valid_patch():
    patch = """
--- a/file.py
+++ b/file.py
@@ -1,3 +1,6 @@
+def feature():
+    result = calculate_metrics()
+    return result * 2
"""
    res = CompletionGate.validate_patch(patch, claimed_status="success")
    assert res.status == GateStatus.PASS
    assert res.is_degenerate is False
    assert res.requires_hitl is False
    assert len(res.warnings) == 0
