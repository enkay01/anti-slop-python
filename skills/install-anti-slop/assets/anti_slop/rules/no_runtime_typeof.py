from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import (
    is_exact_type_check_expr,
    is_single_statement_exact_type_helper,
)


class NoRuntimeTypeofRule(BaseRule):
    rule_id = "no-runtime-typeof"
    code = "SLOP008"
    description = "Disallow exact runtime type equality (type(x) is / __class__ is) and structural type-laundering helpers; use polymorphic dispatch or boundary validation."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Structural helper function returning exact type comparison: def matches_kind(x): return type(x) is Foo
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_single_statement_exact_type_helper(node):
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=(
                            f"Function `{node.name}` is a structural type-laundering wrapper around an exact type comparison. "
                            "Use structural pattern matching, domain parsing, or polymorphic protocols instead."
                        ),
                    )

            # 2. Exact type comparisons: type(x) is Foo, type(x) == Foo, x.__class__ is Foo
            elif is_exact_type_check_expr(node):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        "Exact type identity check (`type(x) is` or `x.__class__ is`) breaks subtyping and polymorphism. "
                        "Use `isinstance()`, structural pattern matching (`match/case`), or parse at the I/O boundary."
                    ),
                )
