from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_private_member_test_access import NoPrivateMemberTestAccessRule


def test_private_attribute_access_flagged():
    code = """
def test_private_state():
    user = User("alice")
    assert user._password_hash == "secret"
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoPrivateMemberTestAccessRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP030"
    assert diags[0].rule_id == "no-private-member-test-access"
    assert "_password_hash" in diags[0].message


def test_private_method_call_flagged():
    code = """
def test_private_method():
    calc = Calculator()
    res = calc._internal_compute()
    assert res == 42
"""
    diags = analyze_source(code, filename="test_calc.py", rules=[NoPrivateMemberTestAccessRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP030"


def test_self_private_helper_allowed():
    code = """
class TestCalculator:
    def _create_calc(self):
        return Calculator()

    def test_calc(self):
        calc = self._create_calc()
        assert calc.add(1, 2) == 3
"""
    diags = analyze_source(code, filename="test_calc.py", rules=[NoPrivateMemberTestAccessRule])
    assert len(diags) == 0


def test_dunder_access_allowed():
    code = """
def test_dunder():
    assert User.__name__ == "User"
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoPrivateMemberTestAccessRule])
    assert len(diags) == 0


def test_production_file_ignored():
    code = """
class InternalWorker:
    def run(self, parent):
        return parent._state
"""
    diags = analyze_source(code, filename="worker.py", rules=[NoPrivateMemberTestAccessRule])
    assert len(diags) == 0
