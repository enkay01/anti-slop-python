from __future__ import annotations

from anti_slop.rules.no_known_value_widening import NoKnownValueWideningRule
from tests.conftest import check_code


def test_widening_dict_literal_to_any_dict_flagged():
    code = """
from typing import Any

handlers: dict[str, Any] = {
    "start": start_handler,
}
"""
    diags = check_code(code, NoKnownValueWideningRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP003"
    assert diags[0].rule_id == "no-known-value-widening"


def test_empty_dict_accumulator_allowed():
    code = """
from typing import Any

cache: dict[str, Any] = {}
"""
    diags = check_code(code, NoKnownValueWideningRule)
    assert len(diags) == 0


def test_typed_dict_or_inference_allowed():
    code = """
handlers = {
    "start": start_handler,
}
"""
    diags = check_code(code, NoKnownValueWideningRule)
    assert len(diags) == 0
