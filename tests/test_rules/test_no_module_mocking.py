from __future__ import annotations

from anti_slop.rules.no_module_mocking import NoModuleMockingRule
from tests.conftest import check_code


def test_unittest_mock_patch_flagged():
    code = """
from unittest.mock import patch

@patch("myapp.services.user_service")
def test_user(mock_service):
    pass
"""
    diags = check_code(code, NoModuleMockingRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP004"
    assert diags[0].rule_id == "no-module-mocking"


def test_mocker_patch_call_flagged():
    code = """
def test_call(mocker):
    mocker.patch("myapp.services.fetch")
"""
    diags = check_code(code, NoModuleMockingRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP004"


def test_dependency_injection_allowed():
    code = """
class FakeUserService:
    def get_user(self, user_id: str):
        return {"id": user_id}

def test_user_di():
    service = FakeUserService()
    assert service.get_user("123") == {"id": "123"}
"""
    diags = check_code(code, NoModuleMockingRule)
    assert len(diags) == 0
