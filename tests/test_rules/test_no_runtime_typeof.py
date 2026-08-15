from __future__ import annotations

from anti_slop.config import AntiSlopConfig
from anti_slop.engine import analyze_source
from anti_slop.rules.no_runtime_typeof import NoRuntimeTypeofRule
from tests.conftest import check_code


def test_isinstance_check_flagged():
    code = """
if isinstance(payload, dict):
    process(payload)
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP008"
    assert diags[0].rule_id == "no-runtime-typeof"


def test_type_is_check_flagged():
    code = """
if type(payload) is str:
    print(payload)
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP008"


def test_type_laundering_helper_function_flagged():
    code = """
def is_exact_type(val, expected_type):
    return type(val) is expected_type
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    # Flags both the function definition and the inner type() check
    assert len(diags) >= 1
    assert any(d.code == "SLOP008" for d in diags)


def test_type_laundering_call_flagged():
    code = """
if is_exact_type(self.id, AuctionLotId):
    proceed()
"""
    diags = check_code(code, NoRuntimeTypeofRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP008"


def test_allow_in_type_guards_option():
    code = """
from typing import TypeGuard

def is_user_dict(val: object) -> TypeGuard[dict[str, str]]:
    return isinstance(val, dict)
"""
    config = AntiSlopConfig(
        rules={"no-runtime-typeof": {"severity": "error", "options": {"allow_in_type_guards": True}}}
    )
    diags = analyze_source(code, filename="guard.py", config=config, rules=[NoRuntimeTypeofRule])
    assert len(diags) == 0
