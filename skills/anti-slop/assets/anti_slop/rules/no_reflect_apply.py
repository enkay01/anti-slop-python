from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name


class NoReflectApplyRule(BaseRule):
    rule_id = "no-reflect-apply"
    code = "SLOP006"
    description = "Disallow reflective method dispatch and operator.methodcaller; call typed functions or methods directly."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Call):
                continue

            # 1. Direct call on getattr: getattr(obj, "method")(args...) or getattr(obj, dynamic)(args...)
            if isinstance(node.func, ast.Call):
                inner_func_name = get_dotted_name(node.func.func)
                if inner_func_name in {"getattr", "builtins.getattr"}:
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message="Replace reflective function dispatch with a typed function or method call. Model dynamic dispatch behind a named Protocol or interface.",
                    )

            # 2. operator.methodcaller(...)
            func_name = get_dotted_name(node.func)
            if func_name in {"operator.methodcaller", "methodcaller"}:
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message="Replace reflective function dispatch with a typed function or method call. Model dynamic dispatch behind a named Protocol or interface.",
                )
