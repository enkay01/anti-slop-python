from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name


def resolves_to_object(annotation: ast.AST | None, aliases: dict[str, ast.AST] | None = None) -> bool:
    if annotation is None:
        return False
    name = get_annotation_name(annotation)
    if name in {"object", "builtins.object"}:
        return True
    if aliases and isinstance(annotation, ast.Name) and annotation.id in aliases:
        target = aliases[annotation.id]
        if target is not annotation:
            return resolves_to_object(target, {k: v for k, v in aliases.items() if k != annotation.id})
    return False


class NoObjectParametersRule(BaseRule):
    rule_id = "no-object-parameters"
    code = "SLOP005"
    description = "Disallow object function parameters; inputs must use an owner-provided type and be parsed at their boundary."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Check posonlyargs, args, kwonlyargs
            all_args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            for arg in all_args:
                # Skip 'self' or 'cls'
                if arg.arg in {"self", "cls"}:
                    continue
                if arg.annotation is not None and resolves_to_object(arg.annotation, context.aliases):
                    yield context.make_diagnostic(
                        node=arg.annotation,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Parameter `{arg.arg}` uses the broad `object` type. Accept a named owner type; parse external input at its boundary before calling this function.",
                    )
