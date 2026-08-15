from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.comments import has_safety_comment_for_node


def is_test_file(filename: str) -> bool:
    clean = filename.replace("\\", "/")
    if "test_" in clean or "_test.py" in clean or "/tests/" in clean or "conftest.py" in clean:
        return True
    return False


def is_in_type_checking_block(node: ast.AST) -> bool:
    current = getattr(node, "parent", None)
    while current is not None:
        if isinstance(current, ast.If):
            test_repr = getattr(current.test, "id", None) or getattr(current.test, "attr", None)
            if test_repr == "TYPE_CHECKING":
                return True
        current = getattr(current, "parent", None)
    return False


class NoAssertValidationRule(BaseRule):
    rule_id = "no-assert-validation"
    code = "SLOP020"
    description = "Disallow assert statements for input validation in business logic; assert is erased under python -O."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Assert):
                continue

            if is_in_type_checking_block(node):
                continue

            lineno = getattr(node, "lineno", 1)
            if has_safety_comment_for_node(context.comments, lineno, lookback_lines=2):
                continue

            yield context.make_diagnostic(
                node=node,
                code=self.code,
                rule_id=self.rule_id,
                message="Avoid `assert` for runtime validation; assert statements are stripped in production under `python -O`. Raise an explicit ValueError/TypeError instead.",
            )
