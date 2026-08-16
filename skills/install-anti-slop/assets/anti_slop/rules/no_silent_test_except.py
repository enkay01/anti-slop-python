from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_class, is_test_file


def is_test_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if node is a test function or method."""
    if node.name.startswith("test"):
        return True

    parent_cls = enclosing_class(node)
    if parent_cls and parent_cls.name.startswith("Test"):
        return True

    return False


def handler_reraises(handler: ast.ExceptHandler) -> bool:
    """Check if an except handler explicitly re-raises an exception."""
    for child in ast.walk(handler):
        if isinstance(child, ast.Raise):
            return True
    return False


class NoSilentTestExceptRule(BaseRule):
    rule_id = "no-silent-test-except"
    code = "SLOP026"
    description = "Disallow try...except blocks in test functions that catch or swallow exceptions without pytest.raises."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            if not is_test_function(node):
                continue

            for child in ast.walk(node):
                if isinstance(child, ast.Try):
                    for handler in child.handlers:
                        if not handler_reraises(handler):
                            yield context.make_diagnostic(
                                node=handler,
                                code=self.code,
                                rule_id=self.rule_id,
                                message=(
                                    f"Replace `try...except` in test `{node.name}` with `with pytest.raises(...)` "
                                    "or let unexpected exceptions fail naturally to preserve full tracebacks."
                                ),
                            )
