from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_assertionless_test import NoAssertionlessTestRule


def test_assertionless_function_flagged():
    code = """
def test_user_creation():
    user = create_user("alice")
    user.activate()
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP025"
    assert diags[0].rule_id == "no-assertionless-test"
    assert "test_user_creation" in diags[0].message


def test_test_with_assert_allowed():
    code = """
def test_user_creation():
    user = create_user("alice")
    assert user.is_active is True
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 0


def test_test_with_pytest_raises_allowed():
    code = """
import pytest

def test_invalid_user_raises():
    with pytest.raises(ValueError):
        create_user("")
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 0


def test_test_with_mock_assertion_allowed():
    code = """
def test_notifier_called(notifier):
    send_notification("hello")
    notifier.assert_called_once_with("hello")
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 0


def test_test_with_unittest_assert_allowed():
    code = """
class TestUser:
    def test_name(self):
        self.assertEqual(get_name(), "alice")
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 0


def test_pure_stub_or_abstract_allowed():
    code = """
from abc import abstractmethod

class BaseTest:
    @abstractmethod
    def test_interface(self):
        pass

    def test_stub(self):
        ...
"""
    diags = analyze_source(code, filename="test_user.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 0


def test_non_test_file_ignored():
    code = """
def test_helper():
    do_something()
"""
    diags = analyze_source(code, filename="service.py", rules=[NoAssertionlessTestRule])
    assert len(diags) == 0
