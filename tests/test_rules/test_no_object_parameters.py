from __future__ import annotations

from anti_slop.rules.no_object_parameters import NoObjectParametersRule
from tests.conftest import check_code


def test_object_parameter_flagged():
    code = """
def save(value: object) -> None:
    pass
"""
    diags = check_code(code, NoObjectParametersRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP005"
    assert diags[0].rule_id == "no-object-parameters"


def test_typed_parameter_allowed():
    code = """
from dataclasses import dataclass

@dataclass
class User:
    id: str

def save(value: User) -> None:
    pass
"""
    diags = check_code(code, NoObjectParametersRule)
    assert len(diags) == 0
