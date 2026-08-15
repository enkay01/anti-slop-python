from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name, is_public_function


def resolves_to_any(annotation: ast.AST | None, aliases: dict[str, ast.AST] | None = None) -> bool:
    if annotation is None:
        return False
    name = get_annotation_name(annotation)
    if name in {"Any", "typing.Any"}:
        return True
    if aliases and isinstance(annotation, ast.Name) and annotation.id in aliases:
        target = aliases[annotation.id]
        if target is not annotation:
            return resolves_to_any(target, {k: v for k, v in aliases.items() if k != annotation.id})
    return False


class NoUnknownParametersRule(BaseRule):
    rule_id = "no-unknown-parameters"
    code = "SLOP010"
    description = "Disallow Any or unannotated parameters on public functions; decode input into explicit domain types at boundaries."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            is_public = is_public_function(node, context.filename)
            all_args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs

            for arg in all_args:
                if arg.arg in {"self", "cls", "cause", "__cause__"}:
                    continue

                if arg.annotation is None:
                    if is_public:
                        yield context.make_diagnostic(
                            node=arg,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Public parameter `{arg.arg}` has no type annotation. Provide an explicit domain contract rather than leaving inputs untyped.",
                        )
                elif resolves_to_any(arg.annotation, context.aliases):
                    yield context.make_diagnostic(
                        node=arg.annotation,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Parameter `{arg.arg}` leaves input unparsed with `Any`. Accept a named domain type; run the expected schema or parser at the I/O boundary before calling this function.",
                    )
