from __future__ import annotations

from anti_slop.config import AntiSlopConfig
from anti_slop.engine import analyze_source
from anti_slop.rules.require_safety_comment_for_cast import RequireSafetyCommentForCastRule
from tests.conftest import check_code


def test_cast_flagged_by_default():
    code = """
from typing import cast

user = cast(User, raw_value)
"""
    diags = check_code(code, RequireSafetyCommentForCastRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP015"
    assert diags[0].rule_id == "require-safety-comment-for-type-assertion"


def test_cast_flagged_despite_comment():
    code = """
from typing import cast

# SAFETY: parse_user validated the identifier before branding it
user = cast(User, raw_value)
"""
    diags = check_code(code, RequireSafetyCommentForCastRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP015"


def test_cast_in_boundary_module_allowed():
    code = """
from typing import cast

user = cast(User, raw_value)
"""
    config = AntiSlopConfig(
        rules={"require-safety-comment-for-type-assertion": {"options": {"boundary_modules": ["src/adapters/**"]}}}
    )
    diags = analyze_source(
        code,
        filename="src/adapters/user_parser.py",
        config=config,
        rules=[RequireSafetyCommentForCastRule],
    )
    assert len(diags) == 0
