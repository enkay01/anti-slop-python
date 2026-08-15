from __future__ import annotations

from anti_slop.rules.no_widen_then_assert import NoWidenThenAssertRule
from tests.conftest import check_code


def test_widen_then_cast_flagged():
    code = """
from typing import Any, cast

# SAFETY: Tested
loaded: Any = {"id": "123"}
# SAFETY: Asserting back
user = cast(dict, loaded)
"""
    diags = check_code(code, NoWidenThenAssertRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP014"
    assert diags[0].rule_id == "no-widen-then-assert"


def test_clean_flow_allowed():
    code = """
from typing import cast

# SAFETY: Parsed external json
user = cast(dict, raw_data)
"""
    diags = check_code(code, NoWidenThenAssertRule)
    assert len(diags) == 0
