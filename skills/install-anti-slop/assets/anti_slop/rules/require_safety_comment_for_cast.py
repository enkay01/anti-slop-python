from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import is_cast_call
from anti_slop.shared.comments import has_safety_comment_for_node


class RequireSafetyCommentForCastRule(BaseRule):
    rule_id = "require-safety-comment-for-type-assertion"
    code = "SLOP015"
    description = "Require a nearby # SAFETY: comment for every typing.cast() assertion."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Call) or not is_cast_call(node):
                continue

            lineno = getattr(node, "lineno", 1)
            if not has_safety_comment_for_node(context.comments, lineno, lookback_lines=2):
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message="This type cast has no `# SAFETY:` justification. State the checked invariant immediately before the cast or its containing statement.",
                )
