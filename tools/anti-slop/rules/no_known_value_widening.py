from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import enclosing_function, get_annotation_name
from anti_slop.shared.dictionary_types import classify_unsafe_dict_annotation, is_known_evidence_value


def is_broad_target_annotation(
    annotation: ast.AST | None,
    aliases: dict[str, ast.AST] | None = None,
) -> str | None:
    """Check if an annotation is explicitly broad (Any, object, or an open dictionary like dict[str, Any])."""
    if annotation is None:
        return None

    name = get_annotation_name(annotation)
    if name in {"Any", "typing.Any"}:
        return "Any"
    if name in {"object", "builtins.object"}:
        return "object"

    unsafe_dict = classify_unsafe_dict_annotation(annotation, aliases)
    if unsafe_dict is not None:
        return f"{unsafe_dict.container}[..., {unsafe_dict.unsafe_value}]"

    return None


class NoKnownValueWideningRule(BaseRule):
    rule_id = "no-known-value-widening"
    code = "SLOP003"
    description = "Disallow syntactically established values from flowing into explicitly broad target types that discard useful evidence."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Variable annotation: `x: dict[str, Any] = {"start": handler}` or `x: Any = 123`
            if isinstance(node, ast.AnnAssign) and node.value is not None:
                broad_kind = is_broad_target_annotation(node.annotation, context.aliases)
                if broad_kind is not None:
                    # Allow empty dict/list accumulators
                    if isinstance(node.value, ast.Dict) and len(node.value.keys) == 0:
                        continue
                    if isinstance(node.value, ast.List) and len(node.value.elts) == 0:
                        continue
                    if is_known_evidence_value(node.value):
                        target_name = get_annotation_name(node.target) or "variable"
                        yield context.make_diagnostic(
                            node=node.value,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"The explicit {broad_kind} type on binding `{target_name}` discards known type evidence. Keep inference or use a named TypedDict/dataclass contract.",
                        )

            # 2. Return statements in functions with explicit broad return annotations
            elif isinstance(node, ast.Return) and node.value is not None:
                func = enclosing_function(node)
                if func is not None and func.returns is not None:
                    broad_kind = is_broad_target_annotation(func.returns, context.aliases)
                    if broad_kind is not None:
                        if isinstance(node.value, ast.Dict) and len(node.value.keys) == 0:
                            continue
                        if is_known_evidence_value(node.value):
                            yield context.make_diagnostic(
                                node=node.value,
                                code=self.code,
                                rule_id=self.rule_id,
                                message=f"The explicit {broad_kind} return type on `{func.name}` discards known type evidence. Return a named domain type or TypedDict.",
                            )
