from __future__ import annotations

from anti_slop.config import AntiSlopConfig
from anti_slop.engine import analyze_source
from anti_slop.rules.no_test_setup_bloat import NoTestSetupBloatRule
from tests.conftest import check_code


def test_excessive_constructor_kwargs_in_test_function_flagged() -> None:
    code = """
def test_valuation():
    target = ComparableCompanyInput(
        security_id="AAPL",
        symbol="AAPL",
        name="Apple Inc.",
        currency="USD",
        market_cap=300.0,
        total_debt=50.0,
        cash=20.0,
    )
    assert target.symbol == "AAPL"
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP023"
    assert diags[0].rule_id == "no-test-setup-bloat"
    assert "Direct instantiation of `ComparableCompanyInput` in test function `test_valuation` has 7 keyword arguments" in diags[0].message


def test_excessive_constructor_in_test_class_method_flagged() -> None:
    code = """
class TestValuation:
    def test_run(self):
        item = ItemPayload(
            a="1",
            b="2",
            c="3",
            d="4",
            e="5",
            f="6",
        )
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP023"


def test_small_constructor_in_test_allowed() -> None:
    code = """
def test_pe_ratio():
    target = ComparableCompanyInput(market_cap=100.0, net_income=10.0)
    assert target.market_cap == 100.0
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 0


def test_typed_helper_builder_baseline_allowed() -> None:
    code = """
def make_company_input(
    symbol: str = "AAPL",
    *,
    market_cap: float = 300.0,
) -> ComparableCompanyInput:
    return ComparableCompanyInput(
        security_id=symbol,
        symbol=symbol,
        name="Apple Inc.",
        currency="USD",
        market_cap=market_cap,
        total_debt=50.0,
        cash=20.0,
        revenue=100.0,
    )

def test_eval():
    target = make_company_input(market_cap=150.0)
    assert target.market_cap == 150.0
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 0


def test_untyped_test_helper_missing_return_flagged() -> None:
    code = """
def make_company_input():
    return None
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP023"
    assert "missing a return type annotation" in diags[0].message


def test_untyped_test_helper_any_return_flagged() -> None:
    code = """
from typing import Any

def build_order() -> Any:
    return None
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP023"
    assert "returns untyped `Any`" in diags[0].message


def test_untyped_test_helper_untyped_kwargs_flagged() -> None:
    code = """
def make_company_input(**overrides) -> ComparableCompanyInput:
    return ComparableCompanyInput()
"""
    diags = check_code(code, NoTestSetupBloatRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP023"
    assert "uses untyped `**overrides`" in diags[0].message


def test_production_file_large_instantiation_allowed() -> None:
    code = """
def create_default_account() -> Account:
    return Account(
        a="1",
        b="2",
        c="3",
        d="4",
        e="5",
        f="6",
        g="7",
    )
"""
    cfg = AntiSlopConfig(rules={"no-test-setup-bloat": "error"})
    diags = analyze_source(code, filename="src/services/account.py", config=cfg, rules=[NoTestSetupBloatRule])
    assert len(diags) == 0
