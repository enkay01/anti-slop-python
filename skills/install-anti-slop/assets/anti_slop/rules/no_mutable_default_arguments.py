from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name

MUTABLE_CALL_NAMES = {
    "list",
    "dict",
    "set",
    "bytearray",
    "collections.defaultdict",
    "defaultdict",
    "collections.deque",
    "deque",
}


def is_mutable_expression(node: ast.AST | None) -> str | None:
    if node is None:
        return None

    if isinstance(node, ast.List):
        return "list literal []"
    if isinstance(node, ast.Dict):
        return "dict literal {}"
    if isinstance(node, ast.Set):
        return "set literal {}"
    if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
        return "comprehension"

    if isinstance(node, ast.Call):
        name = get_dotted_name(node.func)
        if name in MUTABLE_CALL_NAMES:
            return f"`{name}()` call"

    return None


class NoMutableDefaultArgumentsRule(BaseRule):
    rule_id = "no-mutable-default-arguments"
    code = "SLOP021"
    description = "Disallow mutable default arguments (lists, dicts, sets, mutable calls) in function signatures."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # 1. Positional defaults
            positional_args = node.args.posonlyargs + node.args.args
            defaults = node.args.defaults
            default_start_idx = len(positional_args) - len(defaults)

            for idx, arg in enumerate(positional_args):
                if idx >= default_start_idx:
                    default_node = defaults[idx - default_start_idx]
                    mutable_kind = is_mutable_expression(default_node)
                    if mutable_kind is not None:
                        yield context.make_diagnostic(
                            node=default_node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Parameter `{arg.arg}` on `{node.name}` has a mutable default ({mutable_kind}). Default argument expressions are evaluated once at definition time; use `None` as default or an immutable type instead.",
                        )

            # 2. Keyword-only defaults
            for arg, default_node in zip(node.args.kwonlyargs, node.args.kw_defaults):
                if default_node is not None:
                    mutable_kind = is_mutable_expression(default_node)
                    if mutable_kind is not None:
                        yield context.make_diagnostic(
                            node=default_node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Keyword-only parameter `{arg.arg}` on `{node.name}` has a mutable default ({mutable_kind}). Use `None` as default or an immutable type instead.",
                        )
