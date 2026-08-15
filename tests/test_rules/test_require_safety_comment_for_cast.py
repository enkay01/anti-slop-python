from __future__ import annotations

from anti_slop.rules.require_safety_comment_for_cast import RequireSafetyCommentForCastRule
from tests.conftest import check_code


def test_cast_without_safety_comment_flagged():
    code = """
from typing import cast

user = cast(User, raw_value)
"""
    diags = check_code(code, RequireSafetyCommentForCastRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP015"
    assert diags[0].rule_id == "require-safety-comment-for-type-assertion"


def test_cast_with_boilerplate_safety_comment_flagged():
    code = """
from typing import cast

# SAFETY: cast
user = cast(User, raw_value)
"""
    diags = check_code(code, RequireSafetyCommentForCastRule)
    assert len(diags) == 1
    assert diags[0].code == "SLOP015"


def test_cast_with_substantive_safety_comment_allowed():
    code = """
from typing import cast

# SAFETY: parse_user validated the identifier before branding it
user = cast(User, raw_value)
"""
    diags = check_code(code, RequireSafetyCommentForCastRule)
    assert len(diags) == 0
