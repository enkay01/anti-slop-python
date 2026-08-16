from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import is_test_file

EXEMPT_RECEIVERS = {"self", "cls", "pytest", "sys"}


def is_dunder(name: str) -> bool:
    """Check if name is a dunder attribute like __name__ or __doc__."""
    return name.startswith("__") and name.endswith("__")


def is_private_member_access(node: ast.Attribute) -> bool:
    """Check if node accesses a single-underscore private member on an external object."""
    attr = node.attr
    if not attr.startswith("_") or is_dunder(attr):
        return False

    # Allow test classes to access their own private helpers (self._helper / cls._setup)
    if isinstance(node.value, ast.Name) and node.value.id in EXEMPT_RECEIVERS:
        return False

    return True


class NoPrivateMemberTestAccessRule(BaseRule):
    rule_id = "no-private-member-test-access"
    code = "SLOP030"
    description = "Disallow direct access to private members (_attr or _method) in test files (Anal Probe anti-pattern)."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if isinstance(node, ast.Attribute) and is_private_member_access(node):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"Direct access to private member `{node.attr}` violates encapsulation. "
                        "Test observable behavior through public contracts or protocol interfaces."
                    ),
                )
