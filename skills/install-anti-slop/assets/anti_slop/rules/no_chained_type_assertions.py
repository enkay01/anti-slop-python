from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import is_cast_call


class NoChainedTypeAssertionsRule(BaseRule):
    rule_id = "no-chained-type-assertions"
    code = "SLOP001"
    description = "Disallow nested type assertions (chained cast() calls) that discard type evidence."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Call) or not is_cast_call(node):
                continue

            # Only inspect outermost cast calls
            parent = getattr(node, "parent", None)
            if isinstance(parent, ast.Call) and is_cast_call(parent):
                continue

            # Check if any argument or nested expression within the cast contains another cast
            has_inner_cast = False
            for arg in node.args:
                for inner in ast.walk(arg):
                    if isinstance(inner, ast.Call) and is_cast_call(inner):
                        has_inner_cast = True
                        break
                if has_inner_cast:
                    break

            if has_inner_cast:
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message="This assertion chain discards type evidence. Keep the original precise type, or parse untrusted input at its boundary before narrowing it.",
                )
