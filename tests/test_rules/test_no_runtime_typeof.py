from __future__ import annotations

from anti_slop.rules.no_runtime_typeof import NoRuntimeTypeofRule
from tests.conftest import check_code


def test_isinstance_check_allowed():
    code = """
if isinstance(payload, dict):
    process(payload)
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) == 0


def test_type_is_check_flagged():
    code = """
if type(payload) is str:
    print(payload)
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP008"


def test_class_identity_check_flagged():
    code = """
if payload.__class__ is int:
    print(payload)
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP008"


def test_type_laundering_helper_function_flagged():
    code = """
def matches_kind(val: object, expected_type: object) -> bool:
    return type(val) is expected_type
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) >= 1
    assert any(d.code == "SLOP008" for d in diags)
