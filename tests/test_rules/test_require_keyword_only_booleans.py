from __future__ import annotations

from anti_slop.rules.require_keyword_only_booleans import RequireKeywordOnlyBooleansRule
from tests.conftest import check_code


def test_positional_boolean_flagged():
    code = """
def sync_data(user_id: str, force_refresh: bool = False) -> None:
    pass
"""
    diags = check_code(code, RequireKeywordOnlyBooleansRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP017"
    assert diags[0].rule_id == "require-keyword-only-booleans"


def test_keyword_only_boolean_allowed():
    code = """
def sync_data(user_id: str, *, force_refresh: bool = False) -> None:
    pass
"""
    diags = check_code(code, RequireKeywordOnlyBooleansRule)
    assert len(diags) == 0
