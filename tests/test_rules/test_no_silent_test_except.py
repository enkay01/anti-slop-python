from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_silent_test_except import NoSilentTestExceptRule


def test_try_except_pass_flagged():
    code = """
def test_swallowed():
    try:
        risky_operation()
    except ValueError:
        pass
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoSilentTestExceptRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP026"
    assert diags[0].rule_id == "no-silent-test-except"
    assert "test_swallowed" in diags[0].message


def test_try_except_pytest_fail_flagged():
    code = """
import pytest

def test_manual_fail():
    try:
        run_process()
    except Exception as e:
        pytest.fail(f"Failed unexpectedly: {e}")
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoSilentTestExceptRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP026"


def test_try_except_reraise_allowed():
    code = """
def test_cleanup_on_error():
    try:
        run_process()
    except Exception:
        cleanup()
        raise
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoSilentTestExceptRule])
    assert len(diags) == 0


def test_pytest_raises_allowed():
    code = """
import pytest

def test_expected_error():
    with pytest.raises(ValueError):
        risky_operation()
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoSilentTestExceptRule])
    assert len(diags) == 0
