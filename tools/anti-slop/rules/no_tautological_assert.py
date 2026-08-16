from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext


def is_tautological_comparison(node: ast.Compare) -> bool:
    """Check if a comparison is comparing an expression to itself (e.g. x == x, x is x)."""
    if len(node.comparators) != 1:
        return False

    # Check Eq, Is, NotEq, IsNot with identical left and right expressions
    left_dump = ast.dump(node.left)
    right_dump = ast.dump(node.comparators[0])
    return left_dump == right_dump


def is_truthy_literal(node: ast.AST) -> bool:
    """Check if node is a literal that is always truthy."""
    if isinstance(node, ast.Constant):
        return bool(node.value) is True

    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return len(node.elts) > 0

    if isinstance(node, ast.Dict):
        return len(node.keys) > 0

    # bool(True), bool([1, 2]), etc.
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool":
        if node.args and is_truthy_literal(node.args[0]):
            return True

    return False


class NoTautologicalAssertRule(BaseRule):
    rule_id = "no-tautological-assert"
    code = "SLOP024"
    description = "Disallow tautological assertions in tests (e.g. `assert True`, `assert x == x`, literal truthy containers)."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Assert):
                continue

            if is_truthy_literal(node.test):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        "Eliminate tautological assertion on truthy literal. "
                        "Assertions must verify dynamic outputs or use `pytest.fail()` for explicit failure."
                    ),
                )
            elif isinstance(node.test, ast.Compare) and is_tautological_comparison(node.test):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        "Eliminate tautological self-comparison (e.g. `x == x` or `x is x`). "
                        "Assertions must verify dynamic outputs against distinct expected values."
                    ),
                )
