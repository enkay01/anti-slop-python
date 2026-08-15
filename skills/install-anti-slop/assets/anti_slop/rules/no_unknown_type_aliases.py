from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_annotation_name


def resolves_to_top_type(node: ast.AST | None, aliases: dict[str, ast.AST] | None = None) -> bool:
    if node is None:
        return False
    name = get_annotation_name(node)
    if name in {"Any", "typing.Any", "object", "builtins.object"}:
        return True
    if aliases and isinstance(node, ast.Name) and node.id in aliases:
        target = aliases[node.id]
        if target is not node:
            return resolves_to_top_type(target, {k: v for k, v in aliases.items() if k != node.id})
    return False


class NoUnknownTypeAliasesRule(BaseRule):
    rule_id = "no-unknown-type-aliases"
    code = "SLOP012"
    description = "Disallow type aliases whose resolved type is Any or object; types must remain explicit or domain-specific."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Python 3.12+ `type ExternalValue = Any`
            if hasattr(ast, "TypeAlias") and isinstance(node, getattr(ast, "TypeAlias")):
                alias_name = getattr(node.name, "id", None) if isinstance(getattr(node, "name", None), ast.Name) else str(getattr(node, "name", ""))
                alias_value = getattr(node, "value", None)
                if resolves_to_top_type(alias_value, context.aliases):
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Type alias `{alias_name}` hides `Any` or `object`. Keep `Any` explicit at the parsing boundary; otherwise use the parsed owner type.",
                    )

            # 2. `ExternalValue: TypeAlias = Any`
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                ann_name = get_annotation_name(node.annotation)
                if ann_name in {"TypeAlias", "typing.TypeAlias", "typing_extensions.TypeAlias"}:
                    if resolves_to_top_type(node.value, context.aliases):
                        yield context.make_diagnostic(
                            node=node.target,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Type alias `{node.target.id}` hides `Any` or `object`. Keep `Any` explicit at the parsing boundary; otherwise use the parsed owner type.",
                        )

            # 3. Simple top-level assignment: `ExternalValue = Any`
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                # Only check module-level or class-level assignments with capitalized name
                target_name = node.targets[0].id
                if target_name[0].isupper() and resolves_to_top_type(node.value, context.aliases):
                    yield context.make_diagnostic(
                        node=node.targets[0],
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Type alias `{target_name}` hides `Any` or `object`. Keep `Any` explicit at the parsing boundary; otherwise use the parsed owner type.",
                    )
