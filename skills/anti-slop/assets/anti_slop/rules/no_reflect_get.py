from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name

REFLECT_GET_NAMES = {
    "getattr",
    "builtins.getattr",
    "operator.attrgetter",
    "attrgetter",
    "eval",
    "builtins.eval",
}


class NoReflectGetRule(BaseRule):
    rule_id = "no-reflect-get"
    code = "SLOP007"
    description = "Disallow getattr, attrgetter, and eval for attribute access; use typed attribute access or domain parsing."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Call):
                continue

            # Don't double report if it's already caught by no-reflect-apply (getattr(...)(...))
            parent = getattr(node, "parent", None)
            if isinstance(parent, ast.Call) and parent.func is node:
                continue

            func_name = get_dotted_name(node.func)
            if func_name in REFLECT_GET_NAMES:
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=f"Replace `{func_name}` with typed attribute access. Parse dynamic input into a named domain type before reading it.",
                )
