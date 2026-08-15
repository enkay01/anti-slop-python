from __future__ import annotations

from anti_slop.rules.no_reflect_apply import NoReflectApplyRule
from tests.conftest import check_code


def test_getattr_call_flagged():
    code = """
value = getattr(user, "calculate_total")()
"""
    diags = check_code(code, NoReflectApplyRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP006"
    assert diags[0].rule_id == "no-reflect-apply"


def test_methodcaller_flagged():
    code = """
import operator
caller = operator.methodcaller("do_work", 1, 2)
"""
    diags = check_code(code, NoReflectApplyRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP006"


def test_direct_call_allowed():
    code = """
value = user.calculate_total()
"""
    diags = check_code(code, NoReflectApplyRule)
    assert len(diags) == 0
