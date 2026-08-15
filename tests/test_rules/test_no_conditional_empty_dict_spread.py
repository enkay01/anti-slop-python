from __future__ import annotations

from anti_slop.rules.no_conditional_empty_dict_spread import NoConditionalEmptyDictSpreadRule
from tests.conftest import check_code


def test_conditional_empty_dict_spread_flagged():
    code = """
options = {
    "base": 1,
    **({"timeout": timeout} if timeout is not None else {}),
}
"""
    diags = check_code(code, NoConditionalEmptyDictSpreadRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP002"
    assert diags[0].rule_id == "no-conditional-empty-object-spread"


def test_normal_spread_allowed():
    code = """
defaults = {"a": 1}
overrides = {"b": 2}
merged = {**defaults, **overrides}
"""
    diags = check_code(code, NoConditionalEmptyDictSpreadRule)
    assert len(diags) == 0
