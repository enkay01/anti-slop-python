from __future__ import annotations

from anti_slop.rules.no_reflect_get import NoReflectGetRule
from tests.conftest import check_code


def test_dynamic_getattr_flagged():
    code = """
name = getattr(user, dynamic_field)
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP007"
    assert diags[0].rule_id == "no-reflect-get"


def test_dynamic_attrgetter_flagged():
    code = """
import operator
getter = operator.attrgetter(dynamic_field)
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP007"


def test_eval_flagged():
    code = """
name = eval("user.name")
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP007"


def test_dict_subscript_flagged():
    code = """
name = user.__dict__["name"]
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP007"


def test_constant_getattr_allowed():
    code = """
name = getattr(user, "name", None)
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 0


def test_typed_attribute_access_allowed():
    code = """
name = user.name
"""
    diags = check_code(code, NoReflectGetRule)
    assert len(diags) == 0
