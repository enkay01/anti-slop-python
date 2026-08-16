from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_tautological_assert import NoTautologicalAssertRule


def test_assert_true_flagged():
    code = """
def test_something():
    assert True
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTautologicalAssertRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP024"
    assert diags[0].rule_id == "no-tautological-assert"


def test_assert_constant_number_flagged():
    code = """
def test_something():
    assert 1
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTautologicalAssertRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP024"


def test_assert_non_empty_list_flagged():
    code = """
def test_something():
    assert [1, 2, 3]
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTautologicalAssertRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP024"


def test_assert_self_comparison_flagged():
    code = """
def test_something():
    x = 42
    assert x == x
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTautologicalAssertRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP024"
    assert "self-comparison" in diags[0].message


def test_assert_attribute_self_comparison_flagged():
    code = """
def test_something():
    assert sut.status == sut.status
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTautologicalAssertRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP024"


def test_assert_dynamic_value_allowed():
    code = """
def test_something():
    result = compute()
    assert result == 42
    assert result is not None
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTautologicalAssertRule])
    assert len(diags) == 0
