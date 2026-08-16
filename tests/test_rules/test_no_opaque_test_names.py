from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_opaque_test_names import NoOpaqueTestNamesRule


def test_enumerator_names_flagged():
    code = """
def test1():
    assert compute() == 1

def test_2():
    assert compute() == 2

def test_case_3():
    assert compute() == 3
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoOpaqueTestNamesRule])
    assert len(diags) == 3
    assert all(d.code == "SLOP027" for d in diags)


def test_single_letter_names_flagged():
    code = """
def test_a():
    assert compute() == 1
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoOpaqueTestNamesRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP027"


def test_generic_vague_names_flagged():
    code = """
def test_works():
    assert compute() == 1

def test_it():
    assert compute() == 1

def test_run():
    assert compute() == 1
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoOpaqueTestNamesRule])
    assert len(diags) == 3
    assert all(d.code == "SLOP027" for d in diags)


def test_descriptive_names_allowed():
    code = """
def test_computes_total_with_tax():
    assert compute_total(100, 0.1) == 110

def test_rejects_negative_price():
    assert compute_total(-5, 0.1) is None
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoOpaqueTestNamesRule])
    assert len(diags) == 0
