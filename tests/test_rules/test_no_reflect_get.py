from __future__ import annotations

from anti_slop.rules.no_reflect_get import NoReflectGetRule
from tests.conftest import check_code


def test_getattr_flagged():
    code = """
name = getattr(user, "name")
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP007"
    assert diags[0].rule_id == "no-reflect-get"


def test_typed_attribute_access_allowed():
    code = """
name = user.name
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 0
