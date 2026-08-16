from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name, is_test_file

SLEEP_FUNCTIONS = {
    "time.sleep",
    "asyncio.sleep",
    "gevent.sleep",
    "eventlet.sleep",
    "sleep",
}


def is_sleep_call(node: ast.Call) -> bool:
    """Check if node is a call to a sleep function."""
    name = get_dotted_name(node.func)
    if name in SLEEP_FUNCTIONS:
        return True

    if isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
        return True

    return False


class NoTestSleepRule(BaseRule):
    rule_id = "no-test-sleep"
    code = "SLOP028"
    description = "Disallow time.sleep and asyncio.sleep in test files (Slow Poke anti-pattern)."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        if not is_test_file(context.filename):
            return

        for node in ast.walk(context.tree):
            if isinstance(node, ast.Call) and is_sleep_call(node):
                name = get_dotted_name(node.func) or "sleep"
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=(
                        f"Avoid `{name}` in tests. Use polling loops, event synchronization, "
                        "or clock-freezing fixtures instead of wall-clock delays."
                    ),
                )
