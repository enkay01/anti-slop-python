from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_function, get_dotted_name, is_typeguard_function

LAUNDERED_TYPE_CHECK_NAMES = {
    "is_exact_type",
    "check_type",
    "assert_type",
    "verify_type",
    "is_type_match",
    "validate_type",
}


class NoRuntimeTypeofRule(BaseRule):
    rule_id = "no-runtime-typeof"
    code = "SLOP008"
    description = "Disallow ad-hoc runtime type checks (type(x) is / isinstance) or laundering helpers; decode external values at their boundary."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        allow_in_type_guards = context.options.get("allow_in_type_guards", False)

        for node in ast.walk(context.tree):
            is_type_check = False
            message_detail = ""

            # 1. `type(x) is str` or `type(x) == int`
            if isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Call):
                    name = get_dotted_name(node.left.func)
                    if name in {"type", "builtins.type"}:
                        is_type_check = True
                        message_detail = "Direct `type()` check"

            # 2. `isinstance(x, ...)` or `issubclass(...)`
            elif isinstance(node, ast.Call):
                name = get_dotted_name(node.func)
                if name in {"isinstance", "builtins.isinstance", "issubclass", "builtins.issubclass"}:
                    is_type_check = True
                    message_detail = f"`{name}()` check"
                elif name in LAUNDERED_TYPE_CHECK_NAMES:
                    is_type_check = True
                    message_detail = f"Abstracted type-check helper `{name}()`"

            # 3. Helper functions defined to launder type checks: def is_exact_type(...)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in LAUNDERED_TYPE_CHECK_NAMES:
                    is_type_check = True
                    message_detail = f"Type-laundering helper function `{node.name}`"

            if is_type_check:
                if allow_in_type_guards:
                    func = enclosing_function(node)
                    if func is not None and is_typeguard_function(func):
                        continue

                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"{message_detail} narrows a representation without establishing its contract. "
                        "Do not launder types through helper functions; parse input at the I/O boundary into validated domain types."
                    ),
                )
