from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import is_test_file


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
    description = "Disallow assert statements in production code; assert is stripped under python -O."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Assert):
                continue

            if is_in_type_checking_block(node):
                continue

            yield context.make_diagnostic(
                node=node,
                code=self.code,
                rule_id=self.rule_id,
                message="Avoid `assert` in production logic; assert statements are stripped under `python -O`. Raise an explicit ValueError/TypeError or use an explicit condition.",
            )
