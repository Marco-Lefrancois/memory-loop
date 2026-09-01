import pytest
from src.engine.guardian import GuardianAutoReviewer, GuardianCircuitBreaker


def test_guardian_safe_reading_action():
    reviewer = GuardianAutoReviewer()
    decision = reviewer.evaluate_action(
        action_type="fs_read",
        target="docs/00-ingested/spec.md",
        context={"writable_roots": ["c:/Memory Loop/backlog"]}
    )
    assert decision.allowed is True
    assert decision.risk_level == "LOW"


def test_guardian_blocks_secret_exfiltration():
    reviewer = GuardianAutoReviewer()
    decision = reviewer.evaluate_action(
        action_type="read_external",
        target=".env",
        context={}
    )
    assert decision.allowed is False
    assert decision.risk_level == "CRITICAL"
    assert decision.requires_human_gate is True


def test_guardian_blocks_out_of_workspace_write():
    reviewer = GuardianAutoReviewer()
    decision = reviewer.evaluate_action(
        action_type="fs_write",
        target="C:/Windows/System32/evil.dll",
        context={"writable_roots": ["C:/Memory Loop/Projects/Test"]}
    )
    assert decision.allowed is False
    assert decision.risk_level == "HIGH"
    assert decision.requires_human_gate is True


def test_guardian_circuit_breaker_trips():
    reviewer = GuardianAutoReviewer()
    # 3 refus consécutifs
    for i in range(3):
        decision = reviewer.evaluate_action(
            action_type="read_external",
            target=".env",
            context={}
        )
    
    # Au 3ème refus, le circuit breaker doit avoir sauté
    assert decision.allowed is False
    assert "CIRCUIT BREAKER ACTIVÉ" in decision.rationale
