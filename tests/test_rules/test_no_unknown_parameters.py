from __future__ import annotations

from anti_slop.rules.no_unknown_parameters import NoUnknownParametersRule
from tests.conftest import check_code


def test_any_parameter_flagged():
    code = """
from typing import Any

def handle(input_data: Any) -> None:
    pass
"""
    diags = check_code(code, NoUnknownParametersRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP010"
    assert diags[0].rule_id == "no-unknown-parameters"


def test_cause_parameter_allowed():
    code = """
from typing import Any

def wrap_error(message: str, cause: Any = None) -> Exception:
    return Exception(message)
"""
    diags = check_code(code, NoUnknownParametersRule)
    assert len(diags) == 0


def test_domain_parameter_allowed():
    code = """
def handle(user_id: str) -> None:
    pass
"""
    diags = check_code(code, NoUnknownParametersRule)
    assert len(diags) == 0
