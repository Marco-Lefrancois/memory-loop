"""
Tests unitaires pour VerificationLeakageGate (ADR-0354).
"""

import pytest
from src.engine.gates.verification_leakage import VerificationLeakageGate


@pytest.fixture
def gate():
    return VerificationLeakageGate()


def test_clean_blackbox_test_passes(gate):
    code = """
def test_addition():
    calc = Calculator()
    res = calc.add(2, 3)
    assert res == 5
"""
    report = gate.check_code(code, "test_clean.py")
    assert report.passed
    assert report.critical_count == 0


def test_private_attribute_assertion_rejected(gate):
    code = """
def test_leaky_private():
    service = UserService()
    service.register("alice")
    assert service._internal_cache["alice"] is not None
"""
    report = gate.check_code(code, "test_leaky.py")
    assert not report.passed
    assert report.critical_count >= 1
    assert any(v.criterion == 1 for v in report.violations)


def test_tautological_assertion_rejected(gate):
    code = """
def test_tautology():
    val = 42
    assert val == val
"""
    report = gate.check_code(code, "test_tautology.py")
    assert not report.passed
    assert any(v.criterion == 2 for v in report.violations)


def test_empty_assertion_function_rejected(gate):
    code = """
def test_no_assertions():
    service = UserService()
    service.do_something()
    # Aucun assert
"""
    report = gate.check_code(code, "test_empty.py")
    assert not report.passed
    assert any(v.criterion == 3 for v in report.violations)


def test_gherkin_private_leakage_rejected(gate):
    gherkin = """
Feature: User login
  Scenario: Login succeeds
    Given a valid user
    When user logs in
    Then the _private_auth_token is generated
"""
    report = gate.check_code(gherkin, "login.feature")
    assert not report.passed
    assert any(v.criterion == 1 for v in report.violations)
