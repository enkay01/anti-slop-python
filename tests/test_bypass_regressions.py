from __future__ import annotations

from anti_slop.config import AntiSlopConfig
from anti_slop.engine import analyze_source


def test_slop008_class_identity_flagged() -> None:
    code = """
if x.__class__ is int:
    pass
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert any(d.code == "SLOP008" for d in diagnostics)


def test_slop008_structural_helper_flagged() -> None:
    code = """
def matches_kind(x: object) -> bool:
    return type(x) is int
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert any(d.code == "SLOP008" for d in diagnostics)


def test_slop008_isinstance_clean() -> None:
    code = """
def process(node: object) -> bool:
    if isinstance(node, int):
        return True
    return False
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert not any(d.code == "SLOP008" for d in diagnostics)


def test_slop020_assert_in_production_flagged_despite_comment() -> None:
    code = """
# SAFETY: value was validated by request schema decoder
assert x > 0
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert any(d.code == "SLOP020" for d in diagnostics)


def test_slop020_assert_in_test_file_clean() -> None:
    code = """
def test_something():
    assert 1 + 1 == 2
"""
    diagnostics = analyze_source(code, filename="tests/test_service.py")
    assert not any(d.code == "SLOP020" for d in diagnostics)


def test_slop015_cast_unconfigured_flagged() -> None:
    code = """
from typing import cast

def parse(raw: object) -> str:
    return cast(str, raw)
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert any(d.code == "SLOP015" for d in diagnostics)


def test_slop015_cast_matching_boundary_modules_clean() -> None:
    code = """
from typing import cast

def parse(raw: object) -> str:
    return cast(str, raw)
"""
    cfg = AntiSlopConfig(
        options={"require-safety-comment-for-type-assertion": {"boundary_modules": ["src/adapters/**"]}}
    )
    diagnostics = analyze_source(code, filename="src/adapters/user.py", config=cfg)
    assert not any(d.code == "SLOP015" for d in diagnostics)


def test_slop022_renamed_anemic_model_flagged() -> None:
    code = """
from dataclasses import dataclass

@dataclass
class UserUpdate:
    a: str | None = None
    b: str | None = None
    c: str | None = None
    d: str | None = None
"""
    diagnostics = analyze_source(code, filename="src/models.py")
    assert any(d.code == "SLOP022" for d in diagnostics)


def test_slop022_typeddict_total_false_clean() -> None:
    code = """
from typing import TypedDict

class UserPatch(TypedDict, total=False):
    a: str
    b: str
    c: str
    d: str
"""
    diagnostics = analyze_source(code, filename="src/models.py")
    assert not any(d.code == "SLOP022" for d in diagnostics)


def test_slop010_slop011_public_unannotated_flagged() -> None:
    code = """
def handle(payload):
    pass
"""
    diagnostics = analyze_source(code, filename="src/api.py")
    codes = {d.code for d in diagnostics}
    assert "SLOP010" in codes
    assert "SLOP011" in codes


def test_private_unannotated_clean() -> None:
    code = """
def _helper(payload):
    pass
"""
    diagnostics = analyze_source(code, filename="src/api.py")
    assert not any(d.code in {"SLOP010", "SLOP011"} for d in diagnostics)


def test_slop007_constant_getattr_clean() -> None:
    code = """
def get_user_email(obj: object) -> str | None:
    return getattr(obj, "email", None)
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert not any(d.code == "SLOP007" for d in diagnostics)


def test_slop007_dict_subscript_flagged() -> None:
    code = """
def read_dynamic(obj: object, k: str) -> object:
    return obj.__dict__[k]
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert any(d.code == "SLOP007" for d in diagnostics)


def test_slop018_dummy_assignment_swallow_flagged() -> None:
    code = """
def run() -> None:
    try:
        do_work()
    except Exception:
        skipped = True
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert any(d.code == "SLOP018" for d in diagnostics)


def test_slop018_handled_exception_return_clean() -> None:
    code = """
def run() -> int | None:
    try:
        return do_work()
    except ValueError:
        return None
"""
    diagnostics = analyze_source(code, filename="src/service.py")
    assert not any(d.code == "SLOP018" for d in diagnostics)


def test_slop004_test_file_direct_mock_assign_flagged() -> None:
    code = """
from unittest.mock import MagicMock

def test_handler():
    mod.fn = MagicMock()
"""
    diagnostics = analyze_source(code, filename="tests/test_handler.py")
    assert any(d.code == "SLOP004" for d in diagnostics)


def test_slop004_production_setattr_clean() -> None:
    code = """
def configure(obj: object, field: str, value: object) -> None:
    setattr(obj, field, value)
"""
    diagnostics = analyze_source(code, filename="src/plugin.py")
    assert not any(d.code == "SLOP004" for d in diagnostics)


def test_slop023_test_setup_bloat_flagged() -> None:
    code = """
def test_evaluation():
    target = CompanyInput(
        a=1,
        b=2,
        c=3,
        d=4,
        e=5,
        f=6,
    )
"""
    diagnostics = analyze_source(code, filename="tests/test_evaluation.py")
    assert any(d.code == "SLOP023" for d in diagnostics)


def test_slop024_tautological_assert_flagged() -> None:
    code = """
def test_eval():
    assert True
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP024" for d in diagnostics)


def test_slop025_assertionless_test_flagged() -> None:
    code = """
def test_eval():
    do_something()
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP025" for d in diagnostics)


def test_slop026_silent_test_except_flagged() -> None:
    code = """
def test_eval():
    try:
        do_something()
    except Exception:
        pass
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP026" for d in diagnostics)


def test_slop027_opaque_test_name_flagged() -> None:
    code = """
def test1():
    assert compute() == 1
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP027" for d in diagnostics)


def test_slop028_test_sleep_flagged() -> None:
    code = """
import time

def test_eval():
    time.sleep(1)
    assert compute() == 1
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP028" for d in diagnostics)


def test_slop029_test_print_flagged() -> None:
    code = """
def test_eval():
    print("hi")
    assert compute() == 1
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP029" for d in diagnostics)


def test_slop030_private_member_test_access_flagged() -> None:
    code = """
def test_eval():
    assert sut._private_state == 1
"""
    diagnostics = analyze_source(code, filename="tests/test_eval.py")
    assert any(d.code == "SLOP030" for d in diagnostics)


