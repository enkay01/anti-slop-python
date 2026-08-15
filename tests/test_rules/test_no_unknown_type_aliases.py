from __future__ import annotations

from anti_slop.rules.no_unknown_type_aliases import NoUnknownTypeAliasesRule
from tests.conftest import check_code


def test_type_alias_to_any_flagged():
    code = """
from typing import Any, TypeAlias

ExternalValue: TypeAlias = Any
"""
    diags = check_code(code, NoUnknownTypeAliasesRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP012"
    assert diags[0].rule_id == "no-unknown-type-aliases"


def test_simple_assignment_alias_to_any_flagged():
    code = """
from typing import Any

ExternalValue = Any
"""
    diags = check_code(code, NoUnknownTypeAliasesRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP012"


def test_domain_type_alias_allowed():
    code = """
UserId = str
"""
    diags = check_code(code, NoUnknownTypeAliasesRule)
    assert len(diags) == 0
