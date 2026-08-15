from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext


def is_empty_dict(node: ast.AST) -> bool:
    """Check if node is an empty dict literal."""
    return isinstance(node, ast.Dict) and len(node.keys) == 0


def is_conditional_empty_dict_spread(node: ast.AST) -> bool:
    """Check if an expression is an inline if-else where either branch is an empty dict."""
    if isinstance(node, ast.IfExp):
        return is_empty_dict(node.body) or is_empty_dict(node.orelse)
    return False


class NoConditionalEmptyDictSpreadRule(BaseRule):
    rule_id = "no-conditional-empty-object-spread"
    code = "SLOP002"
    description = "Disallow dictionary spreads that conditionally spread an empty dictionary to omit fields."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Dict):
                continue

            for key, val in zip(node.keys, node.values):
                # In Python AST, **dict unpacking in dict literals is represented by key is None
                if key is None and is_conditional_empty_dict_spread(val):
                    yield context.make_diagnostic(
                        node=val,
                        code=self.code,
                        rule_id=self.rule_id,
                        message="This conditional spread hides property omission behind an empty dictionary. Build the dictionary in separate statements and add the property only when present.",
                    )
