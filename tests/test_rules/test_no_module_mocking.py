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


def test_monkeypatch_setattr_flagged():
    code = """
def test_monkey(monkeypatch):
    monkeypatch.setattr("myapp.services.fetch", lambda: None)
"""
    diags = check_code(code, NoModuleMockingRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP004"


def test_framework_patch_decorator_allowed():
    code = """
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@app.patch("/users/{user_id}")
def update_user(user_id: str):
    pass

@router.patch("/items/{item_id}")
def update_item(item_id: str):
    pass
"""
    diags = check_code(code, NoModuleMockingRule)
    assert len(diags) == 0


def test_http_client_patch_method_allowed():
    code = """
def test_api_client(client, requests, httpx):
    client.patch("/api/v1/resource", json={"status": "ok"})
    requests.patch("https://example.com/api", json={})
    httpx.patch("https://example.com/api", json={})
"""
    diags = check_code(code, NoModuleMockingRule)
    assert len(diags) == 0


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
