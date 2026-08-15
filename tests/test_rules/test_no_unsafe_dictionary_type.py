from __future__ import annotations

from anti_slop.rules.no_unsafe_dictionary_type import NoUnsafeDictionaryTypeRule
from tests.conftest import check_code


def test_dict_str_any_flagged():
    code = """
from typing import Any

metadata: dict[str, Any] = {}
"""
    diags = check_code(code, NoUnsafeDictionaryTypeRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP013"
    assert diags[0].rule_id == "no-unsafe-dictionary-type"


def test_mapping_str_object_flagged():
    code = """
from typing import Mapping

metadata: Mapping[str, object]
"""
    diags = check_code(code, NoUnsafeDictionaryTypeRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP013"


def test_typed_dict_allowed():
    code = """
from typing import TypedDict

class UserMeta(TypedDict):
    name: str
    age: int

meta: UserMeta = {"name": "Alice", "age": 30}
"""
    diags = check_code(code, NoUnsafeDictionaryTypeRule)
    assert len(diags) == 0
