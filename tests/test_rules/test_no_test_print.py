from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_test_print import NoTestPrintRule


def test_print_in_test_flagged():
    code = """
def test_something():
    result = compute()
    print(f"Debug result: {result}")
    assert result == 42
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTestPrintRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP029"
    assert diags[0].rule_id == "no-test-print"
    assert "print" in diags[0].message


def test_sys_stdout_write_flagged():
    code = """
import sys

def test_something():
    sys.stdout.write("hello\\n")
    assert True
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTestPrintRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP029"


def test_print_in_production_allowed():
    code = """
def cli_main():
    print("Welcome to CLI")
"""
    diags = analyze_source(code, filename="cli.py", rules=[NoTestPrintRule])
    assert len(diags) == 0
