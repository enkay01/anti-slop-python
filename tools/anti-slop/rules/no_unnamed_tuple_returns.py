from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name


def is_heterogeneous_tuple_annotation(returns_node: ast.AST | None) -> bool:
    if returns_node is None or not isinstance(returns_node, ast.Subscript):
        return False

    val_name = get_annotation_name(returns_node.value)
    if val_name not in {"tuple", "typing.Tuple", "Tuple"}:
        return False

    # Check slice
    if isinstance(returns_node.slice, ast.Tuple) and len(returns_node.slice.elts) >= 2:
        # Check if it's homogeneous tuple[T, ...]
        if len(returns_node.slice.elts) == 2 and isinstance(returns_node.slice.elts[1], ast.Constant) and returns_node.slice.elts[1].value is Ellipsis:
            return False
        return True

    return False


class NoUnnamedTupleReturnsRule(BaseRule):
    rule_id = "no-unnamed-tuple-returns"
    code = "SLOP019"
    description = "Disallow multi-value heterogeneous tuple return types; prefer named dataclasses or NamedTuples."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Exclude standard protocol dunder methods like __divmod__
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            if node.name in {"items", "keys", "values"}:
                continue

            if is_heterogeneous_tuple_annotation(node.returns):
                yield context.make_diagnostic(
                    node=node.returns,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=f"Function `{node.name}` returns an unnamed multi-value tuple. Model returned values as a named `@dataclass(frozen=True)` or `NamedTuple`.",
                )
