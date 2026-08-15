from __future__ import annotations

import ast
from typing import Iterator

from anti_slop.models import Diagnostic
from anti_slop.rules.base import BaseRule, RuleContext
from anti_slop.shared.ast_utils import get_dotted_name, is_test_file

MOCK_EXACT_NAMES = {
    "patch",
    "patch.object",
    "patch.dict",
    "patch.multiple",
    "unittest.mock.patch",
    "unittest.mock.patch.object",
    "unittest.mock.patch.dict",
    "unittest.mock.patch.multiple",
    "mock.patch",
    "mock.patch.object",
    "mock.patch.dict",
    "mock.patch.multiple",
    "mocker.patch",
    "mocker.patch.object",
    "mocker.patch.dict",
    "monkeypatch.setattr",
    "monkeypatch.setitem",
    "monkeypatch.delattr",
    "monkeypatch.delitem",
}

DIRECT_MOCK_CONSTRUCTORS = {
    "MagicMock",
    "Mock",
    "AsyncMock",
    "mock.MagicMock",
    "mock.Mock",
    "mock.AsyncMock",
    "unittest.mock.MagicMock",
    "unittest.mock.Mock",
    "unittest.mock.AsyncMock",
}


def is_mock_target(name: str | None) -> bool:
    if not name:
        return False

    if name in MOCK_EXACT_NAMES:
        return True

    # Check for custom mock prefixes like self.mocker.patch or fixture.mock.patch
    if name.endswith(".patch") or name.endswith(".patch.object"):
        prefix = name.split(".patch")[0].lower()
        # Explicitly ignore HTTP route decorators and HTTP clients (e.g. app.patch, router.patch, client.patch)
        if any(token in prefix for token in {"app", "router", "client", "session", "request", "http", "api", "route"}):
            return False
        # Only treat as mock if prefix explicitly indicates a mock fixture/module
        if any(token in prefix for token in {"mock", "mocker", "unittest"}):
            return True

    return False


class NoModuleMockingRule(BaseRule):
    rule_id = "no-module-mocking"
    code = "SLOP004"
    description = "Disallow module mocking and monkeypatching; tests must replace dependencies through real interfaces."

    def run(self, context: RuleContext) -> Iterator[Diagnostic]:
        in_test = is_test_file(context.filename)

        for node in ast.walk(context.tree):
            # 1. Function / method calls: patch(...) or monkeypatch.setattr(...)
            if isinstance(node, ast.Call):
                name = get_dotted_name(node.func)
                if is_mock_target(name):
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
                        if is_mock_target(dec_name):
                            yield context.make_diagnostic(
                                node=decorator,
                                code=self.code,
                                rule_id=self.rule_id,
                                message="Replace module mocking with dependency injection through a real interface, service layer, or faithful test implementation.",
                            )

            # 3. Direct module-level mocking assignment in test files: mod.fn = MagicMock()
            elif in_test and isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    func_name = get_dotted_name(node.value.func)
                    if func_name in DIRECT_MOCK_CONSTRUCTORS:
                        for target in node.targets:
                            if isinstance(target, ast.Attribute):
                                yield context.make_diagnostic(
                                    node=node,
                                    code=self.code,
                                    rule_id=self.rule_id,
                                    message="Replace module attribute mocking with dependency injection through a real interface or fake implementation.",
                                )
