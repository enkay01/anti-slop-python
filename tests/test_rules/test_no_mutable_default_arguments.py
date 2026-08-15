from __future__ import annotations

from anti_slop.rules.no_mutable_default_arguments import NoMutableDefaultArgumentsRule
from tests.conftest import check_code


def test_mutable_list_default_flagged():
    code = """
def record_metric(name: str, tags: list[str] = []) -> None:
    pass
"""
    diags = check_code(code, NoMutableDefaultArgumentsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP021"
    assert diags[0].rule_id == "no-mutable-default-arguments"


def test_mutable_dict_default_flagged():
    code = """
def fetch(url: str, *, headers: dict[str, str] = {}) -> None:
    pass
"""
    diags = check_code(code, NoMutableDefaultArgumentsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP021"


def test_none_default_allowed():
    code = """
def record_metric(name: str, tags: list[str] | None = None) -> None:
    pass
"""
    diags = check_code(code, NoMutableDefaultArgumentsRule)
    assert len(diags) == 0


def test_immutable_tuple_default_allowed():
    code = """
def record_metric(name: str, tags: tuple[str, ...] = ()) -> None:
    pass
"""
    diags = check_code(code, NoMutableDefaultArgumentsRule)
    assert len(diags) == 0
