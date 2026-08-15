from __future__ import annotations

from anti_slop.rules.no_silent_exception_swallow import NoSilentExceptionSwallowRule
from tests.conftest import check_code


def test_silent_pass_flagged():
    code = """
try:
    process()
except Exception:
    pass
"""
    diags = check_code(code, NoSilentExceptionSwallowRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP018"
    assert diags[0].rule_id == "no-silent-exception-swallow"


def test_dummy_assignment_swallow_flagged():
    code = """
try:
    process()
except Exception:
    _ = None
"""
    diags = check_code(code, NoSilentExceptionSwallowRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP018"


def test_unchained_raise_flagged():
    code = """
try:
    process()
except ValueError as e:
    raise RuntimeError("Failed to process")
"""
    diags = check_code(code, NoSilentExceptionSwallowRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP018"


def test_chained_raise_allowed():
    code = """
try:
    process()
except ValueError as e:
    raise RuntimeError("Failed to process") from e
"""
    diags = check_code(code, NoSilentExceptionSwallowRule)
    assert len(diags) == 0
