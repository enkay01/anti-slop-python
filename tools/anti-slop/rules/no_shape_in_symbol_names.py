from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext

FORBIDDEN_NAME = "shape"


def contains_forbidden_name(name: str) -> bool:
    return FORBIDDEN_NAME in name.lower()


class NoShapeInSymbolNamesRule(BaseRule):
    rule_id = "no-shape-in-symbol-names"
    code = "SLOP009"
    description = "Disallow the case-insensitive substring 'shape' in Python symbol names."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Functions and async functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if contains_forbidden_name(node.name):
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Rename symbol '{node.name}' for its domain role; 'shape' describes structure rather than ownership.",
                    )
                # Check parameter names
                for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                    if contains_forbidden_name(arg.arg):
                        yield context.make_diagnostic(
                            node=arg,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Rename symbol '{arg.arg}' for its domain role; 'shape' describes structure rather than ownership.",
                        )

            # 2. Classes
            elif isinstance(node, ast.ClassDef):
                if contains_forbidden_name(node.name):
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Rename symbol '{node.name}' for its domain role; 'shape' describes structure rather than ownership.",
                    )

            # 3. Variable assignments: `user_shape = ...` or `user_shape: User = ...`
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and contains_forbidden_name(target.id):
                        yield context.make_diagnostic(
                            node=target,
                            code=self.code,
                            rule_id=self.rule_id,
                            message=f"Rename symbol '{target.id}' for its domain role; 'shape' describes structure rather than ownership.",
                        )
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and contains_forbidden_name(node.target.id):
                    yield context.make_diagnostic(
                        node=node.target,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Rename symbol '{node.target.id}' for its domain role; 'shape' describes structure rather than ownership.",
                    )

            # 4. Python 3.12+ `type UserShape = ...`
            elif hasattr(ast, "TypeAlias") and isinstance(node, getattr(ast, "TypeAlias")):
                name = getattr(node.name, "id", None) if isinstance(getattr(node, "name", None), ast.Name) else str(getattr(node, "name", ""))
                if name and contains_forbidden_name(name):
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Rename symbol '{name}' for its domain role; 'shape' describes structure rather than ownership.",
                    )
