from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_class

DEFAULT_MAX_PARAMETERS = 4


def is_dataclass_or_model(cls_node: ast.ClassDef | None) -> bool:
    if cls_node is None:
        return False
    # Check decorators like @dataclass
    for dec in cls_node.decorator_list:
        name = getattr(dec, "id", None) or getattr(getattr(dec, "func", None), "id", None)
        if name in {"dataclass", "pydantic_dataclass"}:
            return True
    # Check base classes like BaseModel
    for base in cls_node.bases:
        base_name = getattr(base, "id", None) or getattr(base, "attr", None)
        if base_name in {"BaseModel", "TypedDict", "NamedTuple"}:
            return True
    return False


class NoExcessiveParametersRule(BaseRule):
    rule_id = "no-excessive-parameters"
    code = "SLOP016"
    description = "Disallow function signatures with excessive parameters (>4); prefer a dataclass or options model."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        max_params = context.options.get("max_parameters", DEFAULT_MAX_PARAMETERS)

        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Check if this is an __init__ in a dataclass/Pydantic class
            cls_parent = enclosing_class(node)
            if node.name == "__init__" and is_dataclass_or_model(cls_parent):
                continue

            # Count non-self/cls parameters
            all_args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            count = sum(1 for arg in all_args if arg.arg not in {"self", "cls"})
            if node.args.vararg is not None:
                count += 1
            if node.args.kwarg is not None:
                count += 1

            if count > max_params:
                yield context.make_diagnostic(
                    node=node,
                    code=self.code,
                    rule_id=self.rule_id,
                    message=f"Function `{node.name}` has {count} parameters (max allowed: {max_params}). Refactor parameters into a named dataclass or options model.",
                )
