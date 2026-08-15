from __future__ import annotations

from anti_slop.rules.no_chained_type_assertions import NoChainedTypeAssertionsRule
from tests.conftest import check_code


def test_chained_cast_flagged():
    code = """
from typing import cast, Any

# SAFETY: Outer cast
val = cast(User, cast(Any, raw_input))
"""
    diags = check_code(code, NoChainedTypeAssertionsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP001"
    assert diags[0].rule_id == "no-chained-type-assertions"


def test_single_cast_allowed():
    code = """
from typing import cast

# SAFETY: Validated by parser
val = cast(User, raw_input)
"""
    diags = check_code(code, NoChainedTypeAssertionsRule)
    assert len(diags) == 0
