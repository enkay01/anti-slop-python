from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import is_cast_call
from anti_slop.shared.dictionary_types import classify_unsafe_dict_annotation, is_known_evidence_value


class NoWidenThenAssertRule(BaseRule):
    rule_id = "no-widen-then-assert"
    code = "SLOP014"
    description = "Disallow local variable flows that widen known values to broad types and later assert them back."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        # Track widened variables in each scope: var_name -> node
        widened_vars: dict[str, ast.AST] = {}

        for node in ast.walk(context.tree):
            # Check variable initialization with explicit broad type from known value
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                # Is annotation broad?
                ann_str = getattr(node.annotation, "id", None) or getattr(node.annotation, "attr", None) or ""
                is_broad = ann_str in {"Any", "object"} or classify_unsafe_dict_annotation(node.annotation, context.aliases) is not None
                if is_broad and is_known_evidence_value(node.value):
                    widened_vars[node.target.id] = node

            # Also check `x: Any = y` where y was a known typed var or call
            elif isinstance(node, ast.Call) and is_cast_call(node):
                # cast(TargetType, var_name)
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Name):
                    var_name = node.args[1].id
                    if var_name in widened_vars:
                        yield context.make_diagnostic(
                            node=node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Binding `{var_name}` discards type evidence and later recreates it with `cast()`. Keep the precise type from initialization through use; parse boundary input once.",
                        )
