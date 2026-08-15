from __future__ import annotations

from anti_slop.rules.no_unknown_returns import NoUnknownReturnsRule
from tests.conftest import check_code


def test_any_return_flagged():
    code = """
from typing import Any

def load_user() -> Any:
    return "some_raw_data"
"""
    diags = check_code(code, NoUnknownReturnsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP011"
    assert diags[0].rule_id == "no-unknown-returns"


def test_awaitable_any_return_flagged():
    code = """
from typing import Any, Awaitable

def fetch_data() -> Awaitable[Any]:
    pass
"""
    diags = check_code(code, NoUnknownReturnsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP011"


def test_domain_return_allowed():
    code = """
from dataclasses import dataclass

@dataclass
class User:
    id: str

def load_user() -> User:
    return User(id="1")
"""
    diags = check_code(code, NoUnknownReturnsRule)
    assert len(diags) == 0
