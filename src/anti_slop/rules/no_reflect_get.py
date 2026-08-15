from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name


def is_constant_str_arg(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


class NoReflectGetRule(BaseRule):
    rule_id = "no-reflect-get"
    code = "SLOP007"
    description = "Disallow dynamic reflection and eval; use typed attribute access, boundary parsing, or literal optional access."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Laundering via obj.__dict__[k] or vars(obj)[k]
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__":
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message="Do not launder reflection through `__dict__` subscripting. Use typed attribute access or parse into a domain type.",
                    )
                elif isinstance(node.value, ast.Call) and get_dotted_name(node.value.func) in {"vars", "builtins.vars"}:
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message="Do not launder reflection through `vars()` subscripting. Use typed attribute access or parse into a domain type.",
                    )

            # 2. Calls: eval(), __getattribute__(), or dynamic getattr()/attrgetter()
            elif isinstance(node, ast.Call):
                # Don't double report if it's already caught by no-reflect-apply (getattr(...)(...))
                parent = getattr(node, "parent", None)
                if isinstance(parent, ast.Call) and parent.func is node:
                    continue

                func_name = get_dotted_name(node.func)

                if func_name in {"eval", "builtins.eval", "exec", "builtins.exec"}:
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message=f"Avoid `{func_name}`; dynamic execution bypasses type safety and validation.",
                    )

                elif isinstance(node.func, ast.Attribute) and node.func.attr == "__getattribute__":
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message="Avoid direct calls to `__getattribute__`. Use typed attribute access.",
                    )

                elif func_name in {"getattr", "builtins.getattr"}:
                    # getattr(obj, "literal") and getattr(obj, "literal", default) are legal
                    if len(node.args) >= 2:
                        attr_arg = node.args[1]
                        if not is_constant_str_arg(attr_arg):
                            yield context.make_diagnostic(
                                node=node,
                                code=self.code,
                                rule_id=self.rule_id,
                                message="Dynamic attribute name in `getattr()` bypasses static analysis. Use explicit branching or parse into a domain type.",
                            )
                    else:
                        yield context.make_diagnostic(
                            node=node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message="Invalid `getattr()` call without attribute argument.",
                        )

                elif func_name in {"operator.attrgetter", "attrgetter"}:
                    # attrgetter("literal") is legal; dynamic attrgetter is not
                    if node.args and not all(is_constant_str_arg(arg) for arg in node.args):
                        yield context.make_diagnostic(
                            node=node,
                            code=self.code,
                            rule_id=self.rule_id,
                            message="Dynamic `attrgetter` bypasses static analysis. Use explicit typed properties.",
                        )
