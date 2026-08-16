from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name, is_test_file

PRINT_FUNCTIONS = {
    "print",
    "builtins.print",
    "sys.stdout.write",
    "sys.stderr.write",
    "stdout.write",
    "stderr.write",
}


def is_print_call(node: ast.Call) -> bool:
    """Check if node is a call to print or stdout/stderr write."""
    name = get_dotted_name(node.func)
    return name in PRINT_FUNCTIONS


class NoTestPrintRule(BaseRule):
    rule_id = "no-test-print"
    code = "SLOP029"
    description = "Disallow print statements and raw stdout/stderr writes in test files (Loudmouth anti-pattern)."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if isinstance(node, ast.Call) and is_print_call(node):
                name = get_dotted_name(node.func) or "print"
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"Avoid `{name}` in test files. Remove debug chatter or use pytest's "
                        "`capsys` / `caplog` fixtures to assert output."
                    ),
                )
