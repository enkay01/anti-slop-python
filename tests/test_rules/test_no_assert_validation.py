from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_assert_validation import NoAssertValidationRule


def test_assert_in_service_flagged():
    code = """
def process(amount: int) -> None:
    assert amount > 0, "amount must be positive"
"""
    diags = analyze_source(code, filename="service.py", rules=[NoAssertValidationRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP020"
    assert diags[0].rule_id == "no-assert-validation"


def test_assert_in_test_file_allowed():
    code = """
def test_something():
    assert 1 == 1
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoAssertValidationRule])
    assert len(diags) == 0


def test_assert_with_safety_comment_allowed():
    code = """
def process(node):
    # SAFETY: Node is proven non-null by caller invariant
    assert node is not None
"""
    diags = analyze_source(code, filename="service.py", rules=[NoAssertValidationRule])
    assert len(diags) == 0
