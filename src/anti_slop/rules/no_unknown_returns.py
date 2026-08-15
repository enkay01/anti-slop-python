from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name


def resolves_to_unknown_return(
    annotation: ast.AST | None,
    aliases: dict[str, ast.AST] | None = None,
) -> bool:
    if annotation is None:
        return False
    name = get_annotation_name(annotation)
    if name in {"Any", "typing.Any"}:
        return True

    # Check Coroutine / Awaitable with Any return
    if isinstance(annotation, ast.Subscript):
        val_name = get_annotation_name(annotation.value)
        if val_name in {"Awaitable", "typing.Awaitable", "Future", "asyncio.Future"}:
            return resolves_to_unknown_return(annotation.slice, aliases)
        if val_name in {"Coroutine", "typing.Coroutine"}:
            if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) >= 3:
                return resolves_to_unknown_return(annotation.slice.elts[2], aliases)

    if aliases and isinstance(annotation, ast.Name) and annotation.id in aliases:
        target = aliases[annotation.id]
        if target is not annotation:
            return resolves_to_unknown_return(target, {k: v for k, v in aliases.items() if k != annotation.id})

    return False


class NoUnknownReturnsRule(BaseRule):
    rule_id = "no-unknown-returns"
    code = "SLOP011"
    description = "Disallow functions whose explicit return contract is Any or Awaitable[Any]."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            if node.returns is not None and resolves_to_unknown_return(node.returns, context.aliases):
                yield context.make_diagnostic(
                    node=node.returns,
                    code=self.code,
                    rule_id=self.rule_id,
                    message="This function exposes `Any` to its caller. Parse the value at its boundary and return a named domain type.",
                )
