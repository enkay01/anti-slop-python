from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name

MOCK_TARGETS = {
    "unittest.mock.patch",
    "mock.patch",
    "patch",
    "patch.object",
    "unittest.mock.patch.object",
    "mock.patch.object",
    "mocker.patch",
    "mocker.patch.object",
    "monkeypatch.setattr",
}


class NoModuleMockingRule(BaseRule):
    rule_id = "no-module-mocking"
    code = "SLOP004"
    description = "Disallow module mocking and monkeypatching; tests must replace dependencies through real interfaces."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        for node in ast.walk(context.tree):
            # 1. Function / method calls: patch(...) or monkeypatch.setattr(...)
            if isinstance(node, ast.Call):
                name = get_dotted_name(node.func)
                if name in MOCK_TARGETS or (name and name.endswith(".patch")):
                    yield context.make_diagnostic(
                        node=node,
                        code=self.code,
                        rule_id=self.rule_id,
                        message="Replace module mocking with dependency injection through a real interface, service layer, or faithful test implementation.",
                    )

            # 2. Decorators without call syntax: @patch or @mock.patch
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        dec_name = get_dotted_name(decorator)
                        if dec_name in MOCK_TARGETS or (dec_name and dec_name.endswith(".patch")):
                            yield context.make_diagnostic(
                                node=decorator,
                                code=self.code,
                                rule_id=self.rule_id,
                                message="Replace module mocking with dependency injection through a real interface, service layer, or faithful test implementation.",
                            )
