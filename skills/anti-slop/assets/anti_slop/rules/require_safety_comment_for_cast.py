from __future__ import annotations

import ast
import fnmatch
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import is_cast_call


def is_boundary_module(filename: str, boundary_patterns: list[str]) -> bool:
    if not boundary_patterns:
        return False
    clean = filename.replace("\\", "/")
    for pattern in boundary_patterns:
        clean_pat = pattern.rstrip("/")
        if fnmatch.fnmatch(clean, clean_pat) or fnmatch.fnmatch(clean, pattern):
            return True
        if "**" in pattern:
            prefix = pattern.split("/**")[0]
            if clean.startswith(prefix + "/") or clean == prefix:
                return True
    return False


class RequireSafetyCommentForCastRule(BaseRule):
    rule_id = "require-safety-comment-for-type-assertion"
    code = "SLOP015"
    description = "Disallow typing.cast() outside configured boundary modules; construct domain types or use runtime parsers."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        boundary_modules = context.options.get("boundary_modules", [])
        if is_boundary_module(context.filename, boundary_modules):
            return

        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Call) or not is_cast_call(node):
                continue

            yield context.make_diagnostic(
                node=node,
                code=self.code,
                rule_id=self.rule_id,
                message=(
                    "Avoid `typing.cast()`; cast fabricates type evidence without runtime validation. "
                    "Construct domain types directly, parse at the boundary, or configure explicit `boundary_modules`."
                ),
            )
