from __future__ import annotations

from anti_slop.rules.no_shape_in_symbol_names import NoShapeInSymbolNamesRule
from tests.conftest import check_code


def test_shape_in_class_name_flagged():
    code = """
class UserShape:
    id: str
"""
    diags = check_code(code, NoShapeInSymbolNamesRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP009"
    assert diags[0].rule_id == "no-shape-in-symbol-names"


def test_shape_in_variable_name_flagged():
    code = """
user_shape = {"id": "123"}
"""
    diags = check_code(code, NoShapeInSymbolNamesRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP009"


def test_clean_domain_name_allowed():
    code = """
class User:
    id: str

user_instance = User()
"""
    diags = check_code(code, NoShapeInSymbolNamesRule)
    assert len(diags) == 0
