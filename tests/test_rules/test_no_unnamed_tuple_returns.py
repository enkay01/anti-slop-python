from __future__ import annotations

from anti_slop.rules.no_unnamed_tuple_returns import NoUnnamedTupleReturnsRule
from tests.conftest import check_code


def test_heterogeneous_tuple_return_flagged():
    code = """
def authenticate() -> tuple[bool, str, int]:
    return True, "ok", 1
"""
    diags = check_code(code, NoUnnamedTupleReturnsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP019"
    assert diags[0].rule_id == "no-unnamed-tuple-returns"


def test_homogeneous_tuple_allowed():
    code = """
def get_coordinates() -> tuple[float, ...]:
    return (1.0, 2.0)
"""
    diags = check_code(code, NoUnnamedTupleReturnsRule)
    assert len(diags) == 0


def test_dataclass_return_allowed():
    code = """
from dataclasses import dataclass

@dataclass(frozen=True)
class AuthResult:
    is_authenticated: bool
    message: str
    user_id: int

def authenticate() -> AuthResult:
    return AuthResult(True, "ok", 1)
"""
    diags = check_code(code, NoUnnamedTupleReturnsRule)
    assert len(diags) == 0
