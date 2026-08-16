from __future__ import annotations

import ast
import re
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_class, is_test_file

OPAQUE_NAME_PATTERNS = [
    re.compile(r"^test_?[0-9]+$", re.IGNORECASE),
    re.compile(r"^test_case_?[0-9]+$", re.IGNORECASE),
    re.compile(r"^test_[a-zA-Z]$"),
    re.compile(
        r"^test_(works|it|all|func|function|method|run|test|success|failure|pass|basic|simple|ok)$",
        re.IGNORECASE,
    ),
]


def is_test_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if node is a test function or method."""
    if node.name.startswith("test"):
        return True

    parent_cls = enclosing_class(node)
    if parent_cls and parent_cls.name.startswith("Test"):
        return True

    return False


def is_opaque_test_name(name: str) -> bool:
    """Check if test function name matches non-descriptive enumerations or generic placeholders."""
    for pattern in OPAQUE_NAME_PATTERNS:
        if pattern.match(name):
            return True
    return False


class NoOpaqueTestNamesRule(BaseRule):
    rule_id = "no-opaque-test-names"
    code = "SLOP027"
    description = "Disallow opaque, enumerated, or non-descriptive test names (e.g. `test1`, `test_case_1`, `test_works`)."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            if not is_test_function(node):
                continue

            if is_opaque_test_name(node.name):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"Test name `{node.name}` is non-descriptive. "
                        "Use semantic names describing the scenario and expected outcome (e.g. `test_rejects_expired_session_token`)."
                    ),
                )
