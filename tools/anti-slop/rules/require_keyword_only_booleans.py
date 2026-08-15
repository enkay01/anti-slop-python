from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name


def is_boolean_annotation(annotation: ast.AST | None) -> bool:
    if annotation is None:
        return False
    name = get_annotation_name(annotation)
    if name in {"bool", "builtins.bool", "bool | None", "Optional[bool]"}:
        return True
    return False


def is_boolean_default(default_node: ast.AST | None) -> bool:
    if default_node is None:
        return False
    if isinstance(default_node, ast.Constant) and isinstance(default_node.value, bool):
        return True
    return False


class RequireKeywordOnlyBooleansRule(BaseRule):
    rule_id = "require-keyword-only-booleans"
    code = "SLOP017"
    description = "Require boolean parameters to be keyword-only (*, flag=True) to eliminate the boolean trap."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Skip dunder methods like __eq__, __contains__, etc.
            if node.name.startswith("__") and node.name.endswith("__"):
                continue

            positional_args = node.args.posonlyargs + node.args.args
            # Calculate defaults mapping for positional args
            # defaults list corresponds to the LAST n positional args
            num_pos = len(positional_args)
            defaults = node.args.defaults
            num_defaults = len(defaults)
            default_start_idx = num_pos - num_defaults

            for idx, arg in enumerate(positional_args):
                if arg.arg in {"self", "cls"}:
                    continue

                default_node = defaults[idx - default_start_idx] if idx >= default_start_idx else None
                is_bool = is_boolean_annotation(arg.annotation) or is_boolean_default(default_node)

                if is_bool:
                    yield context.make_diagnostic(
                        node=arg,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Boolean parameter `{arg.arg}` on function `{node.name}` must be keyword-only (use `*, {arg.arg}: bool = ...`) to prevent the boolean trap.",
                    )
