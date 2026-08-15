from __future__ import annotations

from anti_slop.rules.no_excessive_optional_fields import NoExcessiveOptionalFieldsRule
from tests.conftest import check_code


def test_dataclass_with_excessive_optional_fields_flagged():
    code = """
from dataclasses import dataclass

@dataclass(frozen=True)
class BcaSourceRecord:
    id: str
    identity: str | None
    mileage: int | None
    cap_clean_price: int | None
    clean_condition: bool | None
    write_off_reported: bool | None
"""
    diags = check_code(code, NoExcessiveOptionalFieldsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP022"
    assert diags[0].rule_id == "no-excessive-optional-fields"
    assert "BcaSourceRecord" in diags[0].message


def test_complete_domain_dataclass_allowed():
    code = """
from dataclasses import dataclass

@dataclass(frozen=True)
class AuctionLot:
    id: str
    identity: str
    mileage: int
    cap_clean_price: int
    trim: str | None = None
"""
    diags = check_code(code, NoExcessiveOptionalFieldsRule)
    assert len(diags) == 0


def test_patch_or_query_options_exempted():
    code = """
from dataclasses import dataclass

@dataclass(frozen=True)
class UserUpdatePatch:
    name: str | None = None
    email: str | None = None
    role: str | None = None
"""
    diags = check_code(code, NoExcessiveOptionalFieldsRule)
    assert len(diags) == 0


def test_massive_compound_null_check_chain_flagged():
    code = """
def validate(record):
    if (
        record.a is None
        or record.b is None
        or record.c is None
        or record.d is None
    ):
        return False
    return True
"""
    diags = check_code(code, NoExcessiveOptionalFieldsRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP022"
    assert "4 null checks" in diags[0].message
