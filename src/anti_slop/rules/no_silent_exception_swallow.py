from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name


def is_empty_or_pass_body(body: list[ast.stmt]) -> bool:
    if not body:
        return True
    if len(body) == 1:
        stmt = body[0]
        if isinstance(stmt, ast.Pass):
            return True
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            # Just a string/docstring or None/constant
            return True
        if isinstance(stmt, ast.Assign):
            # Dummy assignments like `_ = None` or `_ = 1`
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id in {"_", "dummy", "unused"}:
                return True
    return False


class NoSilentExceptionSwallowRule(BaseRule):
    rule_id = "no-silent-exception-swallow"
    code = "SLOP018"
    description = "Disallow silent exception swallowing (except ...: pass) and unchained exception re-raises."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            exc_name = get_annotation_name(node.type) if node.type else "Exception"

            # 1. Silent pass/swallow
            if is_empty_or_pass_body(node.body):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=f"Except block for `{exc_name}` silently swallows exceptions without handling or logging. Handle it explicitly, log with logger.exception(), or use contextlib.suppress().",
                )

            # 2. Re-raising a new exception without 'from err' / 'from None'
            for stmt in node.body:
                if isinstance(stmt, ast.Raise) and stmt.exc is not None and stmt.cause is None:
                    # If raising the caught exception itself `raise` or `raise err`, that's fine
                    if isinstance(stmt.exc, ast.Name) and node.name and stmt.exc.id == node.name:
                        continue
                    if isinstance(stmt.exc, ast.Call):
                        yield context.make_diagnostic(
                            node=stmt,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Raising a new exception inside an except block without `from {node.name or 'err'}` erases the original stack trace. Chain exceptions explicitly.",
                        )
