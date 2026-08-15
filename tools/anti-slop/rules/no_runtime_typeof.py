from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_function, get_dotted_name, is_typeguard_function


class NoRuntimeTypeofRule(BaseRule):
    rule_id = "no-runtime-typeof"
    code = "SLOP008"
    description = "Disallow ad-hoc runtime type checks (type(x) is / isinstance); decode external values at their boundary."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        allow_in_type_guards = context.options.get("allow_in_type_guards", False)

        for node in ast.walk(context.tree):
            is_type_check = False

            # 1. `type(x) is str` or `type(x) == int`
            if isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Call):
                    name = get_dotted_name(node.left.func)
                    if name in {"type", "builtins.type"}:
                        is_type_check = True

            # 2. `isinstance(x, ...)` or `issubclass(...)`
            elif isinstance(node, ast.Call):
                name = get_dotted_name(node.func)
                if name in {"isinstance", "builtins.isinstance", "issubclass", "builtins.issubclass"}:
                    is_type_check = True

            if is_type_check:
                if allow_in_type_guards:
                    func = enclosing_function(node)
                    if func is not None and is_typeguard_function(func):
                        continue

                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message="A runtime type check narrows a representation without establishing its contract. Parse input at its I/O boundary, then branch on the domain value.",
                )
