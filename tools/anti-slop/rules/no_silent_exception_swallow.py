from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name, get_dotted_name


def handler_uses_exception_or_controls_flow(node: ast.ExceptHandler) -> bool:
    """Check if the handler's body raises, returns/breaks/continues, logs with exc_info, or passes the caught exception."""
    exc_var = node.name
    for sub in ast.walk(node):
        # 1. Any Raise statement inside the handler
        if isinstance(sub, ast.Raise):
            return True

        # 2. Any flow control: Return, Break, Continue
        if isinstance(sub, (ast.Return, ast.Break, ast.Continue)):
            return True

        # 3. Call to logger.exception or logging with exc_info
        if isinstance(sub, ast.Call):
            call_name = get_dotted_name(sub.func)
            if call_name and "exception" in call_name.lower():
                return True
            for kw in sub.keywords:
                if kw.arg == "exc_info" and not (isinstance(kw.value, ast.Constant) and kw.value.value is False):
                    return True

        # 4. Meaningful reference to the caught exception variable (e.g. handle_error(err))
        if exc_var and isinstance(sub, ast.Name) and sub.id == exc_var:
            parent = getattr(sub, "parent", None)
            if parent is not node:
                return True

    return False


class NoSilentExceptionSwallowRule(BaseRule):
    rule_id = "no-silent-exception-swallow"
    code = "SLOP018"
    description = "Disallow silent exception swallowing and unchained re-raises; handle explicitly or use contextlib.suppress."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            exc_name = get_annotation_name(node.type) if node.type else "Exception"

            # 1. Structural swallow detection: no raise, no flow control, no error logging
            if not handler_uses_exception_or_controls_flow(node):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"Except block for `{exc_name}` silently swallows exceptions without flow control or error logging. "
                        "Handle the error explicitly, return/raise, log with `logger.exception()`, or use `contextlib.suppress()`."
                    ),
                )

            # 2. Re-raising a new exception without 'from err' / 'from None'
            for stmt in node.body:
                if isinstance(stmt, ast.Raise) and stmt.exc is not None and stmt.cause is None:
                    # If re-raising the caught exception itself (`raise` or `raise err`), that's fine
                    if isinstance(stmt.exc, ast.Name) and node.name and stmt.exc.id == node.name:
                        continue
                    if isinstance(stmt.exc, ast.Call):
                        yield context.make_diagnostic(
                            node=stmt,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Raising a new exception inside an except block without `from {node.name or 'err'}` erases the original stack trace. Chain exceptions explicitly.",
                        )
